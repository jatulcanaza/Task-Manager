from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel

from app.core.dependencies import get_current_user_id
from app.core.security import create_sso_token, decode_sso_token, create_access_token

router = APIRouter(prefix="/sso", tags=["sso"])

class SsoTokenOut(BaseModel):
    sso_token: str

class ConsumeIn(BaseModel):
    sso_token: str

class TokenOut(BaseModel):
    access_token: str

@router.post("/token", response_model=SsoTokenOut)
def issue_sso_token(user_id: UUID = Depends(get_current_user_id)):
    return {"sso_token": create_sso_token(str(user_id), minutes=2)}

@router.post("/consume", response_model=TokenOut)
def consume_sso(dto: ConsumeIn):
    sub = decode_sso_token(dto.sso_token)
    return {"access_token": create_access_token(sub)}
