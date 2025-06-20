from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    UNITY_WS_PORT = int(os.getenv("UNITY_WS_PORT", 8765))
    TTS_OUTPUT_PATH = os.getenv("TTS_OUTPUT_PATH", "output.wav")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
    TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
    TWITCH_OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

settings = Settings()
