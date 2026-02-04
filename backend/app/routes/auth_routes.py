from fastapi import APIRouter, Depends  # APIRouter para agrupar rutas; Depends para inyección de dependencias
from sqlalchemy.orm import Session  # Tipo de sesión SQLAlchemy para la BD
from app.core.dependencies import db_session  # Dependency que entrega una Session (wrapper sobre get_db)
from app.factories.postgres_factory import PostgresFactory  # Factory para obtener DAOs basados en PostgreSQL
from app.dtos.auth_dto import RegisterDTO, LoginDTO, TokenDTO  # DTOs de entrada/salida para autenticación
from app.services.auth_service import AuthService  # Servicio con la lógica de negocio de auth (registro/login)

# Router dedicado a endpoints de autenticación:
# - prefix="/auth" => todas las rutas quedan bajo /auth
# - tags=["auth"] => etiqueta para la documentación Swagger/OpenAPI
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenDTO)
def register(dto: RegisterDTO, db: Session = Depends(db_session)):
    """
    Endpoint de registro.
    - Recibe un RegisterDTO (valida email/password con Pydantic)
    - Inyecta una sesión de BD (db) vía Depends(db_session)
    - Crea el servicio de auth usando PostgresFactory (DAOs de Postgres)
    - Registra el usuario y retorna un TokenDTO con el access_token
    """
    svc = AuthService(PostgresFactory(db))       # Servicio configurado con DAOs de PostgreSQL
    token = svc.register(dto.email, dto.password) # Ejecuta registro y genera token
    return TokenDTO(access_token=token)           # Respuesta tipada (token_type por defecto "bearer")

@router.post("/login", response_model=TokenDTO)
def login(dto: LoginDTO, db: Session = Depends(db_session)):
    """
    Endpoint de login.
    - Recibe un LoginDTO (valida email con Pydantic)
    - Inyecta sesión de BD vía Depends(db_session)
    - Usa AuthService con PostgresFactory
    - Verifica credenciales y retorna un TokenDTO con el access_token
    """
    svc = AuthService(PostgresFactory(db))     # Servicio configurado con DAOs de PostgreSQL
    token = svc.login(dto.email, dto.password) # Ejecuta login y genera token si es válido
    return TokenDTO(access_token=token)        # Respuesta tipada
