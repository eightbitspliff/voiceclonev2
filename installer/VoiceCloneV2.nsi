; VoiceClone v2 - Windows-Installer (NSIS)
; Bauen: makensis installer/VoiceCloneV2.nsi  ->  installer/VoiceCloneV2-Setup.exe

Unicode true
!include "MUI2.nsh"

!define APPNAME "VoiceClone v2"
!define APPKEY  "VoiceCloneV2"
!ifndef VERSION
  !define VERSION "1.0.0"
!endif

Name "${APPNAME}"
OutFile "VoiceCloneV2-Setup.exe"
InstallDir "$LOCALAPPDATA\${APPKEY}"
InstallDirRegKey HKCU "Software\${APPKEY}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "${APPNAME} ${VERSION} - powered by VoxCPM2"

!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Willkommen bei ${APPNAME}"
!define MUI_WELCOMEPAGE_TEXT "Dieses Programm installiert ${APPNAME} - Stimmen klonen und Text sprechen lassen mit VoxCPM2.$\r$\n$\r$\nWährend der Installation werden Python (falls nötig), PyTorch und VoxCPM2 aus dem Internet geladen (ca. 4 GB). Beim ersten Start folgt das Sprachmodell (ca. 5 GB).$\r$\n$\r$\nEmpfohlen: NVIDIA-Grafikkarte mit mind. 8 GB Speicher."
!define MUI_FINISHPAGE_RUN "$INSTDIR\start.bat"
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
  File "..\app.py"
  File "..\voice_engine.py"
  File "..\requirements.txt"
  File "..\install.ps1"
  File "..\start.bat"
  File "..\README.md"

  WriteRegStr HKCU "Software\${APPKEY}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}" "InstallLocation" "$INSTDIR"

  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\start.bat" "" "$SYSDIR\SndVol.exe" 0
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\start.bat" "" "$SYSDIR\SndVol.exe" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Deinstallieren.lnk" "$INSTDIR\Uninstall.exe"

  DetailPrint "Richte Python, PyTorch und VoxCPM2 ein (das kann 10-30 Minuten dauern) ..."
  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\install.ps1"' $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "Die Einrichtung ist fehlgeschlagen (Details: $INSTDIR\install.log).$\r$\nBeim nächsten Start von ${APPNAME} wird sie automatisch erneut versucht."
  ${EndIf}
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  MessageBox MB_YESNO|MB_ICONQUESTION "Gespeicherte Stimmen und erzeugte Audiodateien ebenfalls löschen?" IDYES delall
    RMDir /r "$INSTDIR\.venv"
    RMDir /r "$INSTDIR\python"
    Delete "$INSTDIR\*.py"
    Delete "$INSTDIR\*.txt"
    Delete "$INSTDIR\*.ps1"
    Delete "$INSTDIR\*.bat"
    Delete "$INSTDIR\*.md"
    Delete "$INSTDIR\install.log"
    Delete "$INSTDIR\Uninstall.exe"
    Goto done
  delall:
    RMDir /r "$INSTDIR"
  done:
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPKEY}"
  DeleteRegKey HKCU "Software\${APPKEY}"
SectionEnd
