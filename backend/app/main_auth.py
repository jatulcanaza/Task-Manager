import os
# os:
#   - Permite acceder a variables de entorno
#   - Se usa aquí para configurar CORS dinámicamente según el entorno

from fastapi import FastAPI
# FastAPI:
#   - Framework principal para construir la API de autenticación

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware:
#   - Middleware para controlar accesos Cross-Origin (CORS)
#   - Necesario cuando frontend(s) y backend están en dominios/puertos distintos


from app.routes.auth_routes import router as auth_router
# auth_router:
#   - Router que expone endpoints de autenticación tradicional
#   - Ej: login, signup, refresh, etc.

from app.routes.sso_routes import router as sso_router
# sso_router:
#   - Router que expone endpoints de Single Sign-On (SSO)
#   - Emisión y consumo de tokens SSO entre aplicaciones


# -----------------------------------------------------------------------------
# FACTORY DE APLICACIÓN FASTAPI (AUTH SERVICE)
# -----------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI del servicio AUTH.

    Responsabilidades:
    - Inicializar la app
    - Configurar CORS
    - Registrar routers de autenticación y SSO
    """

    # -------------------------------------------------------------------------
    # 1) CREACIÓN DE LA APLICACIÓN
    # -------------------------------------------------------------------------
    app = FastAPI(
        title="Task Manager - AUTH",
        version="1.0"
    )

    # -------------------------------------------------------------------------
    # 2) CONFIGURACIÓN DE CORS
    # -------------------------------------------------------------------------
    # Se leen los orígenes permitidos desde variable de entorno:
    #   CORS_ORIGINS="http://localhost:3000,http://example.com"
    raw = os.getenv("CORS_ORIGINS", "").strip()

    # Se parsea la lista separada por comas.
    # Si no existe la variable, se usan valores por defecto
    # pensados para desarrollo local (dos frontends distintos).
    origins = [o.strip() for o in raw.split(",") if o.strip()] or [
        "http://localhost", "http://127.0.0.1",
        "http://localhost:8080", "http://localhost:8081",
        "http://127.0.0.1:8080", "http://127.0.0.1:8081",
    ]

    # Registro del middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,      # Frontends permitidos
        allow_credentials=True,     # Permite Authorization headers / cookies
        allow_methods=["*"],        # GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],        # Headers personalizados
    )

    # -------------------------------------------------------------------------
    # 3) REGISTRO DE ROUTERS
    # -------------------------------------------------------------------------
    # Endpoints de autenticación tradicional
    app.include_router(auth_router)

    # Endpoints de Single Sign-On (SSO)
    app.include_router(sso_router)

    return app


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DE LA APP
# -----------------------------------------------------------------------------
# Esta instancia es utilizada por el servidor ASGI (Uvicorn/Gunicorn)
# para levantar el microservicio AUTH.
app = create_app()
