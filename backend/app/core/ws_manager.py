from typing import Set
# Set:
#   - Estructura sin duplicados
#   - Ideal para almacenar conexiones WebSocket activas

from fastapi import WebSocket
# WebSocket:
#   - Representa una conexión WebSocket activa en FastAPI
#   - Permite enviar/recibir mensajes en tiempo real

import asyncio
# asyncio:
#   - Framework de concurrencia asíncrona
#   - Permite manejar múltiples conexiones sin bloquear


# -----------------------------------------------------------------------------
# WEBSOCKET MANAGER
# -----------------------------------------------------------------------------
# Esta clase centraliza:
# - Registro de clientes WebSocket
# - Envío de mensajes broadcast
# - Limpieza de conexiones caídas
#
# Es thread-safe a nivel asyncio gracias a asyncio.Lock
# -----------------------------------------------------------------------------
class WSManager:

    def __init__(self):
        # ---------------------------------------------------------------------
        # _clients:
        #   - Conjunto de conexiones WebSocket activas
        #   - Se usa set para evitar duplicados
        #
        # _lock:
        #   - Lock asíncrono para proteger accesos concurrentes
        #   - Previene race conditions al agregar/quitar clientes
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    # -------------------------------------------------------------------------
    # REGISTRAR NUEVO CLIENTE
    # -------------------------------------------------------------------------
    async def connect(self, ws: WebSocket):
        """
        Acepta una nueva conexión WebSocket y la registra.

        Flujo:
        1) ws.accept() completa el handshake WebSocket.
        2) Se adquiere el lock.
        3) Se agrega el cliente al conjunto activo.
        """

        # Completa el handshake WebSocket
        await ws.accept()

        # Acceso protegido a la colección de clientes
        async with self._lock:
            self._clients.add(ws)

    # -------------------------------------------------------------------------
    # DESCONECTAR CLIENTE
    # -------------------------------------------------------------------------
    async def disconnect(self, ws: WebSocket):
        """
        Elimina un cliente WebSocket del conjunto activo.

        Se usa discard() en lugar de remove() para:
        - Evitar excepciones si el cliente ya no existe
        """

        async with self._lock:
            self._clients.discard(ws)

    # -------------------------------------------------------------------------
    # SNAPSHOT DE CLIENTES
    # -------------------------------------------------------------------------
    async def _snapshot_clients(self):
        """
        Retorna una copia (snapshot) de los clientes conectados.

        Motivo:
        - Evita iterar directamente sobre el set compartido.
        - Permite enviar mensajes sin mantener el lock bloqueado.
        """

        async with self._lock:
            # Se retorna una lista inmutable para iteración segura
            return list(self._clients)

    # -------------------------------------------------------------------------
    # LIMPIEZA DE CONEXIONES MUERTAS
    # -------------------------------------------------------------------------
    async def _drop_dead(self, dead):
        """
        Elimina conexiones WebSocket que fallaron durante el envío.

        Parámetro:
        - dead:
            Lista de WebSockets que lanzaron excepción (desconectados).
        """

        if not dead:
            return

        async with self._lock:
            for ws in dead:
                self._clients.discard(ws)

    # -------------------------------------------------------------------------
    # BROADCAST JSON
    # -------------------------------------------------------------------------
    async def broadcast_json(self, payload: dict):
        """
        Envía un mensaje JSON a todos los clientes conectados.

        Estrategia:
        - Se toma un snapshot de clientes.
        - Se intenta enviar a cada uno.
        - Si falla, se marca como 'dead'.
        - Al final, se limpian las conexiones muertas.
        """

        clients = await self._snapshot_clients()
        dead = []

        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                # Si falla el envío, se considera conexión muerta
                dead.append(ws)

        # Limpieza posterior (fuera del loop principal)
        await self._drop_dead(dead)

    # -------------------------------------------------------------------------
    # BROADCAST TEXTO
    # -------------------------------------------------------------------------
    async def broadcast_text(self, message: str):
        """
        Envía un mensaje de texto plano a todos los clientes conectados.

        Similar a broadcast_json, pero usando send_text.
        """

        clients = await self._snapshot_clients()
        dead = []

        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        await self._drop_dead(dead)


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DEL WS MANAGER
# -----------------------------------------------------------------------------
# Se expone una única instancia compartida en toda la app.
#
# Uso típico:
#   await ws_manager.broadcast_json(data)
#   await ws_manager.connect(websocket)
#   await ws_manager.disconnect(websocket)
ws_manager = WSManager()
