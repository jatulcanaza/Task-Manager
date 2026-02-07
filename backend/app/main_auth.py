import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_routes import router as auth_router
from app.routes.sso_routes import router as sso_router

def create_app() -> FastAPI:
    app = FastAPI(title="Task Manager - AUTH", version="1.0")

    raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        "http://localhost", "http://127.0.0.1",
        "http://localhost:8080", "http://localhost:8081",
        "http://127.0.0.1:8080", "http://127.0.0.1:8081",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(sso_router)
    return app

app = create_app()
