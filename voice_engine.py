"""Kernlogik: Audio-Aufbereitung, Stimmprofile, Verlauf und VoxCPM2-Synthese."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("VOICECLONE_DATA", BASE_DIR))
VOICES_DIR = DATA_DIR / "voices"
OUTPUTS_DIR = DATA_DIR / "outputs"
RECORDINGS_DIR = DATA_DIR / "recordings"
SETTINGS_FILE = DATA_DIR / "settings.json"

# VoxCPM2 kodiert Referenz-Audio mit 16 kHz (gibt aber 48 kHz aus).
REF_SAMPLE_RATE = 16000
GAP_SECONDS = 0.3

DEFAULT_SETTINGS = {
    "theme": "system",          # system | light | dark
    "device": "auto",           # auto | cuda | cpu
    "model": "openbmb/VoxCPM2",
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "max_ref_seconds": 30,
    "auto_transcript": True,
    "normalize": False,
    "load_denoiser": False,
    "accel": "auto",            # auto | off  (torch.compile + CUDA Graphs)
    "input_device": None,
    "asr_language": "auto",     # Sprache für die automatische Transkription
    "export_format": "wav",     # wav | mp3 | ogg | mp4
    "engine": "voxcpm",         # voxcpm | qwen  (Sprachmodell auf der Sprechen-Seite)
    "text_language": "de",      # Sprache der Texte (Qwen3-TTS-Sprache + deutsche Aufbereitung)
    "german_normalize": True,   # Zahlen, Datum, Uhrzeit, Einheiten, Abkürzungen ausschreiben
    "free_vram": True,          # Ollama-Modelle vor dem Laden aus dem Grafikspeicher werfen
}

# Ollama-Server, deren geladene Modelle bei Bedarf entladen werden (Standardport + Zusatzports)
OLLAMA_URLS = [u.strip() for u in os.environ.get(
    "VOICECLONE_OLLAMA", "http://127.0.0.1:11434,http://127.0.0.1:21434").split(",") if u.strip()]

# Mehrsprachige Spracherkennung (Whisper) für das Referenz-Transkript.
ASR_MODEL = "openai/whisper-large-v3-turbo"


# --------------------------------------------------------------------------- #
# Einstellungen
# --------------------------------------------------------------------------- #
def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    try:
        settings.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return settings


def save_settings(values: dict) -> dict:
    settings = load_settings()
    settings.update({k: v for k, v in values.items() if k in DEFAULT_SETTINGS})
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return settings


# --------------------------------------------------------------------------- #
# Audio-Aufbereitung
# --------------------------------------------------------------------------- #
def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def _run_ffmpeg(args: list[str]) -> None:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.run([_ffmpeg_exe(), "-y", "-loglevel", "error", *args],
                          capture_output=True, text=True, creationflags=flags)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg-Fehler: {proc.stderr.strip() or proc.returncode}")


def _ffmpeg_to_wav(path: str) -> str:
    """Konvertiert Formate, die soundfile nicht lesen kann (z. B. M4A/AAC), per FFmpeg."""
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    _run_ffmpeg(["-i", path, "-ac", "1", "-ar", str(REF_SAMPLE_RATE), out])
    return out


# Speicherformate für erzeugte Audios (intern wird immer verlustfrei als WAV gespeichert)
EXPORT_FORMATS = {
    "wav": {"ext": ".wav", "label": "WAV Audio", "args": None},
    "mp3": {"ext": ".mp3", "label": "MP3 Audio", "args": ["-c:a", "libmp3lame", "-b:a", "192k"]},
    "ogg": {"ext": ".ogg", "label": "OGG Vorbis Audio", "args": ["-c:a", "libvorbis", "-q:a", "6"]},
    "mp4": {"ext": ".mp4", "label": "MP4 Audio AAC", "args": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]},
}


def export_audio(wav_path: Path, fmt: str, title: str = "") -> Path:
    """Wandelt eine erzeugte WAV-Datei in das gewünschte Format um (temporäre Datei)."""
    spec = EXPORT_FORMATS.get(fmt)
    if spec is None:
        raise ValueError(f"Unbekanntes Format: {fmt}")
    out = Path(tempfile.mkdtemp(prefix="vc_export_")) / (wav_path.stem + spec["ext"])
    if spec["args"] is None:
        shutil.copy(wav_path, out)
        return out
    meta = ["-metadata", f"title={title[:120]}", "-metadata", "artist=VoiceClone v2"] if title else []
    _run_ffmpeg(["-i", str(wav_path), "-vn", *spec["args"], *meta, str(out)])
    return out


def load_audio(path: str, sr: int = REF_SAMPLE_RATE) -> np.ndarray:
    try:
        audio, _ = librosa.load(path, sr=sr, mono=True)
    except Exception:
        audio, _ = librosa.load(_ffmpeg_to_wav(path), sr=sr, mono=True)
    return audio.astype(np.float32)


def _load_clean(path: str, top_db: float = 35.0) -> np.ndarray:
    audio = load_audio(path)
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


def waveform_peaks(path: Path, bins: int = 120) -> list[float]:
    """Grobe Hüllkurve für die Wellenform-Anzeige im Interface."""
    try:
        audio, _ = sf.read(path, dtype="float32", always_2d=True)
        audio = np.abs(audio.mean(axis=1))
    except Exception:
        return []
    if audio.size == 0:
        return []
    chunks = np.array_split(audio, bins)
    peaks = np.array([c.max() if c.size else 0.0 for c in chunks])
    top = peaks.max() or 1.0
    return [round(float(p / top), 3) for p in peaks]


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
    # "whisper" = automatisch erkannt, "manual" = vom Nutzer bearbeitet,
    # "" = Altbestand (frühere Spracherkennung konnte kein Deutsch -> nicht vertrauenswürdig)
    transcript_source: str = ""

    @property
    def transcript_trusted(self) -> bool:
        return bool(self.transcript.strip()) and self.transcript_source in ("whisper", "manual")

    @property
    def folder(self) -> Path:
        return VOICES_DIR / safe_name(self.name)

    @property
    def wav_path(self) -> Path:
        return self.folder / "reference.wav"


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w\- ]+", "", name, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "_", name) or "stimme"


def save_profile(name: str, audio: np.ndarray, transcript: str, sources: list[str],
                 transcript_source: str = "") -> VoiceProfile:
    folder = VOICES_DIR / safe_name(name)
    folder.mkdir(parents=True, exist_ok=True)
    sf.write(folder / "reference.wav", audio, REF_SAMPLE_RATE)
    profile = VoiceProfile(
        name=name.strip(),
        transcript=transcript.strip(),
        duration=round(audio.size / REF_SAMPLE_RATE, 2),
        sources=sources,
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
        transcript_source=transcript_source,
    )
    (folder / "meta.json").write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


def _read_profile(meta: Path) -> VoiceProfile:
    data = json.loads(meta.read_text(encoding="utf-8"))
    known = VoiceProfile.__dataclass_fields__
    return VoiceProfile(**{k: v for k, v in data.items() if k in known})


def update_transcript(name: str, transcript: str, source: str) -> None:
    meta = VOICES_DIR / safe_name(name) / "meta.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["transcript"] = transcript.strip()
    data["transcript_source"] = source
    meta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_profiles() -> list[VoiceProfile]:
    if not VOICES_DIR.exists():
        return []
    profiles = []
    for meta in VOICES_DIR.glob("*/meta.json"):
        try:
            profiles.append(_read_profile(meta))
        except Exception:
            continue
    return sorted(profiles, key=lambda p: p.created, reverse=True)


def load_profile(name: str) -> VoiceProfile | None:
    meta = VOICES_DIR / safe_name(name) / "meta.json"
    if not meta.exists():
        return None
    return _read_profile(meta)


def delete_profile(name: str) -> None:
    folder = VOICES_DIR / safe_name(name)
    if folder.exists():
        shutil.rmtree(folder)


# --------------------------------------------------------------------------- #
# Verlauf (erzeugte Audiodateien)
# --------------------------------------------------------------------------- #
def save_output(sr: int, audio: np.ndarray, voice_name: str | None, text: str, style: str = "",
                engine: str = "") -> dict:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    tag = safe_name(voice_name) if voice_name else "standard"
    stem = f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}_{tag}"
    path = OUTPUTS_DIR / f"{stem}.wav"
    sf.write(path, audio, sr)
    meta = {
        "file": path.name,
        "voice": voice_name or "",
        "text": text,
        "style": style,
        "engine": engine,
        "duration": round(audio.size / sr, 2),
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    path.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def list_outputs() -> list[dict]:
    if not OUTPUTS_DIR.exists():
        return []
    items = []
    for wav in OUTPUTS_DIR.glob("*.wav"):
        meta_file = wav.with_suffix(".json")
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {"file": wav.name, "voice": "", "text": "", "style": "",
                    "duration": round(sf.info(wav).duration, 2),
                    "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(wav.stat().st_mtime))}
        items.append(meta)
    return sorted(items, key=lambda m: m["file"], reverse=True)


def output_path(file: str) -> Path | None:
    path = (OUTPUTS_DIR / Path(file).name)
    return path if path.suffix == ".wav" and path.exists() else None


def delete_output(file: str) -> None:
    path = output_path(file)
    if path:
        path.unlink(missing_ok=True)
        path.with_suffix(".json").unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Mikrofonaufnahme (läuft in Python, unabhängig vom Fenster/Browser)
# --------------------------------------------------------------------------- #
class Recorder:
    def __init__(self):
        self._stream = None
        self._frames: list[np.ndarray] = []
        self._sr = 0
        self._started = 0.0
        self.level = 0.0
        self._lock = threading.Lock()

    @staticmethod
    def devices() -> list[dict]:
        try:
            import sounddevice as sd

            default_in = sd.default.device[0]
            return [
                {"id": i, "name": d["name"], "default": i == default_in}
                for i, d in enumerate(sd.query_devices())
                if d["max_input_channels"] > 0
            ]
        except Exception:
            return []

    @property
    def active(self) -> bool:
        return self._stream is not None

    @property
    def elapsed(self) -> float:
        return time.time() - self._started if self.active else 0.0

    def start(self, device=None) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:  # PortAudio fehlt o. Ä.
            raise RuntimeError(f"Audio-Aufnahme nicht verfügbar: {exc}")
        if self.active:
            return
        info = sd.query_devices(device, "input")
        self._sr = int(info["default_samplerate"]) or 48000
        self._frames = []
        self.level = 0.0

        def callback(indata, frames, t, status):
            mono = indata.mean(axis=1).copy()
            with self._lock:
                self._frames.append(mono)
            self.level = float(min(1.0, np.sqrt(np.mean(mono ** 2)) * 6))

        self._stream = sd.InputStream(device=device, channels=1, samplerate=self._sr,
                                      dtype="float32", callback=callback)
        self._stream.start()
        self._started = time.time()

    def stop(self) -> dict:
        if not self.active:
            raise RuntimeError("Es läuft keine Aufnahme.")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self.level = 0.0
        with self._lock:
            audio = np.concatenate(self._frames) if self._frames else np.zeros(0, dtype=np.float32)
            self._frames = []
        if audio.size < self._sr * 0.5:
            raise RuntimeError("Aufnahme zu kurz (mind. 0,5 Sekunden).")
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        rec_id = uuid.uuid4().hex[:12]
        path = RECORDINGS_DIR / f"{rec_id}.wav"
        sf.write(path, audio, self._sr)
        return {"id": rec_id, "duration": round(audio.size / self._sr, 2)}


def recording_path(rec_id: str) -> Path | None:
    if not re.fullmatch(r"[0-9a-f]{12}", rec_id or ""):
        return None
    path = RECORDINGS_DIR / f"{rec_id}.wav"
    return path if path.exists() else None


# --------------------------------------------------------------------------- #
# Text-Aufteilung für lange Texte
# --------------------------------------------------------------------------- #
def split_text(text: str, max_chars: int = 220) -> list[str]:
    from german_text import split_sentences

    text = re.sub(r"[ \t]+", " ", text.strip())
    sentences = split_sentences(text)
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


class Cancelled(Exception):
    pass


# --------------------------------------------------------------------------- #
# Modelle
# --------------------------------------------------------------------------- #
@dataclass
class EngineStatus:
    state: str = "idle"          # idle | loading | ready | error
    message: str = "Modell noch nicht geladen"
    device: str = ""
    gpu: str = ""
    extra: dict = field(default_factory=dict)


def hardware_info() -> dict:
    """Erkennt Grafikkarte, Grafikspeicher und Beschleunigungsmöglichkeiten."""
    info = {"cuda": False, "gpu": "", "vram_gb": 0.0, "compute": "", "bf16": False, "triton": False}
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info.update(cuda=True, gpu=props.name, vram_gb=round(props.total_memory / 1024 ** 3, 1),
                        compute=f"{props.major}.{props.minor}", bf16=torch.cuda.is_bf16_supported())
        try:
            import triton  # noqa: F401

            info["triton"] = True
        except Exception:
            pass
    except Exception:
        pass
    return info


def vram_usage() -> dict:
    """Freier und belegter Grafikspeicher (ganze Karte, auch andere Programme)."""
    try:
        import torch

        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info(0)
            return {"free_gb": round(free / 1024 ** 3, 2), "total_gb": round(total / 1024 ** 3, 2),
                    "app_gb": round(torch.cuda.memory_reserved(0) / 1024 ** 3, 2)}
    except Exception:
        pass
    return {}


def free_foreign_vram() -> list[str]:
    """Entlädt Modelle aus laufenden Ollama-Servern, damit VoiceClone den Grafikspeicher
    für sich hat. Läuft ein Modell zusätzlich im Grafikspeicher, lagert der NVIDIA-Treiber
    unter Windows in den Arbeitsspeicher aus – die Sprachausgabe wird dann vielfach langsamer."""
    import urllib.request

    unloaded = []
    for base in OLLAMA_URLS:
        try:
            with urllib.request.urlopen(f"{base}/api/ps", timeout=1.5) as r:
                models = json.loads(r.read().decode("utf-8")).get("models", [])
        except Exception:
            continue
        for m in models:
            name = m.get("name") or m.get("model")
            if not name or not m.get("size_vram"):
                continue
            body = json.dumps({"model": name, "keep_alive": 0}).encode("utf-8")
            req = urllib.request.Request(f"{base}/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=20).read()
                unloaded.append(name)
            except Exception as exc:
                print(f"[WARN] Ollama-Modell {name} konnte nicht entladen werden: {exc}")
    if unloaded:
        print(f"[INFO] Grafikspeicher freigegeben – Ollama-Modelle entladen: {', '.join(unloaded)}")
        time.sleep(1.0)
    return unloaded


def _tune_torch() -> None:
    """Globale PyTorch-Einstellungen für NVIDIA-Grafikkarten (Ampere und neuer)."""
    import torch

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision("high")


class Engine:
    def __init__(self, model_id: str = "openbmb/VoxCPM2", device: str | None = None,
                 accel: str = "auto", load_denoiser: bool = False):
        self.model_id = model_id
        self.device = None if device in (None, "", "auto") else device
        self.accel = accel                 # auto | off
        self.load_denoiser = load_denoiser
        self.compiled = False              # torch.compile + CUDA Graphs aktiv?
        self.free_vram = True              # Ollama-Modelle vor dem Laden entladen
        self._model = None
        self._lock = threading.Lock()
        self._gen_lock = threading.Lock()
        self._prompt_cache_key = None
        self._prompt_cache = None
        self.status = EngineStatus()

    def load_async(self) -> None:
        threading.Thread(target=lambda: self._safe_load(), daemon=True).start()

    def _safe_load(self) -> None:
        try:
            _ = self.model
        except Exception:
            pass

    # ---- TTS ----
    def _want_compile(self) -> bool:
        if self.accel == "off" or (self.device and not self.device.startswith("cuda")):
            return False
        hw = hardware_info()
        return hw["cuda"] and hw["triton"]

    def _load(self, compile_: bool):
        from voxcpm import VoxCPM

        return VoxCPM.from_pretrained(self.model_id, load_denoiser=self.load_denoiser,
                                      optimize=compile_, device=self.device)

    @property
    def model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = self._load_with_fallback()
        return self._model

    def _load_with_fallback(self):
        compile_ = self._want_compile()
        msg = "Lade VoxCPM2 … (beim ersten Start wird das Modell heruntergeladen, ca. 5 GB)"
        if compile_:
            msg += " – Beschleunigung wird vorbereitet (einmalig 1–3 Minuten)"
        self.status = EngineStatus("loading", msg)
        try:
            if self.free_vram:
                free_foreign_vram()
            _tune_torch()
            try:
                model = self._load(compile_)
                self.compiled = compile_
            except Exception as exc:
                if not compile_:
                    raise
                print(f"[WARN] Beschleunigung (torch.compile) fehlgeschlagen, lade ohne: {exc}")
                self._free_gpu()
                model = self._load(False)
                self.compiled = False
            self._warmup(model)
        except Exception as exc:
            self.status = EngineStatus("error", f"Modell konnte nicht geladen werden: {exc}")
            raise
        dev, gpu = self._device_info(model)
        self.status = EngineStatus("ready", "Bereit", dev, gpu, {
            "compiled": self.compiled, "dtype": getattr(model.tts_model.config, "dtype", ""),
            **{k: v for k, v in hardware_info().items() if k in ("vram_gb", "compute", "triton")},
        })
        return model

    @staticmethod
    def _free_gpu() -> None:
        import gc

        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    @staticmethod
    def _warmup(model) -> None:
        """Kurzer Probelauf, damit die erste echte Anfrage nicht auf CUDA-Initialisierung wartet."""
        try:
            model.tts_model.generate(target_text="Hallo.", max_len=8)
        except Exception as exc:
            print(f"[WARN] Aufwärmen übersprungen: {exc}")

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def unload(self) -> None:
        """Gibt den Grafikspeicher frei (z. B. wenn Qwen3-TTS geladen wird)."""
        with self._gen_lock, self._lock:
            if self._model is None:
                return
            self._model = None
            self._prompt_cache_key = self._prompt_cache = None
            if self.compiled:
                try:
                    import torch

                    torch._dynamo.reset()  # kompilierte Graphen halten sonst Grafikspeicher fest
                except Exception:
                    pass
            self._free_gpu()
            self.status = EngineStatus("idle", "VoxCPM2 entladen (Grafikspeicher für Qwen3-TTS frei)")

    def _disable_compile(self) -> None:
        """Lädt das Modell ohne torch.compile neu (Rückfall bei Laufzeitfehlern)."""
        with self._lock:
            self._model = None
            self._prompt_cache_key = self._prompt_cache = None
            self._free_gpu()
            self.accel = "off"
            self._model = self._load_with_fallback()

    @staticmethod
    def _device_info(model) -> tuple[str, str]:
        try:
            import torch

            dev = str(getattr(model.tts_model, "device", "")) or ("cuda" if torch.cuda.is_available() else "cpu")
            gpu = torch.cuda.get_device_name(0) if dev.startswith("cuda") else ""
            return dev, gpu
        except Exception:
            return "", ""

    @property
    def sample_rate(self) -> int:
        return self.model.tts_model.sample_rate

    def _get_prompt_cache(self, model, profile: VoiceProfile | None, ultimate: bool):
        """Referenz nur einmal kodieren und für alle Sätze (und Folgeanfragen) wiederverwenden."""
        if profile is None:
            return None
        ref = str(profile.wav_path)
        key = (ref, profile.wav_path.stat().st_mtime, ultimate, profile.transcript if ultimate else "")
        if key != self._prompt_cache_key:
            self._prompt_cache = model.tts_model.build_prompt_cache(
                prompt_text=profile.transcript if ultimate else None,
                prompt_wav_path=ref if ultimate else None,
                reference_wav_path=ref,
            )
            self._prompt_cache_key = key
        return self._prompt_cache

    def _generate_chunk(self, model, text: str, cache, cfg_value: float, steps: int) -> np.ndarray:
        gen = model.tts_model._generate_with_prompt_cache(
            target_text=text, prompt_cache=cache, min_len=2, max_len=4096,
            inference_timesteps=steps, cfg_value=cfg_value,
            retry_badcase=True, retry_badcase_max_times=3, retry_badcase_ratio_threshold=6.0,
            streaming=False,
        )
        try:
            wav, _, _ = next(gen)
        finally:
            gen.close()
        return wav.squeeze(0).float().cpu().numpy()

    def synthesize(self, text: str, profile: VoiceProfile | None, style: str = "",
                   use_transcript: bool = True, cfg_value: float = 2.0,
                   inference_timesteps: int = 10, normalize: bool = False,
                   denoise: bool = False, progress=None, cancel: threading.Event | None = None
                   ) -> tuple[int, np.ndarray]:
        chunks = split_text(text)
        if not chunks:
            raise ValueError("Bitte einen Text eingeben.")
        ultimate = bool(profile is not None and use_transcript and profile.transcript_trusted)
        style = style.strip().strip("()")
        prefix = f"({style})" if style and not ultimate else ""

        if progress:
            progress(0.0, "Lade Modell …" if self._model is None else "Starte …")
        try:
            return self._synthesize(chunks, profile, prefix, ultimate, float(cfg_value),
                                    int(inference_timesteps), normalize, denoise, progress, cancel)
        except Cancelled:
            raise
        except Exception as exc:
            if not self.compiled:
                raise
            # torch.compile kann auf manchen Systemen erst zur Laufzeit scheitern -> ohne wiederholen
            print(f"[WARN] Fehler mit Beschleunigung, wiederhole ohne torch.compile: {exc}")
            if progress:
                progress(0.0, "Beschleunigung nicht nutzbar – lade Modell ohne neu …")
            self._disable_compile()
            return self._synthesize(chunks, profile, prefix, ultimate, float(cfg_value),
                                    int(inference_timesteps), normalize, denoise, progress, cancel)

    def _synthesize(self, chunks, profile, prefix, ultimate, cfg_value, steps, normalize, denoise,
                    progress, cancel) -> tuple[int, np.ndarray]:
        model = self.model
        sr = self.sample_rate
        pause = np.zeros(int(0.2 * sr), dtype=np.float32)
        out: list[np.ndarray] = []
        fast_path = not (denoise and self.load_denoiser)
        normalizer = None
        if normalize:
            from voxcpm.utils.text_normalize import TextNormalizer

            normalizer = TextNormalizer()
        with self._gen_lock:
            cache = self._get_prompt_cache(model, profile, ultimate) if fast_path else None
            for i, chunk in enumerate(chunks):
                if cancel is not None and cancel.is_set():
                    raise Cancelled()
                if progress:
                    progress(i / len(chunks), f"Erzeuge Abschnitt {i + 1} von {len(chunks)}")
                if fast_path:
                    t = normalizer.normalize(chunk) if normalizer else chunk
                    wav = self._generate_chunk(model, prefix + t, cache, cfg_value, steps)
                else:  # Entrauschen der Referenz -> offizieller (langsamerer) Weg
                    kwargs = dict(cfg_value=cfg_value, inference_timesteps=steps, normalize=normalize, denoise=True)
                    if profile is not None:
                        kwargs["reference_wav_path"] = str(profile.wav_path)
                        if ultimate:
                            kwargs.update(prompt_wav_path=str(profile.wav_path), prompt_text=profile.transcript)
                    wav = model.generate(text=prefix + chunk, **kwargs)
                if out:
                    out.append(pause)
                out.append(np.asarray(wav, dtype=np.float32))
        if progress:
            progress(1.0, "Fertig")
        return sr, np.concatenate(out)

    # ---- Spracherkennung (für automatisches Transkript) ----
    def transcribe(self, wav_path: str, language: str = "auto") -> str:
        """Erkennt den gesprochenen Text der Referenz mit Whisper (u. a. Deutsch).

        VoxCPM2 setzt im "Ultimate Cloning" voraus, dass das Transkript exakt dem
        Gesprochenen entspricht – ein falsches Transkript ergibt unverständliche Sprache.
        """
        import torch
        from transformers import pipeline

        device = self.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        if device == "cuda":
            device = "cuda:0"
        asr = pipeline(
            "automatic-speech-recognition",
            model=ASR_MODEL,
            dtype=torch.float16 if device.startswith("cuda") else torch.float32,
            device=device,
        )
        try:
            audio = load_audio(wav_path, sr=16000)
            generate_kwargs = {"task": "transcribe"}
            if language and language != "auto":
                generate_kwargs["language"] = language
            result = asr({"raw": audio, "sampling_rate": 16000},
                         return_timestamps=True, generate_kwargs=generate_kwargs)
            text = result["text"] if isinstance(result, dict) else str(result)
            return re.sub(r"\s+", " ", text).strip()
        finally:
            # Speicher (VRAM) für VoxCPM2 wieder freigeben
            del asr
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
