import os
# os:
#   - Permite leer variables de entorno
#   - Se usa aquí para configurar CORS dinámicamente

import asyncio
# asyncio:
#   - Framework asíncrono de Python
#   - Se utiliza para obtener el event loop principal en startup

from fastapi import FastAPI
# FastAPI:
#   - Framework principal para construir la API del servicio B

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware:
#   - Middleware para controlar accesos Cross-Origin (CORS)
#   - Necesario cuando el frontend (dashboard) corre en otro puerto/dominio


from app.routes.report_routes import router as report_router
# report_router:
#   - Endpoints de reportes (lectura / analítica)
#   - Combina datos de Postgres y Mongo

from app.routes.ws_routes import router as ws_router
# ws_router:
#   - Endpoints WebSocket (/ws/*)
#   - Permiten comunicación en tiempo real con el frontend

from app.routes.b_routes import router as b_router
# b_router:
#   - Endpoints específicos de Web B
#   - Ej: log de accesos, eventos administrativos, etc.

from app.core.mqtt_listener import start_mqtt_listener
# start_mqtt_listener:
#   - Inicializa el listener MQTT
#   - Recibe eventos desde el Bridge
#   - Los retransmite vía WebSocket usando ws_manager


# -----------------------------------------------------------------------------
# FACTORY DE APLICACIÓN FASTAPI (SERVICE B)
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI del servicio B.

    Responsabilidades:
    - Configurar CORS para el dashboard
    - Registrar routers de reportes, WS y endpoints B
    - Iniciar el listener MQTT en startup
    """

    # -------------------------------------------------------------------------
    # 1) CREACIÓN DE LA APLICACIÓN
    # -------------------------------------------------------------------------
    app = FastAPI(
        title="Task Manager - B (Reports/WS)",
        version="1.0"
    )

    # -------------------------------------------------------------------------
    # 2) CONFIGURACIÓN DE CORS
    # -------------------------------------------------------------------------
    # Se leen los orígenes permitidos desde variable de entorno:
    #   CORS_ORIGINS="http://dashboard.example.com"
    raw = os.getenv("CORS_ORIGINS", "").strip()

    # Se parsea la lista de orígenes.
    # Si no está definida, se usan valores por defecto
    # pensados para el frontend de Web B (puerto 8081).
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ]

    # Registro del middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,      # Frontend permitido (dashboard)
        allow_credentials=True,     # Permite headers Authorization / cookies
        allow_methods=["*"],        # GET, POST, etc.
        allow_headers=["*"],        # Headers personalizados
    )

    # -------------------------------------------------------------------------
    # 3) REGISTRO DE ROUTERS
    # -------------------------------------------------------------------------
    # Reportes (solo lectura)
    app.include_router(report_router)

    # WebSockets (realtime)
    app.include_router(ws_router)

    # Endpoints propios de Web B (logs, accesos, etc.)
    app.include_router(b_router)

    # -------------------------------------------------------------------------
    # 4) EVENTO STARTUP
    # -------------------------------------------------------------------------
    @app.on_event("startup")
    async def _startup():
        """
        Hook de arranque del servicio B.

        Se inicializa:
        - Event loop principal
        - Listener MQTT
        - Integración MQTT → WebSocket
        """

        # Obtiene el event loop activo de FastAPI / Uvicorn
        loop = asyncio.get_running_loop()

        # Inicia el listener MQTT
        # - MQTT corre en un hilo propio
        # - Los mensajes se reenvían al loop asyncio vía run_coroutine_threadsafe
        start_mqtt_listener(loop)

        # Log informativo de arranque correcto
        print("[B] startup ok: MQTT listener + WS ready")

    return app


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DE LA APP
# -----------------------------------------------------------------------------
# Esta instancia es usada por el servidor ASGI (Uvicorn/Gunicorn)
# para levantar el microservicio B.
app = create_app()

