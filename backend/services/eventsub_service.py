import aiohttp
import asyncio
import json
import logging
from config import settings
from services.event_bus import EventBus

logger = logging.getLogger(__name__)

class EventSubService:
    def __init__(self):
        self.session = None
        self.ws = None
        self._running = False
        self._conduit_id = None
        self.app_token = None

    async def get_app_token(self):
        logger.info("[EventSub] Requesting App token...")
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": settings.TWITCH_CLIENT_ID,
            "client_secret": settings.TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        async with aiohttp.ClientSession() as temp_session:
            async with temp_session.post(url, params=params) as resp:
                data = await resp.json()
                if "access_token" in data:
                    self.app_token = data["access_token"]
                    logger.info("[EventSub] App token acquired.")
                else:
                    raise Exception(f"Failed to get app token: {data}")

    async def start(self):
        await self.get_app_token()

        self.session = aiohttp.ClientSession(headers={
            "Client-ID": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.app_token}"
        })

        await self._initialize_conduit()
        if not self._conduit_id:
            logger.error("[EventSub] Failed to get or create conduit.")
            return

        self._running = True
        asyncio.create_task(self._run_websocket())

    async def _initialize_conduit(self):
        logger.info("[EventSub] Fetching or creating conduit...")
        async with self.session.get("https://api.twitch.tv/helix/eventsub/conduits") as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('data'):
                self._conduit_id = data['data'][0]['id']
                logger.info(f"[EventSub] Found conduit: {self._conduit_id}")
                return

        async with self.session.post("https://api.twitch.tv/helix/eventsub/conduits", json={"shard_count": 1}) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('data'):
                self._conduit_id = data['data'][0]['id']
                logger.info(f"[EventSub] Created new conduit: {self._conduit_id}")

    async def _assign_shard(self, session_id):
        await self.session.patch("https://api.twitch.tv/helix/eventsub/conduits/shards", json={
            "conduit_id": self._conduit_id,
            "shards": [{
                "id": "0",
                "transport": {
                    "method": "websocket",
                    "session_id": session_id
                }
            }]
        })

    async def _subscribe_events(self):
        user_id = settings.TWITCH_USER_ID
        subs = [
            {"type": "channel.follow", "version": "2", "condition": {
                "broadcaster_user_id": user_id,
                "moderator_user_id": user_id}},
            {"type": "stream.online", "version": "1", "condition": {
                "broadcaster_user_id": user_id}},
            {"type": "channel.subscribe", "version": "1", "condition": {
                "broadcaster_user_id": user_id}},
            {"type": "channel.subscription.gift", "version": "1", "condition": {
                "broadcaster_user_id": user_id}},
            {"type": "channel.raid", "version": "1", "condition": {
                "to_broadcaster_user_id": user_id}},
            {"type": "channel.cheer", "version": "1", "condition": {
                "broadcaster_user_id": user_id}},
        ]

        for sub in subs:
            payload = {
                "type": sub["type"],
                "version": sub["version"],
                "condition": sub["condition"],
                "transport": {
                    "method": "conduit",
                    "conduit_id": self._conduit_id
                }
            }
            async with self.session.post("https://api.twitch.tv/helix/eventsub/subscriptions", json=payload) as resp:
                if resp.status not in (200, 202, 409):
                    logger.warning(f"[EventSub] Failed to subscribe to {sub['type']}")

    async def _run_websocket(self):
        url = "wss://eventsub.wss.twitch.tv/ws"
        while self._running:
            try:
                async with self.session.ws_connect(url, heartbeat=8, receive_timeout=None) as ws:
                    self.ws = ws
                    logger.info("[EventSub] Connected to WebSocket.")

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._handle_event(json.loads(msg.data))
            except Exception as e:
                logger.error(f"[EventSub] WebSocket error: {e}")
            finally:
                self.ws = None
                await asyncio.sleep(5)

    async def _handle_event(self, payload):
        mt = payload.get("metadata", {}).get("message_type")

        if mt == "session_welcome":
            session_id = payload["payload"]["session"]["id"]
            await self._assign_shard(session_id)
            await self._subscribe_events()

        elif mt == "notification":
            sub_type = payload["payload"]["subscription"]["type"]
            event_info = payload["payload"]["event"]
            user = (
                event_info.get("user_name")
                or event_info.get("from_broadcaster_user_name")
                or event_info.get("to_broadcaster_user_name")
                or "unknown"
            )

            logger.info(f"[EventSub] Received {sub_type} from {user}")
            await EventBus.emit("twitch_event", {
                "type": sub_type,
                "username": user,
                "details": event_info
            })

        elif mt == "session_reconnect":
            logger.warning("[EventSub] Reconnect requested (not yet handled).")

    async def stop(self):
        self._running = False
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

# External hook
eventsub_service = EventSubService()

async def start_eventsub_listener():
    await eventsub_service.start()
