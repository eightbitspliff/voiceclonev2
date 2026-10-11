"""VoiceClone v2 – Desktop-Start.

Startet die lokale API und öffnet die Oberfläche in einem eigenen Programmfenster
(pywebview / Edge WebView2). Ohne pywebview wird der Standardbrowser verwendet.
Optionen: --browser (im Browser öffnen), --port N, --debug
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
os.chdir(BASE)

# Kompilierte Kernel (torch.compile/Triton) dauerhaft im Programmordner speichern,
# damit die Beschleunigung nur beim allerersten Start vorbereitet werden muss.
_cache = BASE / "cache"
os.environ.setdefault("TORCHINDUCTOR_CACHE_DIR", str(_cache / "inductor"))
os.environ.setdefault("TRITON_CACHE_DIR", str(_cache / "triton"))
os.environ.setdefault("TORCHINDUCTOR_FX_GRAPH_CACHE", "1")
os.environ.setdefault("TORCHINDUCTOR_AUTOGRAD_CACHE", "1")
sys.path.insert(0, str(BASE))

# Unter pythonw.exe gibt es keine Konsole -> Ausgaben in eine Logdatei umleiten.
LOG_FILE = BASE / "voiceclone.log"
if sys.stdout is None or sys.stderr is None or "pythonw" in Path(sys.executable).name.lower():
    _log = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log


def _free_port(preferred: int) -> int:
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("Kein freier Port gefunden")


def _show_error(msg: str) -> None:
    print(msg)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, msg, "VoiceClone v2 – Fehler", 0x10)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", action="store_true", help="Im Standardbrowser statt im App-Fenster öffnen")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    print(f"\n===== VoiceClone v2 Start {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
    try:
        import uvicorn

        import server
    except Exception:
        _show_error("VoiceClone v2 konnte nicht gestartet werden:\n\n" + traceback.format_exc()
                    + f"\nDetails: {LOG_FILE}")
        return

    port = _free_port(args.port)
    url = f"http://127.0.0.1:{port}/"
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(200):
        try:
            urllib.request.urlopen(url + "api/status", timeout=1)
            break
        except Exception:
            time.sleep(0.05)

    # Modell im Hintergrund laden, damit es beim ersten "Sprechen" bereit ist
    server.preload()

    webview = None
    if not args.browser:
        try:
            import webview  # type: ignore
        except Exception as exc:
            print(f"[WARN] pywebview nicht verfügbar ({exc}) – öffne im Browser.")

    if webview is None:
        import webbrowser

        webbrowser.open(url)
        print(f"Läuft auf {url} – zum Beenden dieses Fenster/Prozess schließen.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    icon = BASE / "ui" / "icon.ico"
    window = webview.create_window(
        "VoiceClone v2", url, width=1320, height=860, min_size=(980, 640),
        background_color="#0f1117", text_select=True,
    )
    server.window = window
    opts = dict(debug=args.debug, private_mode=False, storage_path=str(BASE / "webview_data"))
    try:
        webview.start(icon=str(icon) if icon.exists() else None, **opts)
    except TypeError:  # ältere pywebview-Versionen ohne icon-Parameter
        webview.start(**opts)
    srv.should_exit = True
    os._exit(0)  # Hintergrund-Threads (Modell, Audio) sofort beenden


if __name__ == "__main__":
    main()
