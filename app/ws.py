from collections import defaultdict
from typing import Dict

from fastapi import WebSocket


class WebsocketConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket] = defaultdict(list)

    async def connect(self, websocket: WebSocket, game: str):
        await websocket.accept()
        self.active_connections[game].append(websocket)

    def disconnect(self, websocket: WebSocket, game: str):
        self.active_connections[game].remove(websocket)

    async def broadcast(self, message: str, game: str):
        for connection in self.active_connections.get(game, []):
            await connection.send_text(message)
