# backend/app/crm/routers/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security.jwt import decode_token
from app.core.ws import manager

router = APIRouter(prefix="/crm/ws", tags=["crm-ws"])


@router.websocket("/kanban")
async def kanban_ws(ws: WebSocket, token: str) -> None:
    try:
        claims = decode_token(token)
        tenant_id = claims["tenant_id"]
    except Exception:
        await ws.close(code=4001)
        return

    room = f"kanban:{tenant_id}"
    await manager.connect(ws, room)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, room)
