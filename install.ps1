# VoiceClone v2 - Einrichtung unter Windows
# Sucht Python 3.10-3.12 (installiert bei Bedarf Python 3.11 lokal), legt eine
# virtuelle Umgebung an und installiert PyTorch (CUDA oder CPU) + alle Pakete.
# -NonInteractive: keine Rueckfragen (wird vom Installer verwendet)
param([switch]$NonInteractive)

$ErrorActionPreference = "Continue"  # Fehler werden explizit per Exit-Code geprueft
$ProgressPreference = "SilentlyContinue"
$env:PIP_PROGRESS_BAR = "off"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:PYTHONIOENCODING = "utf-8"
$AppDir = $PSScriptRoot
Set-Location $AppDir
Start-Transcript -Path (Join-Path $AppDir "install.log") -Append | Out-Null

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }

function Test-Python($exe, $extraArgs) {
    try {
        $v = & $exe @extraArgs -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -match '^3\.(10|11|12)$') { return $true }
    } catch {}
    return $false
}

function Test-WebView2 {
    $id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    foreach ($key in @("HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$id",
                       "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$id",
                       "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$id")) {
        $pv = (Get-ItemProperty -Path $key -Name pv -ErrorAction SilentlyContinue).pv
        if ($pv -and $pv -ne "0.0.0.0") { return $true }
    }
    return $false
}

try {
    Step "Suche passende Python-Version (3.10 - 3.12)"
    $py = $null; $pyArgs = @()
    $local = Join-Path $AppDir "python\python.exe"
    if (Test-Path $local) { $py = $local }
    if (-not $py -and (Get-Command py -ErrorAction SilentlyContinue)) {
        foreach ($ver in "-3.11", "-3.12", "-3.10") {
            if (Test-Python "py" @($ver)) { $py = "py"; $pyArgs = @($ver); break }
        }
    }
    if (-not $py -and (Get-Command python -ErrorAction SilentlyContinue)) {
        if (Test-Python "python" @()) { $py = "python" }
    }
    if (-not $py) {
        Step "Keine passende Python-Version gefunden - lade Python 3.11 herunter (ca. 25 MB)"
        $setup = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
        Invoke-WebRequest "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $setup -UseBasicParsing -ErrorAction Stop
        Step "Installiere Python 3.11 nach $AppDir\python"
        $p = Start-Process $setup -Wait -PassThru -ErrorAction Stop -ArgumentList @(
            "/quiet", "InstallAllUsers=0", "PrependPath=0", "Include_launcher=0",
            "Include_test=0", "Shortcuts=0", "AssociateFiles=0", "TargetDir=`"$AppDir\python`"")
        if ($p.ExitCode -ne 0) { throw "Python-Installation fehlgeschlagen (Code $($p.ExitCode))" }
        $py = $local
    }
    Write-Host "Verwende: $py $pyArgs"

    if (-not (Test-WebView2)) {
        Step "Installiere Microsoft Edge WebView2 (fuer das Programmfenster)"
        try {
            $wv = Join-Path $env:TEMP "MicrosoftEdgeWebview2Setup.exe"
            Invoke-WebRequest "https://go.microsoft.com/fwlink/p/?LinkId=2124703" -OutFile $wv -UseBasicParsing -ErrorAction Stop
            Start-Process $wv -Wait -ArgumentList "/silent", "/install" | Out-Null
        } catch {
            Write-Host "WebView2 konnte nicht installiert werden ($_) - das Programm oeffnet sich dann im Browser."
        }
    }

    $venvPy = Join-Path $AppDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPy)) {
        Step "Erstelle virtuelle Umgebung"
        & $py @pyArgs -m venv (Join-Path $AppDir ".venv")
        if ($LASTEXITCODE -ne 0) { throw "venv konnte nicht erstellt werden" }
    }
    & $venvPy -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip-Update fehlgeschlagen" }

    $hasNvidia = [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)
    if ($hasNvidia) {
        Step "NVIDIA-Grafikkarte gefunden - installiere PyTorch mit CUDA (ca. 3 GB, bitte warten)"
        $index = "https://download.pytorch.org/whl/cu128"
    } else {
        Step "Keine NVIDIA-Grafikkarte gefunden - installiere PyTorch fuer CPU (Sprachausgabe wird langsam sein)"
        $index = "https://download.pytorch.org/whl/cpu"
    }
    & $venvPy -m pip install torch torchaudio --index-url $index
    if ($LASTEXITCODE -ne 0) { throw "PyTorch-Installation fehlgeschlagen" }

    Step "Installiere VoxCPM2 und weitere Pakete"
    & $venvPy -m pip install -r (Join-Path $AppDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Paket-Installation fehlgeschlagen" }

    Step "Pruefe Installation"
    & $venvPy -c "import torch, voxcpm, fastapi, webview, sounddevice; print('PyTorch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "Pruefung fehlgeschlagen - siehe install.log" }

    Step "Einrichtung abgeschlossen."
    Stop-Transcript | Out-Null
    exit 0
} catch {
    Write-Host ""
    Write-Host "FEHLER: $_" -ForegroundColor Red
    Write-Host "Details stehen in $AppDir\install.log"
    Stop-Transcript | Out-Null
    if (-not $NonInteractive) { Read-Host "Enter druecken zum Schliessen" }
    exit 1
}
