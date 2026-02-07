import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.postgres_models import Base
from app.db.postgres import engine

from app.routes.task_routes import router as task_router

# Si A publica eventos, deja tu consumer/publisher aquí si aplica
from app.core.bridge_consumer import start_bridge_consumer

def create_app() -> FastAPI:
    app = FastAPI(title="Task Manager - A (Tasks)", version="1.0")

    raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        "http://localhost", "http://127.0.0.1",
        "http://localhost:8080", "http://127.0.0.1:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)

    app.include_router(task_router)

    @app.on_event("startup")
    async def _startup():
        asyncio.create_task(start_bridge_consumer())

    return app

app = create_app()
