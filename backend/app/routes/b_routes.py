from fastapi import APIRouter, Depends
# APIRouter:
#   - Permite modularizar endpoints en FastAPI
# Depends:
#   - Sistema de inyección de dependencias (auth, DB, etc.)

from uuid import UUID
# UUID:
#   - Tipo fuerte para identificar usuarios de forma segura

from pydantic import BaseModel
# BaseModel:
#   - Validación automática del body de la request
#   - Garantiza estructura y tipos correctos

from datetime import datetime
# datetime:
#   - Se usa para generar timestamps en formato UTC

from app.core.dependencies import get_current_user_id
# get_current_user_id:
#   - Dependency que valida JWT
#   - Extrae el user_id autenticado desde el token

from app.db.mongo import get_mongo_b_db
# get_mongo_b_db:
#   - Retorna la base Mongo B (logs de accesos)

from app.factories.mongo_factory import MongoFactory
# MongoFactory:
#   - Implementa el patrón Factory
#   - Entrega DAOs especializados (access_log_dao, etc.)

from app.core.ws_manager import ws_manager
# ws_manager:
#   - Manager central de WebSockets
#   - Permite emitir eventos en tiempo real al dashboard


# -----------------------------------------------------------------------------
# ROUTER: WEB B
# -----------------------------------------------------------------------------
# Prefijo /b:
# - Endpoints exclusivos de la aplicación Web B
# Tags:
# - Organización en documentación Swagger
router = APIRouter(prefix="/b", tags=["web-b"])


# -----------------------------------------------------------------------------
# DTO DE ENTRADA
# -----------------------------------------------------------------------------
class AccessIn(BaseModel):
    """
    DTO para registrar accesos.

    Campos:
    - access_type:
        Tipo de acceso al sistema:
        - "SSO_TOKEN"
        - "NORMAL_LOGIN"
    """
    access_type: str


# -----------------------------------------------------------------------------
# ENDPOINT: LOG DE ACCESO
# -----------------------------------------------------------------------------
@router.post("/log-access")
async def log_access(
    dto: AccessIn,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Registra un acceso del usuario autenticado y notifica en tiempo real.

    Flujo:
    1) Valida JWT → obtiene user_id.
    2) Inserta registro en Mongo B (auditoría).
    3) Construye evento de dominio (access.logged).
    4) Emite el evento por WebSocket (dashboard realtime).
    5) Retorna respuesta OK.
    """

    # -------------------------------------------------------------------------
    # 1) FACTORY → DAO
    # -------------------------------------------------------------------------
    # MongoFactory abstrae la creación de DAOs
    # Evita acoplar el endpoint a implementaciones concretas
    mf = MongoFactory(get_mongo_b_db())

    # Se registra el acceso en la colección access_logs
    mf.access_log_dao().write(
        owner_id=str(user_id),
        access_type=dto.access_type
    )

    # -------------------------------------------------------------------------
    # 2) EVENTO PARA WEBSOCKET
    # -------------------------------------------------------------------------
    # Evento liviano pensado para visualización en tiempo real
    payload = {
        "type": "access.logged",
        "owner_id": str(user_id),
        "access_type": dto.access_type,
        # ISO 8601 + Z indica UTC (estándar en sistemas distribuidos)
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # -------------------------------------------------------------------------
    # 3) BROADCAST WEBSOCKET
    # -------------------------------------------------------------------------
    # Se notifica inmediatamente a todos los clientes conectados
    # (ej. dashboard administrativo)
    await ws_manager.broadcast_json(payload)

    # -------------------------------------------------------------------------
    # 4) RESPUESTA HTTP
    # -------------------------------------------------------------------------
    return {"ok": True}
