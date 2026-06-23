# backend/app/core/ws.py
from __future__ import annotations
from collections import defaultdict
from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, ws: WebSocket, room: str) -> None:
        await ws.accept()
        self._rooms[room].append(ws)

    def disconnect(self, ws: WebSocket, room: str) -> None:
        room_list = self._rooms[room]
        if ws in room_list:
            room_list.remove(ws)

    async def broadcast(self, room: str, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._rooms[room]):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)


manager = ConnectionManager()
