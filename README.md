# 🎙️ VoiceClone v2

Stimmen klonen und beliebigen Text mit dieser Stimme sprechen lassen – basierend auf
[**VoxCPM2**](https://github.com/OpenBMB/VoxCPM) (2B Parameter, 30 Sprachen inkl. Deutsch, 48 kHz Ausgabe).

## Funktionen

- **Audiodateien hochladen** (WAV, MP3, FLAC, OGG, M4A …) – auch mehrere auf einmal
- **Selbst aufnehmen** per Mikrofon direkt im Browser (mehrere Aufnahmen möglich)
- Automatische Aufbereitung: Mono/16 kHz, Stille am Rand entfernen, Lautstärke normalisieren,
  alle Aufnahmen zu einer Referenz zusammenfügen
- **Automatisches Transkript** (SenseVoice) für *Ultimate Cloning* → höchste Ähnlichkeit
- **Text zu Sprache** mit der geklonten Stimme, auch lange Texte (werden automatisch in Sätze aufgeteilt)
- Optionale **Stil-Anweisung** (z. B. „fröhlich, etwas schneller“)
- Stimmen werden als Profile gespeichert (`voices/`) und können wiederverwendet, bearbeitet und gelöscht werden
- Ergebnisse als 48-kHz-WAV in `outputs/` und zum Download

## Voraussetzungen

- Python **3.10 – 3.12**
- NVIDIA-GPU mit CUDA ≥ 12 empfohlen (ca. 8 GB VRAM). CPU funktioniert, ist aber sehr langsam.
- Beim ersten Start wird das Modell `openbmb/VoxCPM2` (~5 GB) von HuggingFace heruntergeladen.

## Installation & Start

**Windows:** `start.bat` doppelklicken.

**Linux / macOS:**
```bash
./start.sh
```

**Manuell:**
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128   # passend zu deiner CUDA-Version
pip install -r requirements.txt
python app.py
```

Danach im Browser **http://127.0.0.1:7860** öffnen.

> Das Mikrofon funktioniert im Browser nur über `localhost`/`127.0.0.1` oder HTTPS
> (bzw. mit `--share`). Beim ersten Aufnehmen den Mikrofonzugriff erlauben.

### Startoptionen

| Option | Beschreibung |
|---|---|
| `--model PFAD` | HuggingFace-ID oder lokaler Ordner des Modells (Standard `openbmb/VoxCPM2`) |
| `--device cuda\|cpu\|mps` | Gerät erzwingen (Standard: automatisch) |
| `--preload` | Modell sofort beim Start laden statt bei der ersten Anfrage |
| `--optimize` | `torch.compile` aktivieren (schneller, nur Linux + CUDA) |
| `--denoiser` | ZipEnhancer laden, um verrauschte Referenzen zu entrauschen |
| `--port 7860` / `--host 0.0.0.0` | Netzwerk-Einstellungen |
| `--share` | Öffentlichen Gradio-Link erzeugen |

## Bedienung

1. **Tab „Stimme einlesen“**: Namen eingeben, Audiodateien hochladen und/oder mit dem Mikrofon
   aufnehmen (für mehrere Aufnahmen jeweils „Aufnahme hinzufügen“) → **Stimme einlesen**.
2. **Tab „Text sprechen“**: Stimme auswählen, Text eingeben → **Sprechen**.
3. **Tab „Stimmen verwalten“**: Referenz anhören, Transkript korrigieren, Stimmen löschen.

### Tipps für gute Ergebnisse

- 10–30 Sekunden klare Sprache, nur ein Sprecher, ohne Musik, Hall oder Hintergrundgeräusche.
- *Ultimate Cloning* (Transkript nutzen) liefert die größte Ähnlichkeit – das Transkript muss
  aber exakt dem Gesprochenen entsprechen. Bei Bedarf im Tab „Stimmen verwalten“ korrigieren.
- Für Stil-Anweisungen „Transkript nutzen“ deaktivieren (Controllable Cloning).
- Klingt das Ergebnis instabil, CFG leicht senken oder Inferenz-Schritte erhöhen.

## Hinweis

Nutze das Programm nur mit Stimmen, für die du die Erlaubnis der betreffenden Person hast.
Das Klonen fremder Stimmen ohne Zustimmung kann gegen Persönlichkeitsrechte und Gesetze verstoßen.
