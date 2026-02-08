from fastapi import APIRouter, Depends
# APIRouter:
#   - Permite agrupar endpoints relacionados
# Depends:
#   - Sistema de inyección de dependencias de FastAPI

from sqlalchemy.orm import Session
# Session:
#   - Sesión activa de SQLAlchemy
#   - Permite interactuar con PostgreSQL

from uuid import UUID
# UUID:
#   - Identificador fuerte del usuario autenticado

from app.core.dependencies import db_session, get_current_user_id
# db_session:
#   - Dependency que expone una sesión de PostgreSQL
# get_current_user_id:
#   - Dependency de autenticación basada en JWT
#   - Retorna el UUID del usuario autenticado

from app.db.mongo import get_mongo_a_db, get_mongo_b_db
# get_mongo_a_db:
#   - Mongo A: logs de tareas / eventos funcionales
# get_mongo_b_db:
#   - Mongo B: logs de accesos / seguridad

from app.factories.postgres_factory import PostgresFactory
# PostgresFactory:
#   - Factory que encapsula DAOs/repositorios de PostgreSQL

from app.factories.mongo_factory import MongoFactory
# MongoFactory:
#   - Factory que encapsula DAOs de MongoDB
#   - Permite desacoplar endpoints de la implementación real

from app.dtos.report_dto import TaskWithLastChangeDTO
# TaskWithLastChangeDTO:
#   - DTO de salida
#   - Define la estructura del reporte
#   - Usado como response_model para validación y documentación

from app.services.report_service import ReportService
# ReportService:
#   - Servicio de aplicación
#   - Contiene la lógica de negocio de los reportes
#   - Orquesta datos entre Postgres y Mongo


# -----------------------------------------------------------------------------
# ROUTER: REPORTES
# -----------------------------------------------------------------------------
# Prefijo /reports:
# - Endpoints orientados a lectura y análisis
# Tags:
# - Organización en Swagger / OpenAPI
router = APIRouter(prefix="/reports", tags=["reports"])


# -----------------------------------------------------------------------------
# REPORTE: TAREAS CON ÚLTIMO CAMBIO
# -----------------------------------------------------------------------------
@router.get(
    "/tasks-with-last-change",
    response_model=list[TaskWithLastChangeDTO]
)
def tasks_with_last_change(
    db: Session = Depends(db_session),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Retorna un reporte de tareas del usuario junto con su último cambio.

    Seguridad:
    - Endpoint protegido por JWT
    - El reporte se filtra por user_id

    Arquitectura:
    - PostgreSQL → datos principales de tareas
    - Mongo A     → logs de cambios / eventos
    """

    # -------------------------------------------------------------------------
    # CREACIÓN DEL SERVICIO DE REPORTE
    # -------------------------------------------------------------------------
    # Se inyectan las dependencias usando factories:
    # - PostgresFactory(db): acceso a datos relacionales
    # - MongoFactory(get_mongo_a_db()): acceso a logs de eventos
    svc = ReportService(
        PostgresFactory(db),
        MongoFactory(get_mongo_a_db())
    )

    # -------------------------------------------------------------------------
    # EJECUCIÓN DEL CASO DE USO
    # -------------------------------------------------------------------------
    # El servicio se encarga de:
    # - Consultar tareas en Postgres
    # - Consultar último evento en Mongo
    # - Combinar datos
    # - Retornar DTOs
    return svc.tasks_with_last_change(user_id)


# -----------------------------------------------------------------------------
# REPORTE: ESTADÍSTICAS DE ACCESOS
# -----------------------------------------------------------------------------
@router.get("/access-stats")
def access_stats():
    """
    Retorna estadísticas agregadas de accesos al sistema.

    Fuente de datos:
    - Mongo B (access_logs)

    Uso típico:
    - Dashboard administrativo
    - Auditoría de seguridad
    """

    # -------------------------------------------------------------------------
    # DAO DE ACCESOS
    # -------------------------------------------------------------------------
    # Se obtiene el DAO a través de la factory
    dao = MongoFactory(get_mongo_b_db()).access_log_dao()

    # -------------------------------------------------------------------------
    # EJECUCIÓN DE AGREGACIÓN
    # -------------------------------------------------------------------------
    # stats():
    # - Agrupa accesos por tipo (SSO_TOKEN / NORMAL_LOGIN)
    # - Retorna conteos
    return dao.stats()
