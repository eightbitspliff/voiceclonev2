"""VoiceClone v2 – Stimmen klonen mit VoxCPM2 (Gradio-Oberfläche)."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from pathlib import Path

import gradio as gr

import voice_engine as ve

ENGINE: ve.Engine | None = None
NO_VOICE = "— Keine (Standardstimme) —"


# --------------------------------------------------------------------------- #
# Callbacks
# --------------------------------------------------------------------------- #
def _voice_choices() -> list[str]:
    return [NO_VOICE] + ve.list_profiles()


def add_recording(recording, recordings: list[str]):
    if not recording:
        gr.Warning("Bitte zuerst etwas mit dem Mikrofon aufnehmen.")
        return recordings, _recordings_info(recordings), gr.update()
    dst = Path(tempfile.gettempdir()) / f"vc_mic_{int(time.time() * 1000)}.wav"
    shutil.copy(recording, dst)
    recordings = recordings + [str(dst)]
    return recordings, _recordings_info(recordings), None


def clear_recordings():
    return [], _recordings_info([])


def _recordings_info(recordings: list[str]) -> str:
    if not recordings:
        return "Noch keine Mikrofonaufnahmen hinzugefügt."
    return f"**{len(recordings)}** Mikrofonaufnahme(n) bereit."


def read_voice(name, files, recording, recordings, max_seconds, auto_transcript, progress=gr.Progress()):
    name = (name or "").strip()
    if not name:
        raise gr.Error("Bitte einen Namen für die Stimme eingeben.")

    paths = [f if isinstance(f, str) else f.name for f in (files or [])]
    paths += list(recordings or [])
    if recording and recording not in paths:  # noch nicht hinzugefügte Aufnahme mitnehmen
        paths.append(recording)
    if not paths:
        raise gr.Error("Bitte Audiodateien hochladen oder eine Aufnahme mit dem Mikrofon machen.")

    progress(0.1, desc="Lese Audiodateien …")
    try:
        audio, used = ve.build_reference(paths, float(max_seconds))
    except ValueError as exc:
        raise gr.Error(str(exc))

    transcript = ""
    profile = ve.save_profile(name, audio, transcript, used)

    if auto_transcript:
        progress(0.5, desc="Erstelle Transkript (Spracherkennung) …")
        try:
            transcript = ENGINE.transcribe(str(profile.wav_path))
            ve.update_transcript(name, transcript)
        except Exception as exc:
            gr.Warning(f"Automatisches Transkript fehlgeschlagen: {exc}")

    progress(1.0, desc="Fertig")
    info = (f"✅ Stimme **{profile.name}** eingelesen – {profile.duration:.1f} s Referenz "
            f"aus {len(used)} Datei(en): {', '.join(used)}")
    choices = _voice_choices()
    return (info, str(profile.wav_path), transcript,
            gr.update(choices=choices, value=profile.name),
            gr.update(choices=choices[1:], value=profile.name))


def show_voice(name):
    profile = ve.load_profile(name) if name and name != NO_VOICE else None
    if profile is None:
        return None, "", "Standardstimme des Modells (kein Klonen)."
    details = f"Referenz: {profile.duration:.1f} s · erstellt {profile.created} · Quellen: {', '.join(profile.sources)}"
    return str(profile.wav_path), profile.transcript, details


def save_transcript(name, transcript):
    if not name or name == NO_VOICE:
        raise gr.Error("Keine Stimme ausgewählt.")
    ve.update_transcript(name, transcript or "")
    gr.Info("Transkript gespeichert.")


def remove_voice(name):
    if not name or name == NO_VOICE:
        raise gr.Error("Keine Stimme ausgewählt.")
    ve.delete_profile(name)
    gr.Info(f"Stimme „{name}“ gelöscht.")
    choices = _voice_choices()
    return gr.update(choices=choices, value=NO_VOICE), gr.update(choices=choices[1:], value=None)


def refresh_voices():
    choices = _voice_choices()
    return gr.update(choices=choices), gr.update(choices=choices[1:])


def generate(voice, text, style, use_transcript, cfg_value, steps, normalize, denoise, progress=gr.Progress()):
    if not text or not text.strip():
        raise gr.Error("Bitte einen Text eingeben.")
    profile = None
    if voice and voice != NO_VOICE:
        profile = ve.load_profile(voice)
        if profile is None:
            raise gr.Error(f"Stimme „{voice}“ nicht gefunden.")
    progress(0, desc="Lade Modell (beim ersten Mal kann das dauern) …")
    try:
        sr, audio = ENGINE.synthesize(
            text, profile, style=style or "", use_transcript=use_transcript,
            cfg_value=cfg_value, inference_timesteps=steps,
            normalize=normalize, denoise=denoise, progress=progress,
        )
    except Exception as exc:
        raise gr.Error(f"Fehler bei der Sprachausgabe: {exc}")
    path = ve.save_output(sr, audio, profile.name if profile else None)
    return str(path), str(path)


# --------------------------------------------------------------------------- #
# Oberfläche
# --------------------------------------------------------------------------- #
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="VoiceClone v2 – VoxCPM2") as demo:
        gr.Markdown("# 🎙️ VoiceClone v2\nStimmen klonen und Text sprechen lassen – powered by **VoxCPM2**")

        recordings = gr.State([])

        with gr.Tab("1 · Stimme einlesen"):
            with gr.Row():
                with gr.Column():
                    voice_name = gr.Textbox(label="Name der Stimme", placeholder="z. B. Florian")
                    files = gr.File(label="Audiodateien hochladen (WAV, MP3, FLAC, OGG, M4A …)",
                                    file_count="multiple", file_types=["audio"])
                    mic = gr.Audio(label="Oder selbst aufnehmen (Mikrofon)", sources=["microphone"],
                                   type="filepath")
                    with gr.Row():
                        add_btn = gr.Button("➕ Aufnahme hinzufügen")
                        clear_btn = gr.Button("🗑️ Aufnahmen leeren")
                    rec_info = gr.Markdown(_recordings_info([]))
                    with gr.Accordion("Optionen", open=False):
                        max_seconds = gr.Slider(5, 60, value=30, step=1,
                                                label="Maximale Referenzlänge (Sekunden)")
                        auto_transcript = gr.Checkbox(
                            value=True,
                            label="Transkript automatisch erstellen (für „Ultimate Cloning“, höchste Ähnlichkeit)")
                    read_btn = gr.Button("📥 Stimme einlesen", variant="primary")
                with gr.Column():
                    read_info = gr.Markdown()
                    ref_preview = gr.Audio(label="Erzeugte Referenz", type="filepath", interactive=False)
                    ref_transcript = gr.Textbox(label="Transkript der Referenz", lines=4, interactive=False)
                    gr.Markdown(
                        "**Tipps:** 10–30 s klare Sprache ohne Musik/Hall ergeben die besten Ergebnisse. "
                        "Mehrere Dateien werden automatisch zu einer Referenz zusammengefügt.")

        with gr.Tab("2 · Text sprechen"):
            with gr.Row():
                with gr.Column():
                    voice_select = gr.Dropdown(label="Stimme", choices=_voice_choices(), value=NO_VOICE)
                    voice_details = gr.Markdown("Standardstimme des Modells (kein Klonen).")
                    text = gr.Textbox(label="Text", lines=8,
                                      placeholder="Gib hier den Text ein, der mit der geklonten Stimme gesprochen werden soll …")
                    style = gr.Textbox(label="Stil-Anweisung (optional)",
                                       placeholder="z. B. fröhlich, etwas schneller / whispering, calm")
                    use_transcript = gr.Checkbox(
                        value=True,
                        label="Transkript nutzen (Ultimate Cloning – höchste Ähnlichkeit, Stil-Anweisung wird dann ignoriert)")
                    with gr.Accordion("Erweiterte Einstellungen", open=False):
                        cfg_value = gr.Slider(1.0, 3.0, value=2.0, step=0.1, label="CFG (Textnähe / Stabilität)")
                        steps = gr.Slider(4, 30, value=10, step=1, label="Inferenz-Schritte (mehr = besser, langsamer)")
                        normalize = gr.Checkbox(value=False, label="Text normalisieren (Zahlen, Abkürzungen)")
                        denoise = gr.Checkbox(value=False,
                                              label="Referenz entrauschen (nur mit Startoption --denoiser)")
                    gen_btn = gr.Button("🔊 Sprechen", variant="primary")
                with gr.Column():
                    out_audio = gr.Audio(label="Ergebnis", type="filepath", interactive=False)
                    out_file = gr.File(label="Download (WAV, 48 kHz)")

        with gr.Tab("Stimmen verwalten"):
            manage_select = gr.Dropdown(label="Gespeicherte Stimme", choices=ve.list_profiles(), value=None)
            manage_details = gr.Markdown()
            manage_audio = gr.Audio(label="Referenz", type="filepath", interactive=False)
            manage_transcript = gr.Textbox(
                label="Transkript (muss exakt dem Gesprochenen in der Referenz entsprechen)", lines=4)
            with gr.Row():
                save_tr_btn = gr.Button("💾 Transkript speichern")
                refresh_btn = gr.Button("🔄 Liste aktualisieren")
                delete_btn = gr.Button("❌ Stimme löschen", variant="stop")

        # Events
        add_btn.click(add_recording, [mic, recordings], [recordings, rec_info, mic])
        clear_btn.click(clear_recordings, None, [recordings, rec_info])
        read_btn.click(
            read_voice,
            [voice_name, files, mic, recordings, max_seconds, auto_transcript],
            [read_info, ref_preview, ref_transcript, voice_select, manage_select],
        )
        voice_select.change(lambda n: show_voice(n)[2], voice_select, voice_details)
        manage_select.change(lambda n: (show_voice(n)[0], show_voice(n)[1], show_voice(n)[2]),
                             manage_select, [manage_audio, manage_transcript, manage_details])
        save_tr_btn.click(save_transcript, [manage_select, manage_transcript], None)
        refresh_btn.click(refresh_voices, None, [voice_select, manage_select])
        delete_btn.click(remove_voice, manage_select, [voice_select, manage_select])
        gen_btn.click(
            generate,
            [voice_select, text, style, use_transcript, cfg_value, steps, normalize, denoise],
            [out_audio, out_file],
        )
        demo.load(refresh_voices, None, [voice_select, manage_select])
    return demo


def main():
    parser = argparse.ArgumentParser(description="VoiceClone v2 – Stimmen klonen mit VoxCPM2")
    parser.add_argument("--model", default="openbmb/VoxCPM2",
                        help="HuggingFace-ID oder lokaler Pfad des Modells")
    parser.add_argument("--device", default=None, help="z. B. cuda, cuda:0, mps, cpu (Standard: automatisch)")
    parser.add_argument("--optimize", action="store_true", help="torch.compile aktivieren (schneller, nur Linux+CUDA)")
    parser.add_argument("--denoiser", action="store_true", help="ZipEnhancer-Entrauscher laden")
    parser.add_argument("--preload", action="store_true", help="Modell schon beim Start laden")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", help="Öffentlichen Gradio-Link erzeugen")
    parser.add_argument("--inbrowser", action="store_true", help="Browser automatisch öffnen")
    args = parser.parse_args()

    global ENGINE
    ENGINE = ve.Engine(args.model, device=args.device, optimize=args.optimize, load_denoiser=args.denoiser)
    if args.preload:
        _ = ENGINE.model

    build_ui().queue(default_concurrency_limit=1).launch(
        server_name=args.host, server_port=args.port, share=args.share, inbrowser=args.inbrowser,
        theme=gr.themes.Soft(), allowed_paths=[str(ve.VOICES_DIR), str(ve.OUTPUTS_DIR)],
    )


if __name__ == "__main__":
    main()
