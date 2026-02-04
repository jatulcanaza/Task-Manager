from abc import ABC, abstractmethod  # ABC para definir clases abstractas; abstractmethod para métodos obligatorios
from app.daos.interfaces.user_dao import IUserDAO  # Contrato del DAO de usuarios
from app.daos.interfaces.task_dao import ITaskDAO  # Contrato del DAO de tareas
from app.daos.interfaces.log_dao import ILogDAO    # Contrato del DAO de logs

class AbstractDAOFactory(ABC):
    """
    Fábrica abstracta (Abstract Factory) para obtener DAOs.

    Propósito:
    - Centralizar la creación/provisión de DAOs (User/Task/Log)
    - Permitir cambiar la implementación concreta (Postgres, Mongo, mixto, etc.)
      sin cambiar el resto del código (solo se cambia la factory usada).
    """

    @abstractmethod
    def user_dao(self) -> IUserDAO: ...
        # Debe devolver una implementación concreta de IUserDAO
        # (por ejemplo: PostgresUserDAO, MongoUserDAO, etc.)

    @abstractmethod
    def task_dao(self) -> ITaskDAO: ...
        # Debe devolver una implementación concreta de ITaskDAO
        # (por ejemplo: PostgresTaskDAO, etc.)

    @abstractmethod
    def log_dao(self) -> ILogDAO: ...
        # Debe devolver una implementación concreta de ILogDAO
        # (por ejemplo: MongoLogDAO, PostgresLogDAO, etc.)
