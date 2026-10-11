"""Zweites Sprachmodell: Qwen3-TTS (12 Hz, 1.7B Base) als eigener Arbeitsprozess.

qwen-tts verlangt transformers 4.57.x, VoxCPM2 läuft mit neueren Versionen. Deshalb
bekommt Qwen3-TTS eine eigene virtuelle Umgebung (.venv-qwen) und läuft als
Unterprozess (qwen_worker.py), mit dem diese Klasse per JSON-Zeilen spricht.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import soundfile as sf

import voice_engine as ve

QWEN_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
VENV_DIR = ve.BASE_DIR / ".venv-qwen"
WORKER = ve.BASE_DIR / "qwen_worker.py"
INSTALL_SCRIPT = ve.BASE_DIR / "install_qwen.ps1"
INSTALL_LOG = ve.BASE_DIR / "install_qwen.log"
WORKER_LOG = ve.BASE_DIR / "qwen_worker.log"
PREFIX = "@@VC@@"

# Anzeigename -> Sprachname, wie ihn Qwen3-TTS erwartet
LANGUAGES = {
    "auto": "Auto", "de": "German", "en": "English", "fr": "French", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese",
}
BATCH = 4  # Sätze pro Durchgang (mehr = schneller, braucht aber mehr Grafikspeicher)


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def installed() -> bool:
    return venv_python().exists() and (VENV_DIR / ".installed").exists()


class QwenEngine:
    def __init__(self, device: str | None = None):
        self.device = "cpu" if device == "cpu" else "cuda:0"
        self.free_vram = True
        self.status = ve.EngineStatus("idle", "Qwen3-TTS nicht geladen")
        self._proc: subprocess.Popen | None = None
        self._lines: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self.info: dict = {}
        self.install_state = {"state": "installed" if installed() else "missing", "message": ""}

    # ---- Installation ----
    def install_async(self) -> None:
        if self.install_state["state"] == "running":
            return
        self.install_state = {"state": "running", "message": "Installiere Qwen3-TTS … (ca. 3 GB, 5–15 Minuten)"}

        def run():
            ps = shutil.which("powershell") or "powershell"
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                proc = subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                       str(INSTALL_SCRIPT), "-NonInteractive"],
                                      cwd=str(ve.BASE_DIR), creationflags=flags,
                                      capture_output=True, text=True, encoding="utf-8", errors="replace")
                ok = proc.returncode == 0 and installed()
            except Exception as exc:
                ok = False
                print(f"[ERROR] Qwen3-TTS-Installation: {exc}")
            self.install_state = {"state": "installed" if ok else "error",
                                  "message": "" if ok else f"Installation fehlgeschlagen – Details in {INSTALL_LOG.name}"}

        threading.Thread(target=run, daemon=True).start()

    def install_progress(self) -> str:
        """Letzte sinnvolle Zeile aus dem Installationsprotokoll."""
        try:
            lines = INSTALL_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return ""
        for line in reversed(lines):
            if line.startswith("==>"):
                return line[3:].strip()
        return ""

    # ---- Arbeitsprozess ----
    @property
    def loaded(self) -> bool:
        return self._proc is not None and self._proc.poll() is None and self.status.state == "ready"

    def _start(self) -> None:
        if not installed():
            raise RuntimeError("Qwen3-TTS ist noch nicht installiert (Einstellungen → Zweites Modell).")
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                   HF_HUB_DISABLE_SYMLINKS_WARNING="1")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        log = open(WORKER_LOG, "a", encoding="utf-8")
        log.write(f"\n===== Qwen3-TTS-Prozess {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        log.flush()
        self._proc = subprocess.Popen([str(venv_python()), "-u", str(WORKER)], cwd=str(ve.BASE_DIR),
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                                      text=True, encoding="utf-8", errors="replace", bufsize=1,
                                      env=env, creationflags=flags)
        self._lines = queue.Queue()
        proc = self._proc

        def reader():
            for line in proc.stdout:
                if line.startswith(PREFIX):
                    self._lines.put(json.loads(line[len(PREFIX):]))
            self._lines.put({"ok": False, "error": "Qwen3-TTS-Prozess wurde beendet", "eof": True})

        threading.Thread(target=reader, daemon=True).start()
        msg = self._lines.get(timeout=180)
        if msg.get("event") != "started":
            raise RuntimeError(msg.get("error") or "Qwen3-TTS konnte nicht gestartet werden")

    def _call(self, req: dict, timeout: float = 1800) -> dict:
        if self._proc is None or self._proc.poll() is not None:
            self._start()
        self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()
        try:
            resp = self._lines.get(timeout=timeout)
        except queue.Empty:
            self.unload()
            raise RuntimeError("Qwen3-TTS antwortet nicht (Zeitüberschreitung)")
        if not resp.get("ok"):
            if resp.get("eof"):
                self._proc = None
            raise RuntimeError(resp.get("error") or "Qwen3-TTS-Fehler")
        return resp

    def load(self) -> None:
        with self._lock:
            if self.loaded:
                return
            self.status = ve.EngineStatus("loading", "Lade Qwen3-TTS … (beim ersten Mal Download ca. 4,5 GB)")
            try:
                if self.free_vram:
                    ve.free_foreign_vram()
                self.info = self._call({"cmd": "load", "model": QWEN_MODEL, "device": self.device})
            except Exception as exc:
                self.status = ve.EngineStatus("error", f"Qwen3-TTS konnte nicht geladen werden: {exc}")
                raise
            self.status = ve.EngineStatus("ready", "Bereit", self.info.get("device", ""), self.info.get("gpu", ""))

    def unload(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                proc.stdin.flush()
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
        self.status = ve.EngineStatus("idle", "Qwen3-TTS nicht geladen")

    # ---- Sprechen ----
    def synthesize(self, text: str, profile: ve.VoiceProfile | None, use_transcript: bool = True,
                   language: str = "de", temperature: float | None = None,
                   progress=None, cancel: threading.Event | None = None) -> tuple[int, np.ndarray]:
        if profile is None:
            raise ValueError("Qwen3-TTS braucht eine geklonte Stimme – bitte eine Stimme auswählen.")
        chunks = ve.split_text(text)
        if not chunks:
            raise ValueError("Bitte einen Text eingeben.")
        # ICL (Referenz + Transkript) hängt im Deutsch-Test oft ein Wort aus dem Ende der Referenz
        # vor den Satz ("Anfassen, am 3. Oktober …") und war weder verständlicher noch ähnlicher.
        # Deshalb Standard: nur Stimmabdruck. ICL nur auf ausdrücklichen Wunsch (use_transcript="icl").
        icl = bool(use_transcript == "icl" and profile.transcript_trusted)
        if progress:
            progress(0.0, "Lade Qwen3-TTS …" if not self.loaded else "Starte …")
        self.load()
        params = {"temperature": temperature} if temperature else {}
        tmp = Path(tempfile.mkdtemp(prefix="vc_qwen_"))
        parts: list[np.ndarray] = []
        sr = 24000
        try:
            for start in range(0, len(chunks), BATCH):
                if cancel is not None and cancel.is_set():
                    raise ve.Cancelled()
                group = chunks[start:start + BATCH]
                if progress:
                    end = start + len(group)
                    progress(start / len(chunks), f"Erzeuge Abschnitt {start + 1}–{end} von {len(chunks)} (Qwen3-TTS)"
                             if len(group) > 1 else f"Erzeuge Abschnitt {end} von {len(chunks)} (Qwen3-TTS)")
                with self._lock:
                    resp = self._call({
                        "cmd": "generate", "texts": group, "language": LANGUAGES.get(language, language),
                        "ref_wav": str(profile.wav_path), "ref_text": profile.transcript, "icl": icl,
                        "out_dir": str(tmp / f"g{start:04d}"), "params": params,
                    })
                for f in resp["files"]:
                    audio, sr = sf.read(f, dtype="float32")
                    parts.append(audio if audio.ndim == 1 else audio.mean(axis=1))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        pause = np.zeros(int(0.2 * sr), dtype=np.float32)
        out: list[np.ndarray] = []
        for p in parts:
            if out:
                out.append(pause)
            out.append(p)
        if progress:
            progress(1.0, "Fertig")
        return sr, np.concatenate(out)
