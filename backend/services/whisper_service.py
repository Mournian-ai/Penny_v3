import sounddevice as sd
import numpy as np
import queue
import asyncio
from faster_whisper import WhisperModel
from services.event_bus import EventBus
from config import settings

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION = 0.5  # seconds
VAD_ENERGY_THRESHOLD = 30  # tweak as needed

audio_queue = queue.Queue()

model = WhisperModel(settings.WHISPER_MODEL, compute_type="auto")

def audio_callback(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata) * 10
    if volume_norm > VAD_ENERGY_THRESHOLD:
        audio_queue.put(indata.copy())

async def start_listening():
    print("[Whisper] Starting mic stream with VAD...")

    stream = sd.InputStream(
        samplerate=AUDIO_SAMPLE_RATE,
        channels=1,
        dtype='float32',
        blocksize=int(AUDIO_SAMPLE_RATE * AUDIO_CHUNK_DURATION),
        callback=audio_callback
    )

    with stream:
        while True:
            if not audio_queue.empty():
                collected = []
                for _ in range(5):  # collect ~2.5 seconds of speech
                    try:
                        frame = audio_queue.get(timeout=0.5)
                        collected.append(frame)
                    except queue.Empty:
                        break

                if collected:
                    audio_input = np.concatenate(collected, axis=0)
                    audio_input = audio_input.flatten().astype(np.float32)

                    # Normalize and convert
                    print("[Whisper] Transcribing audio...")
                    segments, _ = model.transcribe(audio_input, beam_size=5)
                    for segment in segments:
                        text = segment.text.strip()
                        print(f"[Whisper] → {text}")
                        if text:
                            await EventBus.emit("transcription", {
                                "text": text,
                                "username": "Mournian"
                            })

            await asyncio.sleep(0.1)
