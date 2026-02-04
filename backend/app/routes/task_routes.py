from fastapi import APIRouter, Depends  # APIRouter para agrupar rutas; Depends para inyección de dependencias
from sqlalchemy.orm import Session  # Tipo de sesión SQLAlchemy para Postgres
from uuid import UUID  # Tipo UUID para ids (usuario y tarea)

from app.core.dependencies import db_session, get_current_user_id  # Dependencies: sesión BD y usuario autenticado (JWT)
from app.db.mongo import get_mongo_db  # Acceso a la DB de Mongo (donde se guardan logs)
from app.factories.postgres_factory import PostgresFactory  # Factory de DAOs de PostgreSQL (tareas/usuarios)
from app.factories.mongo_factory import MongoFactory  # Factory de DAOs de MongoDB (logs)
from app.dtos.task_dto import TaskCreateDTO, TaskUpdateDTO, TaskOutDTO  # DTOs de entrada/salida para tareas
from app.services.task_service import TaskService  # Servicio con la lógica de negocio de tareas

# Router dedicado a endpoints de tareas:
# - prefix="/tasks" => todas las rutas quedan bajo /tasks
# - tags=["tasks"] => etiqueta para la documentación Swagger/OpenAPI
router = APIRouter(prefix="/tasks", tags=["tasks"])

def service(db: Session):
    """
    Helper/factory local para construir el TaskService con sus dependencias.
    - PostgresFactory(db): acceso a DAOs de tareas/usuarios en PostgreSQL
    - MongoFactory(get_mongo_db()): acceso al DAO de logs en MongoDB
    """
    return TaskService(PostgresFactory(db), MongoFactory(get_mongo_db()))

@router.get("", response_model=list[TaskOutDTO])
def list_tasks(db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    """
    Lista las tareas del usuario autenticado.
    - Inyecta sesión Postgres y user_id desde JWT.
    - Retorna lista de TaskOutDTO.
    """
    return service(db).list(user_id)

@router.post("", response_model=TaskOutDTO)
def create_task(dto: TaskCreateDTO, db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    """
    Crea una tarea nueva para el usuario autenticado.
    - Recibe TaskCreateDTO (validado por Pydantic)
    - Convierte el DTO a dict con model_dump()
    - Retorna la tarea creada como TaskOutDTO
    """
    return service(db).create(user_id, dto.model_dump())

@router.put("/{task_id}", response_model=TaskOutDTO)
def update_task(task_id: UUID, dto: TaskUpdateDTO, db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    """
    Actualiza una tarea existente (por id) del usuario autenticado.
    - task_id viene por path
    - dto contiene campos opcionales (update parcial)
    - Se filtran los None para no sobreescribir campos con null involuntariamente
    - Retorna la tarea actualizada como TaskOutDTO
    """
    data = {k: v for k, v in dto.model_dump().items() if v is not None}  # Solo campos enviados (no None)
    return service(db).update(user_id, task_id, data)

@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    """
    Elimina una tarea existente (por id) del usuario autenticado.
    - Llama al servicio para eliminar (y potencialmente registrar log)
    - Devuelve una respuesta simple de confirmación
    """
    service(db).delete(user_id, task_id)
    return {"ok": True}
