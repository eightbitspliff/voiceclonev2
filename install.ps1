# VoiceClone v2 - Einrichtung unter Windows
# Richtet mit "uv" ein eigenes Python 3.11 im Programmordner ein (unabhaengig von
# bereits installierten Pythons), legt die virtuelle Umgebung an und installiert
# PyTorch (CUDA oder CPU) + alle Pakete.
# -NonInteractive: keine Rueckfragen (wird vom Installer verwendet)
param([switch]$NonInteractive)

$ErrorActionPreference = "Continue"  # Fehler werden explizit per Exit-Code geprueft
$ProgressPreference = "SilentlyContinue"
$AppDir = $PSScriptRoot
Set-Location $AppDir
Start-Transcript -Path (Join-Path $AppDir "install.log") -Append | Out-Null

$env:PYTHONIOENCODING = "utf-8"
$env:PIP_PROGRESS_BAR = "off"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $AppDir "runtime"
$env:UV_NO_PROGRESS = "1"
$env:UV_LINK_MODE = "copy"
$env:UV_HTTP_TIMEOUT = "300"

$UvVersion = "0.11.32"
$PyVersion = "3.11"
$VenvDir = Join-Path $AppDir ".venv"
$OnWindows = ($env:OS -eq "Windows_NT")
$VenvBin = if ($OnWindows) { Join-Path $VenvDir "Scripts" } else { Join-Path $VenvDir "bin" }
$VenvPy = Join-Path $VenvBin $(if ($OnWindows) { "python.exe" } else { "python" })

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }

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

function Get-Uv {
    $bundled = Join-Path $AppDir "bin\uv.exe"
    if (Test-Path $bundled) { return $bundled }
    if (-not $OnWindows) { return "uv" }  # nur fuer Tests unter Linux/macOS
    Step "Lade uv $UvVersion herunter"
    $zip = Join-Path $env:TEMP "uv-$UvVersion.zip"
    $dest = Join-Path $AppDir "bin"
    Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$UvVersion/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing -ErrorAction Stop
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    if (-not (Test-Path $bundled)) { throw "uv.exe nicht gefunden" }
    return $bundled
}

function Test-VenvOk {
    if (-not (Test-Path $VenvPy)) { return $false }
    $v = & $VenvPy -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    return ($LASTEXITCODE -eq 0 -and $v -match '^3\.(10|11|12)$')
}

try {
    $uv = Get-Uv
    Write-Host "uv: $uv"

    if (-not (Test-VenvOk)) {
        if (Test-Path $VenvDir) {
            Step "Entferne unvollstaendige virtuelle Umgebung"
            Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
        }
        Step "Installiere Python $PyVersion in den Programmordner"
        & $uv python install $PyVersion
        if ($LASTEXITCODE -ne 0) { throw "Python $PyVersion konnte nicht installiert werden" }

        Step "Erstelle virtuelle Umgebung"
        & $uv venv --python $PyVersion --managed-python $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "Virtuelle Umgebung konnte nicht erstellt werden" }
    }
    if (-not (Test-VenvOk)) { throw "Python in der virtuellen Umgebung funktioniert nicht ($VenvPy)" }
    & $VenvPy --version

    if ($OnWindows -and -not (Test-WebView2)) {
        Step "Installiere Microsoft Edge WebView2 (fuer das Programmfenster)"
        try {
            $wv = Join-Path $env:TEMP "MicrosoftEdgeWebview2Setup.exe"
            Invoke-WebRequest "https://go.microsoft.com/fwlink/p/?LinkId=2124703" -OutFile $wv -UseBasicParsing -ErrorAction Stop
            Start-Process $wv -Wait -ArgumentList "/silent", "/install" | Out-Null
        } catch {
            Write-Host "WebView2 konnte nicht installiert werden ($_) - das Programm oeffnet sich dann im Browser."
        }
    }

    $hasNvidia = [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)
    if ($hasNvidia) {
        Step "NVIDIA-Grafikkarte gefunden - installiere PyTorch mit CUDA (ca. 3 GB, bitte warten)"
        $index = "https://download.pytorch.org/whl/cu128"
    } else {
        Step "Keine NVIDIA-Grafikkarte gefunden - installiere PyTorch fuer CPU (Sprachausgabe wird langsam sein)"
        $index = "https://download.pytorch.org/whl/cpu"
    }
    & $uv pip install --python $VenvPy torch torchaudio --index-url $index
    if ($LASTEXITCODE -ne 0) { throw "PyTorch-Installation fehlgeschlagen" }

    Step "Installiere VoxCPM2 und weitere Pakete"
    & $uv pip install --python $VenvPy -r (Join-Path $AppDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Paket-Installation fehlgeschlagen" }

    Step "Pruefe Installation"
    & $VenvPy -c "import torch, voxcpm, fastapi, webview, sounddevice; print('PyTorch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "Pruefung fehlgeschlagen - siehe install.log" }
    if ($OnWindows -and -not (Test-Path (Join-Path $VenvBin "pythonw.exe"))) {
        Copy-Item $VenvPy (Join-Path $VenvBin "pythonw.exe")
    }

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
