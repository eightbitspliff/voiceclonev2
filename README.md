# 🎙️ VoiceClone v2

Stimmen klonen und beliebigen Text mit dieser Stimme sprechen lassen – als Windows-Programm,
basierend auf [**VoxCPM2**](https://github.com/OpenBMB/VoxCPM) (2B Parameter, 30 Sprachen inkl. Deutsch, 48 kHz Ausgabe).

## Installation (Windows)

1. **`VoiceCloneV2-Setup.exe`** ausführen (keine Admin-Rechte nötig).
2. Der Installer richtet automatisch alles ein: Python (falls nötig), PyTorch (mit CUDA bei
   NVIDIA-Grafikkarte), VoxCPM2 und alle Pakete – ca. 4 GB, 10–30 Minuten.
3. **VoiceClone v2** über die Desktop-Verknüpfung oder das Startmenü starten.
   Beim ersten Start wird das Sprachmodell geladen (ca. 5 GB, Status unten links).

Deinstallieren über *Einstellungen → Apps* oder den Startmenü-Eintrag. Stimmen und Ausgaben
können dabei auf Wunsch behalten werden.

Bei Problemen: Startmenü → *VoiceClone v2 (mit Konsole)* zeigt alle Meldungen. Details stehen
außerdem in `install.log` und `voiceclone.log` im Installationsordner (`%LOCALAPPDATA%\VoiceCloneV2`).

## Funktionen

- **Eigenes Programmfenster** mit modernem Interface, Seitenleiste und **Dark-Mode-Schalter**
  (Hell / Dunkel / wie Windows)
- **Stimmen**: Audiodateien per Drag & Drop hinzufügen (WAV, MP3, FLAC, OGG, M4A …) und/oder
  **direkt mit dem Mikrofon aufnehmen** (mit Pegelanzeige) – alles wird automatisch bereinigt,
  normalisiert und zu einer Referenz zusammengefügt
- **Automatisches Transkript** (Whisper, auch Deutsch) für maximale Ähnlichkeit („Ultimate Cloning“),
  jederzeit bearbeitbar
- **Sprechen**: Stimme wählen, Text eingeben, optional Stil-Anweisung (Vorschläge per Klick),
  Fortschritt mit Abbrechen, Wiedergabe mit Wellenform, *Speichern unter …*
- **Verlauf** aller Ausgaben mit Suche, Wiedergabe, Text wiederverwenden, Löschen
- **Einstellungen**: Farbschema, Rechengerät (GPU/CPU), Qualität, Mikrofon, Speicherorte
- Lange Texte werden automatisch in Sätze aufgeteilt; Ausgabe als 48-kHz-WAV

## Voraussetzungen

- Windows 10/11 (64 Bit), Internetverbindung für die Einrichtung
- NVIDIA-Grafikkarte mit ≥ 8 GB VRAM empfohlen (CPU funktioniert, ist aber sehr langsam)
- ca. 15 GB freier Speicher

## Tipps für gute Ergebnisse

- 10–30 Sekunden klare Sprache, nur ein Sprecher, ohne Musik, Hall oder Hintergrundgeräusche.
- „Maximale Ähnlichkeit“ nutzt das Transkript – es muss exakt dem Gesprochenen entsprechen
  (unter *Stimmen → Transkript* korrigierbar).
- Für Stil-Anweisungen „Maximale Ähnlichkeit“ ausschalten. Stil-Anweisungen wirken am besten auf Englisch (z. B. `cheerful`, `whispering`).
- Ist die Ausgabe unverständlich, stimmt fast immer das Transkript nicht: unter *Stimmen → Transkript* korrigieren oder „Maximale Ähnlichkeit“ ausschalten.
- Klingt das Ergebnis instabil: Textnähe (CFG) leicht senken oder Qualität (Schritte) erhöhen.

## Entwicklung / andere Systeme

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python voiceclone.pyw            # App-Fenster
python voiceclone.pyw --browser  # stattdessen im Browser öffnen
```

| Datei | Inhalt |
|---|---|
| `voiceclone.pyw` | Programmstart: lokaler Server + Programmfenster (pywebview / WebView2) |
| `server.py` | Lokale API (FastAPI) |
| `voice_engine.py` | Audio-Aufbereitung, Stimmprofile, Aufnahme, VoxCPM2-Synthese |
| `ui/` | Oberfläche (HTML/CSS/JS, läuft offline) |
| `install.ps1` | Einrichtung unter Windows (eigenes Python über uv, PyTorch, Pakete) |
| `installer/` | NSIS-Skripte für Setup und `VoiceClone.exe` |

Installer bauen (mit NSIS): `installer/build.sh`.
Bei jedem Push baut GitHub Actions den Installer automatisch (Artefakt *VoiceCloneV2-Setup*).

## Hinweis

Nutze das Programm nur mit Stimmen, für die du die Erlaubnis der betreffenden Person hast.
Das Klonen fremder Stimmen ohne Zustimmung kann gegen Persönlichkeitsrechte und Gesetze verstoßen.
