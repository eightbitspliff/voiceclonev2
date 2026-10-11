# VoiceClone v2 - Einrichtung des zweiten Sprachmodells Qwen3-TTS (12Hz 1.7B Base)
# Eigene virtuelle Umgebung (.venv-qwen), weil qwen-tts transformers 4.57.x verlangt,
# waehrend VoxCPM2 in .venv mit einer neueren Version laeuft.
# Wird aus der App heraus (Einstellungen -> Zweites Modell) oder per Hand gestartet.
param([switch]$NonInteractive)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$AppDir = $PSScriptRoot
Set-Location $AppDir
$Log = Join-Path $AppDir "install_qwen.log"
Start-Transcript -Path $Log | Out-Null

$env:PYTHONIOENCODING = "utf-8"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $AppDir "runtime"
$env:UV_NO_PROGRESS = "1"
$env:UV_LINK_MODE = "copy"
$env:UV_HTTP_TIMEOUT = "300"

$PyVersion = "3.11"
$QwenTts = "qwen-tts==0.1.1"
$VenvDir = Join-Path $AppDir ".venv-qwen"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
$MainPy = Join-Path $AppDir ".venv\Scripts\python.exe"
$Marker = Join-Path $VenvDir ".installed"

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }

try {
    $uv = Join-Path $AppDir "bin\uv.exe"
    if (-not (Test-Path $uv)) { throw "uv.exe fehlt - bitte VoiceClone v2 neu installieren" }
    if (Test-Path $Marker) { Remove-Item $Marker -Force }

    if (-not (Test-Path $VenvPy)) {
        Step "Erstelle virtuelle Umgebung fuer Qwen3-TTS"
        & $uv venv --python $PyVersion --managed-python $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "Virtuelle Umgebung konnte nicht erstellt werden" }
    }

    # Gleiche PyTorch-Variante wie die Haupt-App (CUDA oder CPU)
    $torchInfo = & $MainPy -c "import torch; print(torch.__version__.split('+')[0], torch.version.cuda or 'cpu')" 2>$null
    $index = "https://download.pytorch.org/whl/cu128"
    $torchSpec = @("torch", "torchaudio")
    if ($LASTEXITCODE -eq 0 -and $torchInfo) {
        $parts = "$torchInfo".Trim().Split(" ")
        Write-Host "PyTorch der Haupt-App: $($parts[0]) (CUDA: $($parts[1]))"
        $torchSpec = @("torch==$($parts[0])", "torchaudio==$($parts[0])")
        if ($parts[1] -eq "cpu") { $index = "https://download.pytorch.org/whl/cpu" }
    }
    Step "Installiere PyTorch fuer Qwen3-TTS (ca. 3 GB, bitte warten)"
    & $uv pip install --python $VenvPy @torchSpec --index-url $index
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Gleiche Version nicht verfuegbar - nehme die neueste passende."
        & $uv pip install --python $VenvPy torch torchaudio --index-url $index
        if ($LASTEXITCODE -ne 0) { throw "PyTorch-Installation fehlgeschlagen" }
    }

    Step "Installiere Qwen3-TTS ($QwenTts)"
    & $uv pip install --python $VenvPy $QwenTts soundfile numpy hf_xet
    if ($LASTEXITCODE -ne 0) { throw "qwen-tts konnte nicht installiert werden" }

    Step "Pruefe Installation"
    & $VenvPy -c "import torch, qwen_tts, soundfile; print('PyTorch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "Pruefung fehlgeschlagen - siehe install_qwen.log" }

    Set-Content -Path $Marker -Value (Get-Date -Format s)
    Step "Qwen3-TTS ist eingerichtet. Das Modell (ca. 4,5 GB) wird beim ersten Sprechen geladen."
    Stop-Transcript | Out-Null
    exit 0
} catch {
    Write-Host ""
    Write-Host "FEHLER: $_" -ForegroundColor Red
    Stop-Transcript | Out-Null
    if (-not $NonInteractive) { Read-Host "Enter druecken zum Schliessen" }
    exit 1
}
