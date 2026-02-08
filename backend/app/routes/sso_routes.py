from fastapi import APIRouter, Depends
# APIRouter:
#   - Permite definir un conjunto de endpoints relacionados
# Depends:
#   - Sistema de inyección de dependencias de FastAPI

from uuid import UUID
# UUID:
#   - Identificador fuerte del usuario autenticado

from pydantic import BaseModel
# BaseModel:
#   - Define DTOs (Data Transfer Objects)
#   - Valida automáticamente el body de las requests y responses

from app.core.dependencies import get_current_user_id
# get_current_user_id:
#   - Dependency de autenticación
#   - Valida el JWT de acceso
#   - Retorna el UUID del usuario autenticado

from app.core.security import create_sso_token, decode_sso_token, create_access_token
# create_sso_token:
#   - Genera un token SSO de vida corta
# decode_sso_token:
#   - Valida y decodifica el token SSO
# create_access_token:
#   - Genera un JWT de acceso estándar


# -----------------------------------------------------------------------------
# ROUTER: SSO (SINGLE SIGN-ON)
# -----------------------------------------------------------------------------
# Prefijo /sso:
# - Endpoints relacionados con autenticación entre aplicaciones
# Tags:
# - Organización en Swagger / OpenAPI
router = APIRouter(prefix="/sso", tags=["sso"])


# -----------------------------------------------------------------------------
# DTOs
# -----------------------------------------------------------------------------
class SsoTokenOut(BaseModel):
    """
    DTO de salida para emisión de token SSO.
    """
    sso_token: str


class ConsumeIn(BaseModel):
    """
    DTO de entrada para consumir un token SSO.
    """
    sso_token: str


class TokenOut(BaseModel):
    """
    DTO de salida para JWT de acceso estándar.
    """
    access_token: str


# -----------------------------------------------------------------------------
# ENDPOINT: EMITIR TOKEN SSO
# -----------------------------------------------------------------------------
@router.post("/token", response_model=SsoTokenOut)
def issue_sso_token(
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Emite un token SSO de vida corta para el usuario autenticado.

    Seguridad:
    - Endpoint protegido con JWT de acceso
    - Solo usuarios autenticados pueden pedir un token SSO

    Uso típico:
    - Web A solicita token SSO
    - Redirecciona a Web B con el token
    """

    return {
        # Se genera un token SSO válido por 2 minutos
        "sso_token": create_sso_token(str(user_id), minutes=2)
    }


# -----------------------------------------------------------------------------
# ENDPOINT: CONSUMIR TOKEN SSO
# -----------------------------------------------------------------------------
@router.post("/consume", response_model=TokenOut)
def consume_sso(dto: ConsumeIn):
    """
    Consume un token SSO y devuelve un JWT de acceso normal.

    Flujo:
    1) Web B recibe token SSO.
    2) Se valida firma, expiración, issuer y audience.
    3) Se extrae el 'sub' (user_id).
    4) Se emite un access token estándar.
    """

    # -------------------------------------------------------------------------
    # 1) Validar y decodificar token SSO
    # -------------------------------------------------------------------------
    sub = decode_sso_token(dto.sso_token)

    # -------------------------------------------------------------------------
    # 2) Emitir JWT de acceso normal
    # -------------------------------------------------------------------------
    return {
        "access_token": create_access_token(sub)
    }
