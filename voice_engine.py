"""Kernlogik: Audio-Aufbereitung, Stimmprofile und VoxCPM2-Synthese."""

from __future__ import annotations

import json
import re
import shutil
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent
VOICES_DIR = BASE_DIR / "voices"
OUTPUTS_DIR = BASE_DIR / "outputs"

# VoxCPM2 kodiert Referenz-Audio mit 16 kHz (gibt aber 48 kHz aus).
REF_SAMPLE_RATE = 16000
GAP_SECONDS = 0.3


# --------------------------------------------------------------------------- #
# Audio-Aufbereitung
# --------------------------------------------------------------------------- #
def _load_clean(path: str, top_db: float = 35.0) -> np.ndarray:
    audio, _ = librosa.load(path, sr=REF_SAMPLE_RATE, mono=True)
    if audio.size == 0:
        return audio
    audio, _ = librosa.effects.trim(audio, top_db=top_db)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1e-4:
        audio = audio / peak * 0.95
    return audio.astype(np.float32)


def build_reference(paths: list[str], max_seconds: float) -> tuple[np.ndarray, list[str]]:
    """Lädt alle Aufnahmen, entfernt Stille am Rand, normalisiert und fügt sie
    zu einem Referenz-Clip zusammen (maximal ``max_seconds`` lang)."""
    gap = np.zeros(int(GAP_SECONDS * REF_SAMPLE_RATE), dtype=np.float32)
    max_samples = int(max_seconds * REF_SAMPLE_RATE)
    parts: list[np.ndarray] = []
    used: list[str] = []
    total = 0
    for p in paths:
        try:
            audio = _load_clean(p)
        except Exception as exc:  # defekte/unbekannte Datei überspringen
            print(f"[WARN] Datei konnte nicht gelesen werden: {p} ({exc})")
            continue
        if audio.size < REF_SAMPLE_RATE * 0.5:  # kürzer als 0,5 s -> ignorieren
            continue
        if parts:
            parts.append(gap)
            total += gap.size
        remaining = max_samples - total
        if remaining <= 0:
            break
        parts.append(audio[:remaining])
        total += min(audio.size, remaining)
        used.append(Path(p).name)
        if total >= max_samples:
            break
    if not parts:
        raise ValueError("Keine verwertbare Sprachaufnahme gefunden (mind. 0,5 s Sprache nötig).")
    return np.concatenate(parts), used


# --------------------------------------------------------------------------- #
# Stimmprofile
# --------------------------------------------------------------------------- #
@dataclass
class VoiceProfile:
    name: str
    transcript: str
    duration: float
    sources: list[str]
    created: str

    @property
    def wav_path(self) -> Path:
        return VOICES_DIR / safe_name(self.name) / "reference.wav"


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w\- ]+", "", name, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "_", name) or "stimme"


def save_profile(name: str, audio: np.ndarray, transcript: str, sources: list[str]) -> VoiceProfile:
    folder = VOICES_DIR / safe_name(name)
    folder.mkdir(parents=True, exist_ok=True)
    sf.write(folder / "reference.wav", audio, REF_SAMPLE_RATE)
    profile = VoiceProfile(
        name=name.strip(),
        transcript=transcript.strip(),
        duration=round(audio.size / REF_SAMPLE_RATE, 2),
        sources=sources,
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    (folder / "meta.json").write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


def update_transcript(name: str, transcript: str) -> None:
    meta = VOICES_DIR / safe_name(name) / "meta.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["transcript"] = transcript.strip()
    meta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_profiles() -> list[str]:
    if not VOICES_DIR.exists():
        return []
    names = []
    for meta in sorted(VOICES_DIR.glob("*/meta.json")):
        try:
            names.append(json.loads(meta.read_text(encoding="utf-8"))["name"])
        except Exception:
            continue
    return names


def load_profile(name: str) -> VoiceProfile | None:
    meta = VOICES_DIR / safe_name(name) / "meta.json"
    if not meta.exists():
        return None
    return VoiceProfile(**json.loads(meta.read_text(encoding="utf-8")))


def delete_profile(name: str) -> None:
    folder = VOICES_DIR / safe_name(name)
    if folder.exists():
        shutil.rmtree(folder)


# --------------------------------------------------------------------------- #
# Text-Aufteilung für lange Texte
# --------------------------------------------------------------------------- #
def split_text(text: str, max_chars: int = 220) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text.strip())
    sentences = [s.strip() for s in re.split(r"(?<=[.!?;:。！？；])\s+|\n+", text) if s.strip()]
    chunks: list[str] = []
    current = ""
    for s in sentences:
        # Sehr lange Sätze an Kommas weiter teilen
        pieces = [s] if len(s) <= max_chars else [p.strip() for p in re.split(r"(?<=[,，])\s*", s) if p.strip()]
        for piece in pieces:
            if current and len(current) + 1 + len(piece) > max_chars:
                chunks.append(current)
                current = piece
            else:
                current = f"{current} {piece}".strip()
    if current:
        chunks.append(current)
    return chunks


