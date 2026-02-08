import os
# os:
#   - Permite leer variables de entorno
#   - Se usa aquí para configurar CORS de forma dinámica

import asyncio
# asyncio:
#   - Framework asíncrono de Python
#   - Se utiliza para lanzar tareas en segundo plano al iniciar la app

from fastapi import FastAPI
# FastAPI:
#   - Framework principal para construir la API

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware:
#   - Middleware para controlar accesos cross-origin (CORS)
#   - Necesario cuando el frontend corre en otro dominio/puerto


from app.models.postgres_models import Base
# Base:
#   - Base declarativa de SQLAlchemy
#   - Contiene todos los modelos ORM de PostgreSQL

from app.db.postgres import engine
# engine:
#   - Engine de SQLAlchemy
#   - Maneja la conexión a PostgreSQL


from app.routes.task_routes import router as task_router
# task_router:
#   - Router que expone el CRUD de tareas (/tasks)
#   - Contiene endpoints protegidos con JWT


# Si A publica eventos, deja tu consumer/publisher aquí si aplica
from app.core.bridge_consumer import start_bridge_consumer
# start_bridge_consumer:
#   - Consumer asíncrono de RabbitMQ
#   - Escucha eventos task.* y los puentea a MQTT + email
#   - Se ejecuta como tarea en segundo plano


# -----------------------------------------------------------------------------
# FACTORY DE APLICACIÓN FASTAPI
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Responsabilidades:
    - Configurar CORS
    - Inicializar base de datos
    - Registrar routers
    - Lanzar procesos asíncronos de background en startup
    """

    # -------------------------------------------------------------------------
    # 1) CREACIÓN DE LA APP
    # -------------------------------------------------------------------------
    app = FastAPI(
        title="Task Manager - A (Tasks)",
        version="1.0"
    )

    # -------------------------------------------------------------------------
    # 2) CONFIGURACIÓN DE CORS
    # -------------------------------------------------------------------------
    # Se leen los orígenes permitidos desde variable de entorno:
    #   CORS_ORIGINS="http://localhost:3000,http://example.com"
    raw = os.getenv("CORS_ORIGINS", "").strip()

    # Se parsea la lista separada por comas
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        # Fallback seguro para desarrollo local
        "http://localhost", "http://127.0.0.1",
        "http://localhost:8080", "http://127.0.0.1:8080",
    ]

    # Se registra el middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,      # Orígenes permitidos
        allow_credentials=True,     # Cookies / Authorization headers
        allow_methods=["*"],        # GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],        # Headers personalizados
    )

    # -------------------------------------------------------------------------
    # 3) INICIALIZACIÓN DE BASE DE DATOS
    # -------------------------------------------------------------------------
    # Crea las tablas en PostgreSQL si no existen.
    #
    # Nota:
    # - Útil en entornos de desarrollo/demo
    # - En producción suele manejarse con migraciones (Alembic)
    Base.metadata.create_all(bind=engine)

    # -------------------------------------------------------------------------
    # 4) REGISTRO DE ROUTERS
    # -------------------------------------------------------------------------
    # Se monta el router de tareas (/tasks)
    app.include_router(task_router)

    # -------------------------------------------------------------------------
    # 5) EVENTO STARTUP
    # -------------------------------------------------------------------------
    @app.on_event("startup")
    async def _startup():
        """
        Hook de arranque de la aplicación.

        Se lanza el bridge consumer como tarea asíncrona:
        - No bloquea el arranque de la API
        - Permite que la app atienda requests mientras consume eventos
        """

        # asyncio.create_task:
        # - Ejecuta start_bridge_consumer() en background
        # - El consumer vive mientras la app esté levantada
        asyncio.create_task(start_bridge_consumer())

    return app


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DE LA APP
# -----------------------------------------------------------------------------
# Esta es la instancia que usa Uvicorn/Gunicorn para levantar el servicio
app = create_app()
