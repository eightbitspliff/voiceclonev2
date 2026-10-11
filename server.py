"""Lokale API für die Desktop-Oberfläche (FastAPI)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from pydantic import BaseModel

import voice_engine as ve

STATIC_DIR = ve.BASE_DIR / "ui"
APP_VERSION = "2.2.0"

app = FastAPI(title="VoiceClone v2")
settings = ve.load_settings()
engine = ve.Engine(settings["model"], device=settings["device"],
                   optimize=settings["optimize"], load_denoiser=settings["load_denoiser"])
recorder = ve.Recorder()
window = None  # wird von voiceclone.pyw gesetzt (pywebview-Fenster)


# --------------------------------------------------------------------------- #
# Hintergrund-Jobs (Stimme einlesen, Sprache erzeugen)
# --------------------------------------------------------------------------- #
class Job:
    def __init__(self, kind: str):
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.status = "running"   # running | done | error | cancelled
        self.progress = 0.0
        self.message = "Startet …"
        self.result = None
        self.error = ""
        self.cancel = threading.Event()

    def update(self, progress: float, message: str) -> None:
        self.progress = max(0.0, min(1.0, float(progress)))
        self.message = message

    def as_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "status": self.status, "progress": self.progress,
                "message": self.message, "result": self.result, "error": self.error}


JOBS: dict[str, Job] = {}


def run_job(kind: str, func) -> Job:
    job = Job(kind)
    JOBS[job.id] = job

    def worker():
        try:
            job.result = func(job)
            job.status = "done"
            job.progress = 1.0
            job.message = "Fertig"
        except ve.Cancelled:
            job.status = "cancelled"
            job.message = "Abgebrochen"
        except Exception as exc:
            job.status = "error"
            job.error = str(exc) or exc.__class__.__name__
            print(f"[ERROR] {kind}: {job.error}")

    threading.Thread(target=worker, daemon=True).start()
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden")
    return job.as_dict()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = JOBS.get(job_id)
    if job:
        job.cancel.set()
        job.message = "Wird abgebrochen …"
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Status & Einstellungen
# --------------------------------------------------------------------------- #
@app.get("/api/status")
def status():
    s = engine.status
    return {"state": s.state, "message": s.message, "device": s.device, "gpu": s.gpu,
            "version": APP_VERSION, "desktop": window is not None}


@app.post("/api/model/load")
def load_model():
    if engine.status.state in ("idle", "error"):
        engine.load_async()
    return status()


@app.get("/api/settings")
def get_settings():
    return ve.load_settings()


@app.put("/api/settings")
def put_settings(values: dict):
    global settings
    old = settings
    settings = ve.save_settings(values)
    restart_keys = ("device", "model", "load_denoiser", "optimize")
    needs_restart = any(old.get(k) != settings.get(k) for k in restart_keys)
    return {"settings": settings, "restart_required": needs_restart}


# --------------------------------------------------------------------------- #
# Mikrofon
# --------------------------------------------------------------------------- #
@app.get("/api/audio/devices")
def audio_devices():
    return ve.Recorder.devices()


@app.post("/api/record/start")
def record_start():
    try:
        recorder.start(settings.get("input_device"))
    except Exception as exc:
        raise HTTPException(400, f"Mikrofon konnte nicht gestartet werden: {exc}")
    return {"ok": True}


@app.get("/api/record/level")
def record_level():
    return {"active": recorder.active, "level": recorder.level, "elapsed": round(recorder.elapsed, 1)}


@app.post("/api/record/stop")
def record_stop():
    try:
        return recorder.stop()
    except Exception as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/recordings/{rec_id}/audio")
def recording_audio(rec_id: str):
    path = ve.recording_path(rec_id)
    if not path:
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/wav")


@app.delete("/api/recordings/{rec_id}")
def recording_delete(rec_id: str):
    path = ve.recording_path(rec_id)
    if path:
        path.unlink(missing_ok=True)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Stimmen
# --------------------------------------------------------------------------- #
def _voice_dict(p: ve.VoiceProfile) -> dict:
    return {"name": p.name, "transcript": p.transcript, "duration": p.duration,
            "sources": p.sources, "created": p.created, "peaks": ve.waveform_peaks(p.wav_path, 80),
            "transcript_source": p.transcript_source, "transcript_trusted": p.transcript_trusted}


@app.get("/api/voices")
def voices():
    return [_voice_dict(p) for p in ve.list_profiles()]


@app.post("/api/voices")
async def create_voice(
    name: str = Form(...),
    recordings: str = Form(""),
    max_seconds: float = Form(30),
    auto_transcript: bool = Form(True),
    files: list[UploadFile] = File(default=[]),
):
    name = name.strip()
    if not name:
        raise HTTPException(400, "Bitte einen Namen für die Stimme eingeben.")
    if ve.load_profile(name) is not None:
        raise HTTPException(400, f"Eine Stimme mit dem Namen „{name}“ existiert bereits.")

    tmpdir = Path(tempfile.mkdtemp(prefix="vc_upload_"))
    paths: list[str] = []
    for f in files:
        if not f.filename:
            continue
        dst = tmpdir / Path(f.filename).name
        with dst.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        paths.append(str(dst))
    for rec_id in filter(None, recordings.split(",")):
        p = ve.recording_path(rec_id.strip())
        if p:
            named = tmpdir / f"Mikrofon_{len(paths) + 1}.wav"
            shutil.copy(p, named)
            paths.append(str(named))
    if not paths:
        raise HTTPException(400, "Bitte Audiodateien hinzufügen oder eine Aufnahme machen.")

    def work(job: Job):
        try:
            job.update(0.1, "Lese und bereinige Audiodateien …")
            audio, used = ve.build_reference(paths, max_seconds)
            profile = ve.save_profile(name, audio, "", used)
            warning = ""
            if auto_transcript:
                job.update(0.4, "Erkenne gesprochenen Text (Whisper, beim ersten Mal Download ca. 1,6 GB) …")
                try:
                    text = engine.transcribe(str(profile.wav_path), settings.get("asr_language", "auto"))
                    ve.update_transcript(name, text, "whisper")
                except Exception as exc:
                    warning = f"Automatisches Transkript fehlgeschlagen: {exc}"
            for rec_id in filter(None, recordings.split(",")):
                p = ve.recording_path(rec_id.strip())
                if p:
                    p.unlink(missing_ok=True)
            result = _voice_dict(ve.load_profile(name))
            result["warning"] = warning
            return result
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    return run_job("voice", work).as_dict()


class TranscriptIn(BaseModel):
    transcript: str


@app.put("/api/voices/{name}/transcript")
def put_transcript(name: str, body: TranscriptIn):
    if ve.load_profile(name) is None:
        raise HTTPException(404, "Stimme nicht gefunden")
    ve.update_transcript(name, body.transcript, "manual")
    return _voice_dict(ve.load_profile(name))


@app.post("/api/voices/{name}/transcribe")
def retranscribe(name: str):
    profile = ve.load_profile(name)
    if profile is None:
        raise HTTPException(404, "Stimme nicht gefunden")

    def work(job: Job):
        job.update(0.2, "Erkenne gesprochenen Text (Whisper) …")
        text = engine.transcribe(str(profile.wav_path), settings.get("asr_language", "auto"))
        ve.update_transcript(name, text, "whisper")
        return _voice_dict(ve.load_profile(name))

    return run_job("transcribe", work).as_dict()


@app.get("/api/voices/{name}/audio")
def voice_audio(name: str):
    profile = ve.load_profile(name)
    if profile is None or not profile.wav_path.exists():
        raise HTTPException(404)
    return FileResponse(profile.wav_path, media_type="audio/wav")


@app.delete("/api/voices/{name}")
def voice_delete(name: str):
    ve.delete_profile(name)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Sprache erzeugen
# --------------------------------------------------------------------------- #
class GenerateIn(BaseModel):
    text: str
    voice: str = ""
    style: str = ""
    use_transcript: bool = True
    cfg_value: float | None = None
    inference_timesteps: int | None = None
    normalize: bool | None = None


@app.post("/api/generate")
def generate(body: GenerateIn):
    if not body.text.strip():
        raise HTTPException(400, "Bitte einen Text eingeben.")
    profile = None
    if body.voice:
        profile = ve.load_profile(body.voice)
        if profile is None:
            raise HTTPException(404, f"Stimme „{body.voice}“ nicht gefunden.")

    def work(job: Job):
        sr, audio = engine.synthesize(
            body.text, profile, style=body.style, use_transcript=body.use_transcript,
            cfg_value=body.cfg_value if body.cfg_value is not None else settings["cfg_value"],
            inference_timesteps=body.inference_timesteps or settings["inference_timesteps"],
            normalize=body.normalize if body.normalize is not None else settings["normalize"],
            progress=job.update, cancel=job.cancel,
        )
        meta = ve.save_output(sr, audio, profile.name if profile else None, body.text, body.style)
        meta["peaks"] = ve.waveform_peaks(ve.output_path(meta["file"]), 160)
        return meta

    return run_job("generate", work).as_dict()


# --------------------------------------------------------------------------- #
# Verlauf
# --------------------------------------------------------------------------- #
@app.get("/api/history")
def history():
    return ve.list_outputs()


@app.get("/api/history/{file}/audio")
def history_audio(file: str):
    path = ve.output_path(file)
    if not path:
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/wav", filename=path.name)


@app.get("/api/history/{file}/peaks")
def history_peaks(file: str):
    path = ve.output_path(file)
    return ve.waveform_peaks(path, 160) if path else []


@app.delete("/api/history/{file}")
def history_delete(file: str):
    ve.delete_output(file)
    return {"ok": True}


def _reveal(path: Path) -> None:
    if sys.platform == "win32":
        if path.is_file():
            subprocess.Popen(["explorer", "/select,", str(path)])
        else:
            os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R" if path.is_file() else "", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path if path.is_dir() else path.parent)])


@app.post("/api/history/{file}/reveal")
def history_reveal(file: str):
    path = ve.output_path(file)
    if not path:
        raise HTTPException(404)
    _reveal(path)
    return {"ok": True}


@app.post("/api/open-folder/{which}")
def open_folder(which: str):
    folder = {"outputs": ve.OUTPUTS_DIR, "voices": ve.VOICES_DIR}.get(which)
    if folder is None:
        raise HTTPException(404)
    folder.mkdir(parents=True, exist_ok=True)
    _reveal(folder)
    return {"ok": True}


class SaveAsIn(BaseModel):
    format: str = "wav"


def _export(file: str, fmt: str) -> Path:
    path = ve.output_path(file)
    if not path:
        raise HTTPException(404, "Datei nicht gefunden")
    if fmt not in ve.EXPORT_FORMATS:
        raise HTTPException(400, f"Unbekanntes Format: {fmt}")
    meta = next((m for m in ve.list_outputs() if m["file"] == path.name), {})
    return ve.export_audio(path, fmt, meta.get("text", ""))


@app.get("/api/history/{file}/export")
def history_export(file: str, format: str = "wav"):
    out = _export(file, format)
    cleanup = BackgroundTask(shutil.rmtree, out.parent, ignore_errors=True)
    return FileResponse(out, filename=out.name, background=cleanup)


@app.post("/api/history/{file}/save-as")
def history_save_as(file: str, body: SaveAsIn | None = None):
    fmt = (body.format if body else "wav").lower()
    if window is None:  # Browser-Modus: normaler Download
        _export(file, fmt)  # prüft Datei/Format vorab
        return {"ok": False, "download": f"/api/history/{file}/export?format={fmt}"}
    import webview

    spec = ve.EXPORT_FORMATS.get(fmt)
    if spec is None:
        raise HTTPException(400, f"Unbekanntes Format: {fmt}")
    save_mode = getattr(getattr(webview, "FileDialog", None), "SAVE", None) or webview.SAVE_DIALOG
    target = window.create_file_dialog(save_mode, save_filename=Path(file).stem + spec["ext"],
                                       file_types=(f"{spec['label']} (*{spec['ext']})",))
    if not target:
        return {"ok": False, "cancelled": True}
    target = Path(target[0] if isinstance(target, (list, tuple)) else target)
    if target.suffix.lower() != spec["ext"]:
        target = target.with_suffix(spec["ext"])
    out = _export(file, fmt)
    try:
        shutil.copy(out, target)
    finally:
        shutil.rmtree(out.parent, ignore_errors=True)
    return {"ok": True, "path": str(target)}


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):
    return JSONResponse({"detail": str(exc)}, status_code=500)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
