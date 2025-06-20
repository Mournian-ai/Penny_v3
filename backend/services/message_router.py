from services.event_bus import EventBus
from services.tts_service import speak
from services.openai_service import query_openai
from services.prompt_builder import build_prompt, SYSTEM_PROMPT

def init_message_router():
    EventBus.subscribe("transcription", on_transcription)
    EventBus.subscribe("twitch_event", on_twitch_event)

async def on_transcription(data):
    text = data.get("text", "") if isinstance(data, dict) else data
    speaker = data.get("username", "someone") if isinstance(data, dict) else "Mournian"

    if "penny" in text.lower():
        prompt, history = build_prompt(speaker, text)
        reply = await query_openai(prompt, history=history, system_prompt=SYSTEM_PROMPT)
        await speak(reply, mood="curious")

async def on_twitch_event(event):
    type = event.get("type")
    user = event.get("username", "someone")

    if type == "channel.subscribe":
        await speak(f"Thanks for subscribing, {user}!", mood="grateful")
    elif type == "channel.follow":
        await speak(f"Welcome aboard, {user}! Try not to break anything.", mood="snarky")
    elif type == "channel.raid":
        await speak(f"Oh no. {user} brought friends.", mood="chaotic")
    elif type == "channel.cheer":
        await speak(f"Bits! Shiny! {user}, you're my favorite wallet.", mood="greedy")
