#!/usr/bin/env bash
# Startet VoiceClone v2 unter Linux/macOS (legt beim ersten Start eine virtuelle Umgebung an)
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi
exec .venv/bin/python voiceclone.pyw "$@"
