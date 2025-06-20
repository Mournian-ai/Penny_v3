import subprocess
from config import settings
from services.event_bus import EventBus

PIPER_PATH = "/home/mournian/piper/src/python/.venv/bin/piper"
PIPER_MODEL = "/home/mournian/piper/voices/glados.onnx"  # change path if needed

async def speak(text: str, mood: str = "neutral"):
    print(f"[TTS] Speaking: {text} (mood: {mood})")

    try:
        subprocess.run([
            PIPER_PATH,
            "--model", PIPER_MODEL,
            "--output_file", settings.TTS_OUTPUT_PATH,
            "--sentence_silence", "0.2",
            "--length_scale", "1.0",
        ], input=text.encode(), check=True)

        # Notify Unity to play this file
        await EventBus.emit("speak", {
            "file": settings.TTS_OUTPUT_PATH,
            "text": text,
            "mood": mood
        })

    except Exception as e:
        print(f"[TTS] Error generating audio: {e}")
