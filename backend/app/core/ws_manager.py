from typing import Set
from fastapi import WebSocket
import asyncio

class WSManager:
    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._clients.discard(ws)

    async def _snapshot_clients(self):
        async with self._lock:
            return list(self._clients)

    async def _drop_dead(self, dead):
        if not dead:
            return
        async with self._lock:
            for ws in dead:
                self._clients.discard(ws)

    async def broadcast_json(self, payload: dict):
        clients = await self._snapshot_clients()
        dead = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        await self._drop_dead(dead)

    async def broadcast_text(self, message: str):
        clients = await self._snapshot_clients()
        dead = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        await self._drop_dead(dead)

ws_manager = WSManager()
