; VoiceClone.exe - Programmstarter (wird vom Installer mitgeliefert)
; Startet die App ohne Konsolenfenster; richtet sie bei Bedarf zuerst ein.
Unicode true
Name "VoiceClone v2"
OutFile "VoiceClone.exe"
Icon "..\ui\icon.ico"
RequestExecutionLevel user
SilentInstall silent
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
VIProductVersion "2.2.0.0"
VIAddVersionKey "ProductName" "VoiceClone v2"
VIAddVersionKey "FileDescription" "VoiceClone v2 - Stimmen klonen mit VoxCPM2"
VIAddVersionKey "FileVersion" "2.2.0"
VIAddVersionKey "LegalCopyright" "Apache-2.0 (VoxCPM2: OpenBMB)"

Section
  SetOutPath "$EXEDIR"
  !insertmacro FindPowerShell
  IfFileExists "$EXEDIR\.venv\Scripts\pythonw.exe" run
    MessageBox MB_YESNO|MB_ICONQUESTION "VoiceClone v2 ist noch nicht vollständig eingerichtet.$\r$\nJetzt einrichten? (Download ca. 4 GB, dauert 10-30 Minuten)" IDNO done
    ExecWait '"$PSEXE" -NoProfile -ExecutionPolicy Bypass -File "$EXEDIR\install.ps1"'
    IfFileExists "$EXEDIR\.venv\Scripts\pythonw.exe" run
    MessageBox MB_ICONSTOP "Die Einrichtung ist fehlgeschlagen. Details: $EXEDIR\install.log"
    Goto done
  run:
  Exec '"$EXEDIR\.venv\Scripts\pythonw.exe" "$EXEDIR\voiceclone.pyw"'
  done:
SectionEnd
