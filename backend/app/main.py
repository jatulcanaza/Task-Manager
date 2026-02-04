from fastapi import FastAPI  # Clase principal para crear la aplicación FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Middleware para habilitar/gestionar CORS

from app.core.config import settings  # Configuración (incluye CORS_ORIGINS, URLs de BD, etc.)
from app.models.postgres_models import Base  # Metadata base de SQLAlchemy (contiene definición de tablas/modelos)
from app.db.postgres import engine  # Engine de SQLAlchemy configurado para PostgreSQL

from app.routes.auth_routes import router as auth_router  # Rutas de autenticación (registro/login)
from app.routes.task_routes import router as task_router  # Rutas de tareas (CRUD)
from app.routes.report_routes import router as report_router  # Rutas de reportes (consultas combinadas)

def create_app() -> FastAPI:
    """
    Crea y configura la instancia de FastAPI.
    Responsabilidades:
    - Inicializar la app (título/versión)
    - Configurar CORS según settings
    - Crear tablas en PostgreSQL (en arranque, para proyecto simple/académico)
    - Registrar routers (auth, tasks, reports)
    """
    app = FastAPI(title="Task Manager - Arquitectura", version="1.0")  # Instancia principal de la API

    # Lee CORS_ORIGINS desde settings (string) y lo convierte a lista separada por comas
    # Ej: "http://localhost:8080,https://mi-frontend.com" -> ["http://localhost:8080", "https://mi-frontend.com"]
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

    # Agrega middleware CORS para permitir solicitudes desde los orígenes permitidos
    # allow_methods=["*"] y allow_headers=["*"] habilitan todos los métodos/headers (útil en dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,        # Lista de orígenes permitidos
        allow_credentials=True,       # Permite envío de cookies/credenciales (si aplica)
        allow_methods=["*"],          # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],          # Permite todos los headers
    )

    # Crea tablas al iniciar (simple para proyecto académico)
    # Base.metadata reúne todas las tablas definidas en los modelos ORM importados
    # create_all crea las tablas si no existen (no hace migraciones avanzadas)
    Base.metadata.create_all(bind=engine)

    # Registra los routers/endpoints en la app
    app.include_router(auth_router)    # /auth/...
    app.include_router(task_router)    # /tasks/...
    app.include_router(report_router)  # /reports/...

    return app  # Devuelve la app ya configurada

# Instancia la aplicación al importar el módulo (útil para Uvicorn/Gunicorn: "module:app")
app = create_app()
