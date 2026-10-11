; VoiceClone v2 - Windows-Installer (NSIS)
; Bauen: makensis installer/VoiceCloneV2.nsi  ->  installer/VoiceCloneV2-Setup.exe

Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

; Installer/Starter sind 32-Bit-Programme: ohne "Sysnative" würde Windows die
; 32-Bit-PowerShell starten, die z. B. nvidia-smi.exe nicht findet.
Var PSEXE
!macro FindPowerShell
  StrCpy $PSEXE "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
  ${If} ${RunningX64}
  ${AndIf} ${FileExists} "$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
    StrCpy $PSEXE "$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
  ${EndIf}
!macroend

!define APPNAME "VoiceClone v2"
!define APPKEY  "VoiceCloneV2"
!define VERSION "2.1.0"
!define UNINST  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}"

; Programmstarter mit Icon zuerst bauen
!makensis "launcher.nsi"

Name "${APPNAME}"
OutFile "VoiceCloneV2-Setup.exe"
InstallDir "$LOCALAPPDATA\${APPKEY}"
InstallDirRegKey HKCU "Software\${APPKEY}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
BrandingText "${APPNAME} ${VERSION}"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "FileDescription" "${APPNAME} Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Apache-2.0"

!define MUI_ICON "..\ui\icon.ico"
!define MUI_UNICON "..\ui\icon.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Willkommen bei ${APPNAME}"
!define MUI_WELCOMEPAGE_TEXT "Stimmen klonen und Texte sprechen lassen – mit dem KI-Modell VoxCPM2.$\r$\n$\r$\nWährend der Installation werden Python (falls nötig), PyTorch und VoxCPM2 aus dem Internet geladen (ca. 4 GB, 10–30 Minuten). Beim ersten Programmstart folgt das Sprachmodell (ca. 5 GB).$\r$\n$\r$\nEmpfohlen: NVIDIA-Grafikkarte mit mindestens 8 GB Grafikspeicher.$\r$\n$\r$\nKlicke auf „Weiter“, um fortzufahren."
!define MUI_FINISHPAGE_TITLE "${APPNAME} ist bereit"
!define MUI_FINISHPAGE_TEXT "Die Installation ist abgeschlossen. Du findest ${APPNAME} auf dem Desktop und im Startmenü."
!define MUI_FINISHPAGE_RUN "$INSTDIR\VoiceClone.exe"
!define MUI_FINISHPAGE_RUN_TEXT "${APPNAME} jetzt starten"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "German"

Section "Install"
  SetOutPath "$INSTDIR"
  File "VoiceClone.exe"
  File "..\voiceclone.pyw"
  File "..\server.py"
  File "..\voice_engine.py"
  File "..\requirements.txt"
  File "..\install.ps1"
  File "..\start.bat"
  File "..\README.md"
  SetOutPath "$INSTDIR\bin"
  File "bin\uv.exe"
  SetOutPath "$INSTDIR\ui"
  File "..\ui\index.html"
  File "..\ui\app.css"
  File "..\ui\app.js"
  File "..\ui\icon.svg"
  File "..\ui\icon.ico"
  File "..\ui\icon.png"
  SetOutPath "$INSTDIR"

  WriteRegStr HKCU "Software\${APPKEY}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINST}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "${UNINST}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINST}" "DisplayIcon" "$INSTDIR\ui\icon.ico"
  WriteRegStr HKCU "${UNINST}" "Publisher" "VoiceClone"
  WriteRegStr HKCU "${UNINST}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${UNINST}" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "${UNINST}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST}" "NoRepair" 1

  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\VoiceClone.exe" "" "$INSTDIR\ui\icon.ico" 0
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\VoiceClone.exe" "" "$INSTDIR\ui\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME} (mit Konsole).lnk" "$INSTDIR\start.bat" "" "$INSTDIR\ui\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Deinstallieren.lnk" "$INSTDIR\Uninstall.exe"

  !insertmacro FindPowerShell
  DetailPrint ""
  DetailPrint "Richte Python, PyTorch und VoxCPM2 ein – das kann 10–30 Minuten dauern ..."
  nsExec::ExecToLog '"$PSEXE" -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\install.ps1" -NonInteractive'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "Die Einrichtung ist fehlgeschlagen (Details: $INSTDIR\install.log).$\r$\nBeim nächsten Start von ${APPNAME} wird sie automatisch erneut versucht."
  ${EndIf}
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  RMDir /r "$INSTDIR\.venv"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\runtime"
  RMDir /r "$INSTDIR\bin"
  RMDir /r "$INSTDIR\ui"
  RMDir /r "$INSTDIR\webview_data"
  RMDir /r "$INSTDIR\recordings"
  RMDir /r "$INSTDIR\__pycache__"
  Delete "$INSTDIR\VoiceClone.exe"
  Delete "$INSTDIR\voiceclone.pyw"
  Delete "$INSTDIR\*.py"
  Delete "$INSTDIR\requirements.txt"
  Delete "$INSTDIR\install.ps1"
  Delete "$INSTDIR\start.bat"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\install.log"
  Delete "$INSTDIR\voiceclone.log"
  MessageBox MB_YESNO|MB_ICONQUESTION "Gespeicherte Stimmen, erzeugte Audiodateien und Einstellungen ebenfalls löschen?" IDNO keep
    RMDir /r "$INSTDIR\voices"
    RMDir /r "$INSTDIR\outputs"
    Delete "$INSTDIR\settings.json"
  keep:
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${UNINST}"
  DeleteRegKey HKCU "Software\${APPKEY}"
SectionEnd
