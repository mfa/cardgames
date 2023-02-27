import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict

from fastapi import WebSocket
from fastapi.templating import Jinja2Templates


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


def gen_templates():
    templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

    def to_svg(value):
        value = value.replace("-", "_").lower()
        return f"white_{value}.svg"

    templates.env.filters["to_svg"] = to_svg
    return templates


def create_user():
    return str(uuid.uuid4())
