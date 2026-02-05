from fastapi import HTTPException
from uuid import UUID

from app.factories.postgres_factory import PostgresFactory
from app.factories.mongo_factory import MongoFactory


class TaskService:
    def __init__(self, pg_factory: PostgresFactory, mongo_factory: MongoFactory):
        self.tasks = pg_factory.task_dao()
        self.logs = mongo_factory.log_dao()

    def create(self, owner_id: UUID, data: dict):
        task = self.tasks.create(owner_id, data)

        detail = {**task, "id": str(task["id"])}

        self.logs.write(
            task_id=task["id"],
            owner_id=owner_id,
            action="CREATE",
            detail=detail
        )

        # ✅ NO publicar aquí (evita runtime error), se publica en BackgroundTasks del route
        return task

    def list(self, owner_id: UUID):
        return self.tasks.list_by_owner(owner_id)

    def update(self, owner_id: UUID, task_id: UUID, data: dict):
        updated = self.tasks.update(owner_id, task_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        self.logs.write(task_id=task_id, owner_id=owner_id, action="UPDATE", detail=data)
        # ✅ publish va en route
        return updated

    def delete(self, owner_id: UUID, task_id: UUID):
        ok = self.tasks.delete(owner_id, task_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        self.logs.write(task_id=task_id, owner_id=owner_id, action="DELETE", detail={})
        # ✅ publish va en route
        return True
