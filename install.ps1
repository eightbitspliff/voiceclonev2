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

function Get-NvidiaGpu {
    # nvidia-smi liegt in System32; aus 32-Bit-Prozessen ist es nur ueber "Sysnative" sichtbar
    $candidates = @(
        (Join-Path $env:windir "Sysnative\nvidia-smi.exe"),
        (Join-Path $env:windir "System32\nvidia-smi.exe"),
        (Join-Path $env:ProgramFiles "NVIDIA Corporation\NVSMI\nvidia-smi.exe")
    )
    $cmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($cmd) { $candidates = @($cmd.Source) + $candidates }
    foreach ($smi in $candidates) {
        if ($smi -and (Test-Path $smi)) {
            $out = @(& $smi --query-gpu=name --format=csv,noheader 2>$null)
            if ($LASTEXITCODE -eq 0 -and $out.Count -gt 0 -and $out[0]) { return "$($out[0])".Trim() }
        }
    }
    try {
        $vc = Get-CimInstance Win32_VideoController -ErrorAction Stop | Where-Object { $_.Name -match "NVIDIA" } | Select-Object -First 1
        if ($vc) { return $vc.Name }
    } catch {}
    return $null
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

    $gpu = Get-NvidiaGpu
    if ($gpu) {
        Step "NVIDIA-Grafikkarte gefunden: $gpu - installiere PyTorch mit CUDA 12.8 (ca. 3 GB, bitte warten)"
        $index = "https://download.pytorch.org/whl/cu128"
    } else {
        Step "Keine NVIDIA-Grafikkarte gefunden - installiere PyTorch fuer CPU (Sprachausgabe wird langsam sein)"
        $index = "https://download.pytorch.org/whl/cpu"
    }
    # Falsche Variante (z. B. CPU-Version trotz Grafikkarte) gezielt ersetzen
    $torchCuda = & $VenvPy -c "import torch; print(torch.version.cuda or 'cpu')" 2>$null
    $reinstall = @()
    if ($LASTEXITCODE -eq 0 -and $torchCuda) {
        Write-Host "Vorhandenes PyTorch: $torchCuda"
        if (($gpu -and $torchCuda -eq "cpu") -or (-not $gpu -and $torchCuda -ne "cpu")) {
            Write-Host "PyTorch-Variante passt nicht zur Hardware - wird ersetzt."
            $reinstall = @("--reinstall-package", "torch", "--reinstall-package", "torchaudio")
        }
    }
    & $uv pip install --python $VenvPy torch torchaudio --index-url $index @reinstall
    if ($LASTEXITCODE -ne 0) { throw "PyTorch-Installation fehlgeschlagen" }

    Step "Installiere VoxCPM2 und weitere Pakete"
    & $uv pip install --python $VenvPy -r (Join-Path $AppDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Paket-Installation fehlgeschlagen" }

    if ($gpu -and $OnWindows) {
        Step "Installiere Triton fuer Windows (Beschleunigung mit torch.compile)"
        # Jede PyTorch-Version braucht eine bestimmte Triton-Version (siehe triton-windows README)
        $tritonSpec = & $VenvPy -c "import torch; m = tuple(int(x) for x in torch.__version__.split('+')[0].split('.')[:2]); t = {(2,7):(3,3),(2,8):(3,4),(2,9):(3,5),(2,10):(3,6),(2,11):(3,6),(2,12):(3,7),(2,13):(3,7),(2,14):(3,8)}.get(m); print('triton-windows>=%d.%d,<%d.%d' % (t[0], t[1], t[0], t[1] + 1) if t else 'triton-windows')"
        if ($LASTEXITCODE -ne 0 -or -not $tritonSpec) { $tritonSpec = "triton-windows" }
        Write-Host "Triton-Version: $tritonSpec"
        & $uv pip install --python $VenvPy $tritonSpec
        if ($LASTEXITCODE -eq 0) {
            $env:TORCHINDUCTOR_CACHE_DIR = Join-Path $AppDir "cache\inductor"
            $env:TRITON_CACHE_DIR = Join-Path $AppDir "cache\triton"
            & $VenvPy -c "import torch; f = torch.compile(lambda x: torch.sin(x) * 2 + 1); y = f(torch.ones(64, device='cuda')); torch.cuda.synchronize(); print('torch.compile OK', round(float(y.sum()), 2))"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "torch.compile funktioniert auf diesem System nicht - Beschleunigung wird deaktiviert (VoiceClone laeuft trotzdem)." -ForegroundColor Yellow
                & $uv pip uninstall --python $VenvPy triton-windows
            }
        } else {
            Write-Host "Triton konnte nicht installiert werden - VoiceClone laeuft ohne Beschleunigung." -ForegroundColor Yellow
        }
    }

    Step "Pruefe Installation"
    & $VenvPy -c "import torch, voxcpm, fastapi, webview, sounddevice; print('PyTorch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "Pruefung fehlgeschlagen - siehe install.log" }
    if ($gpu) {
        $cudaOk = & $VenvPy -c "import torch; print(torch.cuda.is_available())" 2>$null
        if ($cudaOk -ne "True") {
            Write-Host "WARNUNG: Grafikkarte gefunden, aber CUDA ist nicht nutzbar. Bitte den NVIDIA-Treiber aktualisieren." -ForegroundColor Yellow
        }
    }
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
