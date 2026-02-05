from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import db_session, get_current_user_id
from app.core.security import create_sso_token, decode_sso_token, create_access_token
from app.db.mongo import get_mongo_db
from app.factories.mongo_factory import MongoFactory

from pydantic import BaseModel

router = APIRouter(prefix="/sso", tags=["sso"])

class SsoTokenOut(BaseModel):
    sso_token: str

class ConsumeIn(BaseModel):
    sso_token: str

class TokenOut(BaseModel):
    access_token: str

@router.post("/token", response_model=SsoTokenOut)
def issue_sso_token(user_id: UUID = Depends(get_current_user_id)):
    # genera token corto para Web B
    return {"sso_token": create_sso_token(str(user_id), minutes=2)}

@router.post("/consume", response_model=TokenOut)
def consume_sso(dto: ConsumeIn):
    # valida token sso y emite token normal (60min)
    sub = decode_sso_token(dto.sso_token)

    # registra acceso SSO en Mongo
    mf = MongoFactory(get_mongo_db())
    mf.access_log_dao().write(owner_id=sub, access_type="SSO_TOKEN")

    # token normal para usar endpoints /tasks /reports con Bearer
    return {"access_token": create_access_token(sub)}

@router.post("/mark-normal")
def mark_normal_login(user_id: UUID = Depends(get_current_user_id)):
    mf = MongoFactory(get_mongo_db())
    mf.access_log_dao().write(owner_id=str(user_id), access_type="NORMAL_LOGIN")
    return {"ok": True}
