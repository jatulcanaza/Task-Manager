from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import db_session, get_current_user_id
from app.db.mongo import get_mongo_db
from app.factories.postgres_factory import PostgresFactory
from app.factories.mongo_factory import MongoFactory
from app.dtos.task_dto import TaskCreateDTO, TaskUpdateDTO, TaskOutDTO
from app.services.task_service import TaskService
from app.core.event_publisher import publisher  # ✅ IMPORTANTE

router = APIRouter(prefix="/tasks", tags=["tasks"])

def service(db: Session):
    return TaskService(PostgresFactory(db), MongoFactory(get_mongo_db()))

@router.get("", response_model=list[TaskOutDTO])
def list_tasks(
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id)
):
    return service(db).list(user_id)

# ✅ POST correcto: /tasks   (no /tasks/tasks)
@router.post("", response_model=TaskOutDTO)
def create_task(
    dto: TaskCreateDTO,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    task = service(db).create(user_id, dto.model_dump())

    background.add_task(
        publisher.publish,
        "task.created",
        {
            "type": "task.created",
            "task_id": str(task["id"]),
            "owner_id": str(user_id),
            "title": task.get("title"),
            "status": task.get("status"),
        }
    )

    return task

@router.put("/{task_id}", response_model=TaskOutDTO)
def update_task(
    task_id: UUID,
    dto: TaskUpdateDTO,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    data = {k: v for k, v in dto.model_dump().items() if v is not None}
    updated = service(db).update(user_id, task_id, data)

    background.add_task(
        publisher.publish,
        "task.updated",
        {
            "type": "task.updated",
            "task_id": str(task_id),
            "owner_id": str(user_id),
            "changes": data,
        }
    )

    return updated

@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    service(db).delete(user_id, task_id)

    background.add_task(
        publisher.publish,
        "task.deleted",
        {
            "type": "task.deleted",
            "task_id": str(task_id),
            "owner_id": str(user_id),
        }
    )

    return {"ok": True}
