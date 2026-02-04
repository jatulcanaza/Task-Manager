from fastapi import HTTPException  # Excepción HTTP para devolver errores controlados (status_code + detail)
from uuid import UUID  # Tipo UUID para ids de usuario y tarea
from app.factories.postgres_factory import PostgresFactory  # Factory de DAOs para PostgreSQL (tareas)
from app.factories.mongo_factory import MongoFactory  # Factory de DAOs para MongoDB (logs)

class TaskService:
    """
    Servicio de tareas.
    Encapsula la lógica de negocio para operaciones CRUD de tareas y registra auditoría en logs.

    Fuentes de datos usadas:
    - PostgreSQL: persistencia principal de tareas (TaskDAO)
    - MongoDB: logs/auditoría de acciones sobre tareas (LogDAO)
    """

    def __init__(self, pg_factory: PostgresFactory, mongo_factory: MongoFactory):
        # DAO de tareas (PostgreSQL)
        self.tasks = pg_factory.task_dao()

        # DAO de logs (MongoDB)
        self.logs = mongo_factory.log_dao()

    def create(self, owner_id: UUID, data: dict):
        """
        Crea una tarea y registra un log de tipo "CREATE".
        Flujo:
        1) Crea la tarea en PostgreSQL
        2) Prepara el detail del log (incluyendo el id en string para compatibilidad/consistencia)
        3) Escribe el log en MongoDB
        4) Retorna la tarea creada
        """
        task = self.tasks.create(owner_id, data)  # Crea la tarea en Postgres (retorna dict con campos relevantes)

        # Detail del log:
        # - Se copia el dict completo de la tarea
        # - Se fuerza "id" a string (por si el consumidor/log requiere serialización simple)
        detail = {**task, "id": str(task["id"])}

        # Registra el evento CREATE en la colección de logs
        self.logs.write(task_id=task["id"], owner_id=owner_id, action="CREATE", detail=detail)

        return task


    def list(self, owner_id: UUID):
        """
        Lista todas las tareas del owner.
        (No escribe logs porque es una operación de lectura.)
        """
        return self.tasks.list_by_owner(owner_id)

    def update(self, owner_id: UUID, task_id: UUID, data: dict):
        """
        Actualiza una tarea y registra un log de tipo "UPDATE".
        - Si la tarea no existe o no pertenece al owner => 404
        - Si se actualiza, se registra en Mongo el detalle del update (data)
        """
        updated = self.tasks.update(owner_id, task_id, data)  # Intenta actualizar en Postgres
        if not updated:
            # No existe o no pertenece al owner
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # Registra el evento UPDATE con el detalle de campos modificados
        self.logs.write(task_id=task_id, owner_id=owner_id, action="UPDATE", detail=data)
        return updated

    def delete(self, owner_id: UUID, task_id: UUID):
        """
        Elimina una tarea y registra un log de tipo "DELETE".
        - Si no existe o no pertenece al owner => 404
        - Si se elimina, se registra en Mongo con detail vacío (no hay campos adicionales)
        """
        ok = self.tasks.delete(owner_id, task_id)  # Intenta eliminar en Postgres
        if not ok:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # Registra el evento DELETE (sin detalle adicional)
        self.logs.write(task_id=task_id, owner_id=owner_id, action="DELETE", detail={})
        return True
