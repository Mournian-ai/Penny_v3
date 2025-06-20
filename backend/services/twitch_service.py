import aiohttp
import asyncio
import os
from twitchio.ext import commands
from services.event_bus import EventBus
from config import settings

async def refresh_oauth_token():
    """
    Refreshes the Twitch OAuth token using the refresh token from .env.
    Returns the new access token or None if failed.
    """
    print("[Twitch] Refreshing OAuth token...")
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("TWITCH_REFRESH_TOKEN"),
        "client_id": os.getenv("TWITCH_CLIENT_ID"),
        "client_secret": os.getenv("TWITCH_CLIENT_SECRET")
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            if "access_token" in data:
                print("[Twitch] New OAuth token acquired.")
                return data["access_token"]
            else:
                print(f"[Twitch] Failed to refresh token: {data}")
                return None

async def start_chat_listener():
    token = await refresh_oauth_token()
    if not token:
        print("[Twitch] Cannot start chat bot without valid OAuth token.")
        return

    class PennyTwitchBot(commands.Bot):
        def __init__(self):
            super().__init__(
                token=token,
                prefix="!",
                initial_channels=[settings.TWITCH_CHANNEL]
            )

        async def event_ready(self):
            print(f"[Twitch] Connected as {self.nick}")

        async def event_message(self, message):
            if message.echo:
                return

            user = message.author.name
            content = message.content.strip()
            print(f"[Chat] {user}: {content}")

            if "penny" in content.lower():
                await EventBus.emit("transcription", {
                    "text": content,
                    "username": user
                })

    bot = PennyTwitchBot()
    await bot.start()
