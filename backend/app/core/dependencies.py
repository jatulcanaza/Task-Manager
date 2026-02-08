from fastapi import Depends, HTTPException
# Depends:
#   - Sistema de inyección de dependencias de FastAPI
#   - Permite desacoplar lógica (auth, DB, config) de los endpoints
#
# HTTPException:
#   - Excepción estándar para devolver errores HTTP controlados (401, 403, 404, etc.)

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# HTTPBearer:
#   - Implementa el esquema de seguridad "Bearer"
#   - Extrae el header: Authorization: Bearer <token>
#
# HTTPAuthorizationCredentials:
#   - Objeto que contiene:
#       - scheme (Bearer)
#       - credentials (el token JWT en texto plano)

from sqlalchemy.orm import Session
# Session:
#   - Representa una sesión activa contra PostgreSQL usando SQLAlchemy
#   - Se usa para ejecutar queries y transacciones

from uuid import UUID
# UUID:
#   - Tipo fuerte para validar identificadores
#   - Evita usar strings arbitrarios como IDs de usuario

from app.db.postgres import get_db
# get_db:
#   - Dependency que crea y retorna una sesión de PostgreSQL
#   - Maneja apertura y cierre de conexión (yield pattern)

from app.core.security import decode_token
# decode_token:
#   - Función de seguridad que:
#       - Valida la firma del JWT
#       - Verifica expiración
#       - Retorna el "sub" (subject), que representa el ID del usuario


# -----------------------------------------------------------------------------
# ESQUEMA DE SEGURIDAD BEARER
# -----------------------------------------------------------------------------
# Esta instancia se reutiliza en todas las dependencias que necesiten JWT.
# FastAPI la usa para:
# - Leer el header Authorization
# - Retornar 403 si el header no existe o es inválido
bearer = HTTPBearer()


# -----------------------------------------------------------------------------
# DEPENDENCY: OBTENER ID DEL USUARIO AUTENTICADO
# -----------------------------------------------------------------------------
def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> UUID:
    """
    Dependency de autenticación (FastAPI):

    Responsabilidades:
    1) Extraer el token JWT desde el header Authorization (Bearer).
    2) Decodificar y validar el token.
    3) Obtener el 'sub' (subject) del JWT.
    4) Validar que el 'sub' sea un UUID válido.
    5) Retornar el UUID del usuario autenticado.

    Comportamiento ante errores:
    - Token ausente / inválido / expirado / corrupto
    - Subject mal formado
    → HTTP 401 (No autorizado)

    Uso típico:
        @router.get("/protected")
        def endpoint(user_id: UUID = Depends(get_current_user_id)):
            ...
    """

    # -------------------------------------------------------------------------
    # 1) Extraer el token JWT puro
    # -------------------------------------------------------------------------
    # creds.credentials contiene SOLO el token
    # Ejemplo header:
    #   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    token = creds.credentials

    try:
        # ---------------------------------------------------------------------
        # 2) Decodificar y validar el token
        # ---------------------------------------------------------------------
        # decode_token:
        # - Verifica firma
        # - Verifica expiración
        # - Retorna el 'sub'
        sub = decode_token(token)

        # ---------------------------------------------------------------------
        # 3) Validar que el subject sea un UUID
        # ---------------------------------------------------------------------
        # Si el sub no es un UUID válido, esta línea lanza excepción
        return UUID(sub)

    except Exception:
        # ---------------------------------------------------------------------
        # Cualquier fallo de seguridad termina aquí
        # ---------------------------------------------------------------------
        # IMPORTANTE:
        # - No se filtra información (no decimos si expiró o fue inválido)
        # - Respuesta genérica por seguridad
        raise HTTPException(status_code=401, detail="No autorizado")


# -----------------------------------------------------------------------------
# DEPENDENCY: SESIÓN DE BASE DE DATOS
# -----------------------------------------------------------------------------
def db_session(db: Session = Depends(get_db)) -> Session:
    """
    Dependency de conveniencia para base de datos:

    - Expone la sesión SQLAlchemy directamente.
    - get_db se encarga de:
        - Crear la sesión
        - Hacer commit/rollback
        - Cerrar conexión al finalizar la request

    Uso típico:
        def endpoint(
            db: Session = Depends(db_session),
            user_id: UUID = Depends(get_current_user_id)
        ):
            ...
    """
    return db
