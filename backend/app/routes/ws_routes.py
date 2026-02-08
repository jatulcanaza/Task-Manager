from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# APIRouter:
#   - Permite registrar endpoints WebSocket de forma modular
# WebSocket:
#   - Representa una conexión WebSocket activa
# WebSocketDisconnect:
#   - Excepción que FastAPI lanza cuando el cliente se desconecta

from app.core.ws_manager import ws_manager
# ws_manager:
#   - Administrador central de conexiones WebSocket
#   - Maneja registro, broadcast y limpieza de conexiones


# -----------------------------------------------------------------------------
# ROUTER: WEBSOCKETS
# -----------------------------------------------------------------------------
# No se define prefix porque el path completo se define en el decorator
# tags=["ws"]:
#   - Agrupa endpoints WebSocket en la documentación
router = APIRouter(tags=["ws"])


# -----------------------------------------------------------------------------
# ENDPOINT WEBSOCKET: REPORTS
# -----------------------------------------------------------------------------
@router.websocket("/ws/reports")
async def ws_reports(ws: WebSocket):
    """
    Endpoint WebSocket para reportes en tiempo real.

    Responsabilidades:
    - Aceptar la conexión WebSocket.
    - Registrar el cliente en el WSManager.
    - Mantener viva la conexión.
    - Limpiar correctamente al desconectarse.
    """

    # -------------------------------------------------------------------------
    # 1) REGISTRAR CONEXIÓN
    # -------------------------------------------------------------------------
    # ws_manager.connect:
    # - Acepta el handshake WebSocket
    # - Agrega el cliente al pool de conexiones activas
    await ws_manager.connect(ws)

    try:
        # ---------------------------------------------------------------------
        # 2) LOOP DE MANTENIMIENTO (KEEP-ALIVE)
        # ---------------------------------------------------------------------
        # Mientras el cliente esté conectado:
        # - Se espera recibir mensajes de texto
        # - No se procesan (solo mantiene la conexión viva)
        #
        # Esto evita timeouts en proxies / navegadores
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        # ---------------------------------------------------------------------
        # 3) DESCONEXIÓN NORMAL
        # ---------------------------------------------------------------------
        # Esta excepción se lanza cuando:
        # - El cliente cierra la pestaña
        # - Se pierde la conexión
        #
        # No se hace nada aquí porque la limpieza va en finally
        pass

    finally:
        # ---------------------------------------------------------------------
        # 4) LIMPIEZA GARANTIZADA
        # ---------------------------------------------------------------------
        # Siempre se ejecuta:
        # - Elimina el WebSocket del pool
        # - Previene memory leaks
        await ws_manager.disconnect(ws)
