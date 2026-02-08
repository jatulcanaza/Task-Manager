from fastapi import APIRouter, Depends, BackgroundTasks
# APIRouter:
#   - Agrupa endpoints relacionados (módulo "tasks")
# Depends:
#   - Inyección de dependencias (auth, db, etc.)
# BackgroundTasks:
#   - Permite ejecutar tareas después de devolver la respuesta HTTP
#   - Ideal para "side effects" como publicar eventos (no bloquear al usuario)

from sqlalchemy.orm import Session
# Session:
#   - Sesión SQLAlchemy para PostgreSQL

from uuid import UUID
# UUID:
#   - Tipo fuerte para IDs (task_id, user_id)

from app.core.dependencies import db_session, get_current_user_id
# db_session:
#   - Dependency que entrega una sesión de BD (PostgreSQL)
# get_current_user_id:
#   - Dependency que valida JWT y retorna el UUID del usuario autenticado

from app.db.mongo import get_mongo_db
# get_mongo_db:
#   - Función de compatibilidad que retorna Mongo A (task_logs)
#   - Se usa para registrar eventos/logs de tareas

from app.factories.postgres_factory import PostgresFactory
# PostgresFactory:
#   - Factory que construye/expone DAOs/repositorios de Postgres

from app.factories.mongo_factory import MongoFactory
# MongoFactory:
#   - Factory que construye DAOs de Mongo (ej. task_log_dao)

from app.dtos.task_dto import TaskCreateDTO, TaskUpdateDTO, TaskOutDTO
# DTOs:
# - TaskCreateDTO: body para crear tarea
# - TaskUpdateDTO: body para actualizar tarea (campos opcionales)
# - TaskOutDTO: estructura de respuesta (response_model)

from app.services.task_service import TaskService
# TaskService:
#   - Capa de servicio (lógica de negocio)
#   - Encapsula reglas y orquestación de Postgres/Mongo

from app.core.event_publisher import publisher  # ✅ IMPORTANTE
# publisher:
#   - Publicador de eventos a RabbitMQ (exchange "events", tipo TOPIC)
#   - Emite eventos: task.created, task.updated, task.deleted
#   - Consumidos por Bridge → MQTT → WS → dashboard realtime


# -----------------------------------------------------------------------------
# ROUTER: TASKS
# -----------------------------------------------------------------------------
# prefix="/tasks":
#   - Todos los endpoints quedan bajo /tasks
# tags=["tasks"]:
#   - Clasificación en Swagger/OpenAPI
router = APIRouter(prefix="/tasks", tags=["tasks"])


# -----------------------------------------------------------------------------
# FACTORY DE SERVICIO (HELPER)
# -----------------------------------------------------------------------------
def service(db: Session):
    """
    Construye el TaskService inyectando las factories necesarias.

    Patrón aplicado:
    - Controller (router) delgado
    - Lógica en Service Layer
    - Acceso a datos vía Factories/DAOs

    Mongo:
    - Se usa get_mongo_db() (compat) → Mongo A para logs de tareas
    """
    return TaskService(PostgresFactory(db), MongoFactory(get_mongo_db()))


# -----------------------------------------------------------------------------
# ENDPOINT: LISTAR TAREAS
# -----------------------------------------------------------------------------
@router.get("", response_model=list[TaskOutDTO])
def list_tasks(
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Retorna la lista de tareas del usuario autenticado.

    Seguridad:
    - Requiere JWT válido (get_current_user_id)
    - Filtra por owner_id (user_id)

    Persistencia:
    - Postgres (estado actual de tareas)
    """
    return service(db).list(user_id)


# -----------------------------------------------------------------------------
# ENDPOINT: CREAR TAREA
# -----------------------------------------------------------------------------
# ✅ POST correcto: /tasks (no /tasks/tasks)
@router.post("", response_model=TaskOutDTO)
def create_task(
    dto: TaskCreateDTO,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Crea una tarea en Postgres y publica un evento asíncrono.

    Flujo:
    1) Valida JWT → user_id
    2) Valida body con TaskCreateDTO
    3) service.create() persiste en Postgres
    4) Se programa (BackgroundTasks) la publicación de evento en RabbitMQ
    5) Devuelve la tarea creada al cliente (sin esperar el publish)
    """

    # 1) Crear tarea en base de datos (Postgres)
    # dto.model_dump() convierte DTO pydantic a dict
    task = service(db).create(user_id, dto.model_dump())

    # 2) Publicar evento en segundo plano (no bloquea la respuesta)
    background.add_task(
        publisher.publish,
        "task.created",  # routing_key de RabbitMQ
        {
            "type": "task.created",         # tipo lógico del evento
            "task_id": str(task["id"]),     # id de tarea (UUID → string)
            "owner_id": str(user_id),       # dueño/creador
            "title": task.get("title"),     # datos útiles para dashboard
            "status": task.get("status"),
        }
    )

    # 3) Respuesta HTTP inmediata (la publicación ocurre después)
    return task


# -----------------------------------------------------------------------------
# ENDPOINT: ACTUALIZAR TAREA
# -----------------------------------------------------------------------------
@router.put("/{task_id}", response_model=TaskOutDTO)
def update_task(
    task_id: UUID,
    dto: TaskUpdateDTO,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualiza una tarea y publica evento task.updated.

    Consideraciones:
    - task_id viene por path y se valida como UUID
    - dto tiene campos opcionales (parcial update estilo PATCH pero con PUT)
    - Se filtran None para no sobreescribir campos no enviados
    """

    # 1) Limpiar payload:
    #   - Solo incluimos campos que el usuario realmente envió (no None)
    data = {k: v for k, v in dto.model_dump().items() if v is not None}

    # 2) Actualizar en Postgres (validando ownership en el service)
    updated = service(db).update(user_id, task_id, data)

    # 3) Publicar evento asíncrono de actualización
    background.add_task(
        publisher.publish,
        "task.updated",
        {
            "type": "task.updated",
            "task_id": str(task_id),
            "owner_id": str(user_id),
            "changes": data,  # se envían solo los cambios aplicados
        }
    )

    return updated


# -----------------------------------------------------------------------------
# ENDPOINT: ELIMINAR TAREA
# -----------------------------------------------------------------------------
@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    background: BackgroundTasks,
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Elimina una tarea y publica evento task.deleted.

    Flujo:
    - Se elimina del estado actual (Postgres)
    - Se emite evento para:
        - auditoría
        - dashboard realtime
        - otros consumidores
    """

    # 1) Eliminar tarea (service aplica reglas de negocio / ownership)
    service(db).delete(user_id, task_id)

    # 2) Publicar evento asíncrono
    background.add_task(
        publisher.publish,
        "task.deleted",
        {
            "type": "task.deleted",
            "task_id": str(task_id),
            "owner_id": str(user_id),
        }
    )

    # 3) Respuesta estándar
    return {"ok": True}