# --------------------------------------------------------------------------- #
# Modelle (lazy geladen)
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, model_id: str = "openbmb/VoxCPM2", device: str | None = None,
                 optimize: bool = False, load_denoiser: bool = False):
        self.model_id = model_id
        self.device = device
        self.optimize = optimize
        self.load_denoiser = load_denoiser
        self._model = None
        self._asr = None
        self._lock = threading.Lock()

    # ---- TTS ----
    @property
    def model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from voxcpm import VoxCPM

                    print(f"[INFO] Lade {self.model_id} … (beim ersten Start wird das Modell heruntergeladen)")
                    self._model = VoxCPM.from_pretrained(
                        self.model_id,
                        load_denoiser=self.load_denoiser,
                        optimize=self.optimize,
                        device=self.device,
                    )
                    print("[INFO] Modell geladen.")
        return self._model

    @property
    def sample_rate(self) -> int:
        return self.model.tts_model.sample_rate

    def synthesize(self, text: str, profile: VoiceProfile | None, style: str = "",
                   use_transcript: bool = True, cfg_value: float = 2.0,
                   inference_timesteps: int = 10, normalize: bool = False,
                   denoise: bool = False, progress=None) -> tuple[int, np.ndarray]:
        chunks = split_text(text)
        if not chunks:
            raise ValueError("Bitte einen Text eingeben.")

        kwargs: dict = dict(
            cfg_value=float(cfg_value),
            inference_timesteps=int(inference_timesteps),
            normalize=normalize,
            denoise=denoise and self.load_denoiser,
        )
        ultimate = False
        if profile is not None:
            ref = str(profile.wav_path)
            kwargs["reference_wav_path"] = ref
            if use_transcript and profile.transcript:
                # "Ultimate Cloning": Referenz + Transkript als Fortsetzungs-Prompt
                kwargs["prompt_wav_path"] = ref
                kwargs["prompt_text"] = profile.transcript
                ultimate = True

        style = style.strip().strip("()")
        prefix = f"({style})" if style and not ultimate else ""

        model = self.model
        sr = self.sample_rate
        pause = np.zeros(int(0.2 * sr), dtype=np.float32)
        out: list[np.ndarray] = []
        for i, chunk in enumerate(chunks):
            if progress is not None:
                progress((i, len(chunks)), desc=f"Erzeuge Abschnitt {i + 1}/{len(chunks)}")
            wav = model.generate(text=prefix + chunk, **kwargs)
            if out:
                out.append(pause)
            out.append(np.asarray(wav, dtype=np.float32))
        return sr, np.concatenate(out)

    # ---- Spracherkennung (für automatisches Transkript) ----
    def transcribe(self, wav_path: str) -> str:
        if self._asr is None:
            from funasr import AutoModel

            device = self.device
            if device is None:
                import torch

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            self._asr = AutoModel(model="iic/SenseVoiceSmall", disable_update=True, log_level="ERROR", device=device)
        res = self._asr.generate(input=wav_path, language="auto", use_itn=True)
        text = res[0]["text"] if res else ""
        return text.split("|>")[-1].strip()


def save_output(sr: int, audio: np.ndarray, voice_name: str | None) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    tag = safe_name(voice_name) if voice_name else "standard"
    path = OUTPUTS_DIR / f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}_{tag}.wav"
    sf.write(path, audio, sr)
    return path
