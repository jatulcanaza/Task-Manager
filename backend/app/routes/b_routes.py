from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.core.dependencies import get_current_user_id
from app.db.mongo import get_mongo_b_db
from app.factories.mongo_factory import MongoFactory
from app.core.ws_manager import ws_manager  # ✅ importante

router = APIRouter(prefix="/b", tags=["web-b"])

class AccessIn(BaseModel):
    access_type: str  # "SSO_TOKEN" | "NORMAL_LOGIN"

@router.post("/log-access")
async def log_access(dto: AccessIn, user_id: UUID = Depends(get_current_user_id)):
    mf = MongoFactory(get_mongo_b_db())
    mf.access_log_dao().write(owner_id=str(user_id), access_type=dto.access_type)

    payload = {
        "type": "access.logged",
        "owner_id": str(user_id),
        "access_type": dto.access_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    await ws_manager.broadcast_json(payload)

    return {"ok": True}
