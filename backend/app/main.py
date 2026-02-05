import os
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.postgres_models import Base
from app.db.postgres import engine

from app.routes.auth_routes import router as auth_router
from app.routes.task_routes import router as task_router
from app.routes.report_routes import router as report_router
from app.routes.ws_routes import router as ws_router
from app.routes.sso_routes import router as sso_router

from app.core.bridge_consumer import start_bridge_consumer


def create_app() -> FastAPI:
    app = FastAPI(title="Task Manager - Arquitectura", version="1.0")

    # CORS
    raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()]

    # Si no configuras CORS_ORIGINS, en DEV habilitamos localhost para que no te bloquee el navegador.
    if not origins:
        origins = [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # DB init (ojo: en prod preferible migraciones, pero no lo toco)
    Base.metadata.create_all(bind=engine)

    # Routers REST
    app.include_router(auth_router)
    app.include_router(task_router)
    app.include_router(report_router)

    # Routers nuevos
    app.include_router(ws_router)
    app.include_router(sso_router)

    @app.on_event("startup")
    async def _startup():
        asyncio.create_task(start_bridge_consumer())

    return app


app = create_app()
