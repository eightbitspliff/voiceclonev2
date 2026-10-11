"""Qwen3-TTS-Arbeitsprozess für VoiceClone v2.

Läuft in einer eigenen virtuellen Umgebung (.venv-qwen), weil qwen-tts eine andere
transformers-Version braucht als VoxCPM2. Die App startet diesen Prozess bei Bedarf
und spricht über stdin/stdout mit ihm: je Zeile ein JSON-Befehl, je Zeile eine
JSON-Antwort mit dem Präfix ``@@VC@@`` (alle anderen Ausgaben gehen nach stderr).

Befehle:
  {"cmd": "load", "model": "...", "device": "cuda:0"}
  {"cmd": "generate", "texts": [...], "language": "German", "ref_wav": "...",
   "ref_text": "...", "icl": true, "out_dir": "...", "params": {...}}
  {"cmd": "ping"} / {"cmd": "quit"}
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback

PREFIX = "@@VC@@"
_proto = sys.stdout
sys.stdout = sys.stderr  # Bibliotheks-Ausgaben dürfen das Protokoll nicht stören


def send(obj: dict) -> None:
    _proto.write(PREFIX + json.dumps(obj, ensure_ascii=False) + "\n")
    _proto.flush()


class Worker:
    def __init__(self):
        self.model = None
        self.model_id = ""
        self.device = ""
        self._prompt_key = None
        self._prompt = None

    def load(self, model_id: str, device: str) -> dict:
        import torch
        from qwen_tts import Qwen3TTSModel

        if self.model is not None and self.model_id == model_id:
            return self.info()
        if device.startswith("cuda") and not torch.cuda.is_available():
            device = "cpu"
        if device.startswith("cuda"):
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
        attn = "sdpa"
        try:
            import flash_attn  # noqa: F401

            attn = "flash_attention_2"
        except Exception:
            pass
        self.model = Qwen3TTSModel.from_pretrained(model_id, device_map=device, dtype=dtype,
                                                   attn_implementation=attn)
        self.model_id, self.device = model_id, device
        self._prompt_key = self._prompt = None
        return self.info()

    def info(self) -> dict:
        import torch

        gpu = torch.cuda.get_device_name(0) if self.device.startswith("cuda") else ""
        langs = []
        try:
            langs = sorted(self.model.model.get_supported_languages() or [])
        except Exception:
            pass
        return {"model": self.model_id, "device": self.device, "gpu": gpu, "languages": langs}

    def _voice_prompt(self, ref_wav: str, ref_text: str, icl: bool):
        key = (ref_wav, os.path.getmtime(ref_wav), ref_text if icl else "", icl)
        if key != self._prompt_key:
            self._prompt = self.model.create_voice_clone_prompt(
                ref_audio=ref_wav, ref_text=ref_text if icl else None, x_vector_only_mode=not icl)
            self._prompt_key = key
        return self._prompt

    def generate(self, req: dict) -> dict:
        import numpy as np
        import soundfile as sf

        if self.model is None:
            raise RuntimeError("Modell ist nicht geladen")
        texts = [t for t in req["texts"] if t.strip()]
        language = req.get("language") or "Auto"
        params = {k: v for k, v in (req.get("params") or {}).items() if v is not None}
        out_dir = req["out_dir"]
        os.makedirs(out_dir, exist_ok=True)
        t0 = time.perf_counter()
        if req.get("ref_wav"):
            prompt = self._voice_prompt(req["ref_wav"], req.get("ref_text", ""), bool(req.get("icl")))
            wavs, sr = self.model.generate_voice_clone(
                text=texts, language=[language] * len(texts), voice_clone_prompt=prompt * len(texts),
                **params)
        else:
            raise RuntimeError("Qwen3-TTS (Base) braucht eine geklonte Stimme als Referenz.")
        files = []
        for i, wav in enumerate(wavs):
            path = os.path.join(out_dir, f"part_{i:03d}.wav")
            sf.write(path, np.asarray(wav, dtype=np.float32), sr)
            files.append(path)
        return {"sr": sr, "files": files, "seconds": round(time.perf_counter() - t0, 2)}


def main() -> None:
    worker = Worker()
    send({"event": "started", "pid": os.getpid()})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            cmd = req.get("cmd")
            if cmd == "quit":
                send({"ok": True})
                break
            if cmd == "ping":
                send({"ok": True})
            elif cmd == "load":
                send({"ok": True, **worker.load(req["model"], req.get("device") or "cuda:0")})
            elif cmd == "generate":
                send({"ok": True, **worker.generate(req)})
            else:
                send({"ok": False, "error": f"Unbekannter Befehl: {cmd}"})
        except Exception as exc:
            traceback.print_exc()
            send({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"})


if __name__ == "__main__":
    main()
