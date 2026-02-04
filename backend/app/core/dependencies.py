from fastapi import Depends, HTTPException  # Depends para inyección de dependencias; HTTPException para errores HTTP
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # Seguridad HTTP Bearer (Authorization: Bearer <token>)
from sqlalchemy.orm import Session  # Tipo de sesión de SQLAlchemy para acceso a BD
from uuid import UUID  # Tipo UUID para validar/convertir identificadores

from app.db.postgres import get_db  # Dependency que entrega una sesión de PostgreSQL
from app.core.security import decode_token  # Función que decodifica/verifica el JWT y devuelve el "sub" (subject)

# Esquema de autenticación Bearer para extraer el token desde el header Authorization
bearer = HTTPBearer()

def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> UUID:
    """
    Dependency de FastAPI:
    - Obtiene el JWT del header Authorization (Bearer).
    - Decodifica el token para obtener el 'sub' (subject), que se espera sea un UUID.
    - Retorna el UUID del usuario autenticado.
    - Si algo falla, lanza 401 (No autorizado).
    """
    token = creds.credentials  # Token puro extraído de "Authorization: Bearer <token>"
    try:
        sub = decode_token(token)  # Decodifica/valida el token y retorna el subject (id del usuario)
        return UUID(sub)  # Convierte/valida que el 'sub' tenga formato UUID
    except Exception:
        # Cualquier error (token inválido, expirado, sub mal formado, etc.) => 401
        raise HTTPException(status_code=401, detail="No autorizado")

def db_session(db: Session = Depends(get_db)) -> Session:
    """
    Dependency de conveniencia:
    - Expone la sesión de BD (SQLAlchemy Session) para inyectarla en endpoints/servicios.
    - get_db normalmente maneja el ciclo de vida (crear/cerrar) de la sesión.
    """
    return db
