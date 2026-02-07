from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import db_session, get_current_user_id
from app.db.mongo import get_mongo_a_db, get_mongo_b_db
from app.factories.postgres_factory import PostgresFactory
from app.factories.mongo_factory import MongoFactory
from app.dtos.report_dto import TaskWithLastChangeDTO
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/tasks-with-last-change", response_model=list[TaskWithLastChangeDTO])
def tasks_with_last_change(db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    svc = ReportService(PostgresFactory(db), MongoFactory(get_mongo_a_db()))
    return svc.tasks_with_last_change(user_id)

@router.get("/access-stats")
def access_stats():
    dao = MongoFactory(get_mongo_b_db()).access_log_dao()
    return dao.stats()
