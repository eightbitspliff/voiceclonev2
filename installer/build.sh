#!/usr/bin/env bash
# Baut installer/VoiceCloneV2-Setup.exe (benötigt NSIS/makensis, curl, unzip)
set -euo pipefail
cd "$(dirname "$0")"
UV_VERSION="0.11.32"
if [ ! -f bin/uv.exe ]; then
  mkdir -p bin
  curl -sSL -o bin/uv.zip "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-pc-windows-msvc.zip"
  unzip -o -q bin/uv.zip uv.exe -d bin
  rm bin/uv.zip
fi
makensis -V2 VoiceCloneV2.nsi
ls -la VoiceCloneV2-Setup.exe
