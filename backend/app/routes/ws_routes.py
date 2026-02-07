from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import ws_manager

router = APIRouter(tags=["ws"])

@router.websocket("/ws/reports")
async def ws_reports(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive del cliente
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(ws)
