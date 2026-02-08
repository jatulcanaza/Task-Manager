from fastapi import HTTPException
# HTTPException:
#   - Permite lanzar errores HTTP controlados desde la capa de servicio
#   - Se propagan correctamente hasta el cliente vía FastAPI

from uuid import UUID
# UUID:
#   - Tipo fuerte para IDs de usuario y tareas

from app.factories.postgres_factory import PostgresFactory
# PostgresFactory:
#   - Factory que provee DAOs/repositorios de PostgreSQL
#   - Encapsula el acceso a datos relacionales

from app.factories.mongo_factory import MongoFactory
# MongoFactory:
#   - Factory que provee DAOs de MongoDB
#   - Usado para logs/eventos históricos de tareas


# -----------------------------------------------------------------------------
# SERVICE LAYER: TASK SERVICE
# -----------------------------------------------------------------------------
# Esta clase representa la capa de servicio (Application / Domain Service).
#
# Responsabilidades:
# - Orquestar operaciones de negocio sobre tareas
# - Coordinar Postgres (estado actual) y Mongo (historial)
# - Aplicar reglas y validaciones
#
# Importante:
# - NO expone detalles de persistencia a los routers
# - NO publica eventos externos (eso es responsabilidad del route)
# -----------------------------------------------------------------------------
class TaskService:

    def __init__(self, pg_factory: PostgresFactory, mongo_factory: MongoFactory):
        """
        Constructor del servicio.

        Parámetros:
        - pg_factory:
            Factory para acceso a PostgreSQL
        - mongo_factory:
            Factory para acceso a MongoDB (logs)
        """

        # DAO de tareas (Postgres)
        self.tasks = pg_factory.task_dao()

        # DAO de logs de tareas (Mongo)
        self.logs = mongo_factory.log_dao()

    # -------------------------------------------------------------------------
    # CREAR TAREA
    # -------------------------------------------------------------------------
    def create(self, owner_id: UUID, data: dict):
        """
        Crea una nueva tarea.

        Flujo:
        1) Inserta la tarea en PostgreSQL.
        2) Registra evento CREATE en MongoDB.
        3) Retorna la tarea creada.

        Nota de arquitectura:
        - NO se publica evento externo aquí.
        - El publish se hace en el router usando BackgroundTasks.
        """

        # 1) Crear tarea en Postgres
        task = self.tasks.create(owner_id, data)

        # 2) Preparar detalle para auditoría
        #    - Se convierte el id a string para JSON-friendly logs
        detail = {**task, "id": str(task["id"])}

        # 3) Registrar log en Mongo (histórico)
        self.logs.write(
            task_id=task["id"],
            owner_id=owner_id,
            action="CREATE",
            detail=detail
        )

        # ✅ NO publicar aquí (evita runtime error y acoplamiento)
        return task

    # -------------------------------------------------------------------------
    # LISTAR TAREAS
    # -------------------------------------------------------------------------
    def list(self, owner_id: UUID):
        """
        Retorna todas las tareas del usuario.

        Fuente:
        - PostgreSQL (estado actual)
        """
        return self.tasks.list_by_owner(owner_id)

    # -------------------------------------------------------------------------
    # ACTUALIZAR TAREA
    # -------------------------------------------------------------------------
    def update(self, owner_id: UUID, task_id: UUID, data: dict):
        """
        Actualiza una tarea existente.

        Flujo:
        1) Intenta actualizar la tarea en Postgres.
        2) Si no existe o no pertenece al usuario → 404.
        3) Registra evento UPDATE en Mongo.
        4) Retorna la tarea actualizada.
        """

        updated = self.tasks.update(owner_id, task_id, data)

        # Si no se actualizó nada, la tarea no existe o no es del usuario
        if not updated:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # Registrar cambio en Mongo (solo los campos modificados)
        self.logs.write(
            task_id=task_id,
            owner_id=owner_id,
            action="UPDATE",
            detail=data
        )

        # ✅ publish va en route (separación clara de responsabilidades)
        return updated

    # -------------------------------------------------------------------------
    # ELIMINAR TAREA
    # -------------------------------------------------------------------------
    def delete(self, owner_id: UUID, task_id: UUID):
        """
        Elimina una tarea.

        Flujo:
        1) Intenta eliminar la tarea en Postgres.
        2) Si no existe o no pertenece al usuario → 404.
        3) Registra evento DELETE en Mongo.
        """

        ok = self.tasks.delete(owner_id, task_id)

        if not ok:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # Registrar eliminación en Mongo
        self.logs.write(
            task_id=task_id,
            owner_id=owner_id,
            action="DELETE",
            detail={}
        )

        # ✅ publish va en route
        return True
