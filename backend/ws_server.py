import asyncio
import websockets
import json

connected_clients = set()

async def handler(ws):
    connected_clients.add(ws)
    try:
        async for _ in ws:
            pass  # No incoming messages needed for now
    finally:
        connected_clients.remove(ws)

async def broadcast(data: dict):
    if connected_clients:
        message = json.dumps(data)
        await asyncio.gather(*[ws.send(message) for ws in connected_clients])

def start_ws_server():
    return websockets.serve(handler, "0.0.0.0", 8765)
