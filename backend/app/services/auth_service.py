from fastapi import HTTPException  # Excepción HTTP para devolver errores controlados (status_code + detail)
from app.core.security import hash_password, verify_password, create_access_token  # Utilidades de seguridad (bcrypt + JWT)
from app.factories.postgres_factory import PostgresFactory  # Factory para obtener DAOs basados en PostgreSQL

class AuthService:
    """
    Servicio de autenticación.
    Encapsula la lógica de negocio para:
    - registro de usuarios
    - login (verificación de credenciales)
    - emisión de JWT (access token)

    Usa PostgreSQL como fuente de verdad de usuarios (via PostgresFactory).
    """

    def __init__(self, pg_factory: PostgresFactory):
        # Obtiene el DAO de usuarios desde la factory de PostgreSQL
        # (desacopla el servicio de la implementación concreta del DAO)
        self.users = pg_factory.user_dao()

    def register(self, email: str, password: str):
        """
        Registra un usuario nuevo y retorna un access token.
        Flujo:
        1) Verifica si ya existe un usuario con el email
        2) Hashea la contraseña (bcrypt)
        3) Crea el usuario en la BD
        4) Genera un JWT cuyo "sub" es el id del usuario
        """
        if self.users.get_by_email(email):
            # Conflicto: el recurso ya existe (email duplicado)
            raise HTTPException(status_code=409, detail="Email ya registrado")

        # Crea el usuario guardando solo el hash de la contraseña
        uid = self.users.create_user(email, hash_password(password))

        # Genera el token usando el id del usuario como subject (sub)
        token = create_access_token(str(uid))
        return token

    def login(self, email: str, password: str):
        """
        Autentica a un usuario y retorna un access token.
        Flujo:
        1) Busca usuario por email
        2) Verifica contraseña comparando contra password_hash (bcrypt)
        3) Si es válido, emite un JWT con el id del usuario en "sub"
        """
        u = self.users.get_by_email(email)

        # Si no existe usuario o la contraseña no coincide => 401
        if not u or not verify_password(password, u["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # Token con subject = id del usuario
        return create_access_token(str(u["id"]))
