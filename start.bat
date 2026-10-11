@echo off
REM Startet VoiceClone v2 mit sichtbarer Konsole (zur Fehlersuche)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" voiceclone.pyw %*
pause
