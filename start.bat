@echo off
REM Startet VoiceClone v2 (legt beim ersten Start eine virtuelle Umgebung an)
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python app.py %*
pause
