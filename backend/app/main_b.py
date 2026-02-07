import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.report_routes import router as report_router
from app.routes.ws_routes import router as ws_router
from app.routes.b_routes import router as b_router

from app.core.mqtt_listener import start_mqtt_listener

def create_app() -> FastAPI:
    app = FastAPI(title="Task Manager - B (Reports/WS)", version="1.0")

    raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(report_router)
    app.include_router(ws_router)
    app.include_router(b_router)

    @app.on_event("startup")
    async def _startup():
        loop = asyncio.get_running_loop()
        start_mqtt_listener(loop)
        print("[B] startup ok: MQTT listener + WS ready")

    return app

app = create_app()
