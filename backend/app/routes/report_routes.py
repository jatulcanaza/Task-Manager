from fastapi import APIRouter, Depends  # APIRouter para agrupar rutas; Depends para inyección de dependencias
from sqlalchemy.orm import Session  # Tipo de sesión SQLAlchemy
from uuid import UUID  # Tipo UUID para el id del usuario autenticado

from app.core.dependencies import db_session, get_current_user_id  # Dependencies: sesión BD y usuario actual desde JWT
from app.db.mongo import get_mongo_db  # Función para obtener la conexión/DB de Mongo
from app.factories.postgres_factory import PostgresFactory  # Factory de DAOs para PostgreSQL (users/tasks)
from app.factories.mongo_factory import MongoFactory  # Factory de DAOs para MongoDB (logs)
from app.dtos.report_dto import TaskWithLastChangeDTO  # DTO de salida para el reporte
from app.services.report_service import ReportService  # Servicio que arma el reporte combinando Postgres + Mongo

# Router dedicado a endpoints de reportes:
# - prefix="/reports" => todas las rutas quedan bajo /reports
# - tags=["reports"] => etiqueta para la documentación Swagger/OpenAPI
router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/tasks-with-last-change", response_model=list[TaskWithLastChangeDTO])
def tasks_with_last_change(db: Session = Depends(db_session), user_id: UUID = Depends(get_current_user_id)):
    """
    Endpoint de reporte: lista tareas del usuario incluyendo la última acción registrada (desde logs).
    - Inyecta:
      - db: sesión PostgreSQL (para leer tareas)
      - user_id: UUID del usuario autenticado (extraído del JWT)
    - Construye ReportService con:
      - PostgresFactory(db): acceso a DAOs de tareas/usuarios en PostgreSQL
      - MongoFactory(get_mongo_db()): acceso al DAO de logs en MongoDB
    - Retorna una lista de TaskWithLastChangeDTO
    """
    svc = ReportService(PostgresFactory(db), MongoFactory(get_mongo_db()))  # Servicio con ambas fuentes de datos
    return svc.tasks_with_last_change(user_id)  # Ejecuta el caso de uso del reporte para el usuario actual
