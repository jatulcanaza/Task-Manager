from sqlalchemy.orm import Session  # Tipo de sesión SQLAlchemy para trabajar con PostgreSQL
from app.factories.abstract_factory import AbstractDAOFactory  # Base abstracta de la fábrica de DAOs
from app.daos.postgres.user_dao_pg import PostgresUserDAO  # Implementación concreta del DAO de usuarios en Postgres
from app.daos.postgres.task_dao_pg import PostgresTaskDAO  # Implementación concreta del DAO de tareas en Postgres

class PostgresFactory(AbstractDAOFactory):
    """
    Fábrica concreta que provee DAOs relacionados a PostgreSQL.

    En este diseño, PostgreSQL se usa para:
    - usuarios (PostgresUserDAO)
    - tareas (PostgresTaskDAO)

    Y NO se usa para logs (eso se maneja en MongoDB).
    """

    def __init__(self, db: Session):
        # Guarda la sesión de BD (SQLAlchemy Session) inyectada
        self.db = db

    def user_dao(self):
        """
        Devuelve una instancia del DAO de usuarios basado en PostgreSQL.
        Reutiliza la misma sesión 'db' para operar dentro del mismo contexto/transacción.
        """
        return PostgresUserDAO(self.db)

    def task_dao(self):
        """
        Devuelve una instancia del DAO de tareas basado en PostgreSQL.
        Reutiliza la misma sesión 'db' para operar dentro del mismo contexto/transacción.
        """
        return PostgresTaskDAO(self.db)

    def log_dao(self):
        """
        Esta fábrica no soporta logs porque el sistema los maneja con MongoDB.
        """
        raise NotImplementedError("Logs se manejan en MongoDB")
