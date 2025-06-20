import asyncio
from ws_server import start_ws_server
from services.tts_service import speak
from services.whisper_service import start_listening
from services.twitch_service import start_chat_listener
from services.eventsub_service import start_eventsub_listener
from services.message_router import init_message_router

async def main():
    print("[Penny] Starting core systems...")

    # Start WebSocket server for Unity
    await start_ws_server()
    print("[WebSocket] Server running on port 8765")

    # Init message routing subscriptions (chat, events, etc.)
    init_message_router()

    # Start Twitch Chat Bot
    asyncio.create_task(start_chat_listener())

    # Start Twitch EventSub Conduits
    asyncio.create_task(start_eventsub_listener())

    # Start Whisper VAD listener
    asyncio.create_task(start_listening())

    # Keep alive
    await asyncio.Future()  # Infinite wait

if __name__ == "__main__":
    asyncio.run(main())
