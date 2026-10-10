@echo off
REM Startet VoiceClone v2 (richtet beim ersten Start alles automatisch ein)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
  if errorlevel 1 exit /b 1
)
echo Starte VoiceClone v2 ... der Browser oeffnet sich automatisch.
echo Beim ersten Start wird das Modell (ca. 5 GB) heruntergeladen.
".venv\Scripts\python.exe" app.py --inbrowser %*
pause
