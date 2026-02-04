from sqlalchemy.orm import Session  # Sesión de SQLAlchemy para ejecutar operaciones contra la BD
from uuid import UUID  # Tipo UUID para el id del usuario
from typing import Optional  # Para indicar retornos que pueden ser None
from app.models.postgres_models import User  # Modelo ORM de User (tabla en PostgreSQL)
from app.daos.interfaces.user_dao import IUserDAO  # Interfaz/contrato que este DAO debe implementar

class PostgresUserDAO(IUserDAO):
    """
    Implementación concreta de IUserDAO usando PostgreSQL (vía SQLAlchemy ORM).

    Responsabilidades:
    - Crear usuarios (persistir email + password_hash)
    - Consultar usuarios por email
    - Retornar estructuras simples (dict/UUID) en lugar de exponer el objeto ORM
    """

    def __init__(self, db: Session):
        # Guarda la sesión de BD inyectada (normalmente proviene de Depends(get_db))
        self.db = db

    def create_user(self, email: str, password_hash: str) -> UUID:
        """
        Crea un usuario en la base de datos.
        - Recibe email y password_hash (nunca la contraseña en texto plano)
        - Inserta el usuario (add + commit)
        - refresh para traer campos generados (por ejemplo, id)
        - Retorna el UUID del usuario creado
        """
        u = User(email=email, password_hash=password_hash)  # Construye el objeto ORM con los datos del usuario
        self.db.add(u)                                     # Marca para inserción
        self.db.commit()                                   # Ejecuta INSERT
        self.db.refresh(u)                                 # Recarga desde BD (id/autogenerados)
        return u.id                                        # Devuelve el id del usuario

    def get_by_email(self, email: str) -> Optional[dict]:
        """
        Busca un usuario por email.
        - query(User) apunta al modelo/tabla User
        - filter(User.email == email) aplica la condición
        - first() retorna el primer match o None si no existe

        Retorna:
        - dict con datos del usuario si existe
        - None si no existe
        """
        u = self.db.query(User).filter(User.email == email).first()
        if not u:
            return None
        return {"id": u.id, "email": u.email, "password_hash": u.password_hash}  # Representación simple del usuario
