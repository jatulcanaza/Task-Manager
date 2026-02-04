from abc import ABC, abstractmethod  # ABC para definir interfaces; abstractmethod obliga a implementar métodos en subclases
from uuid import UUID  # Tipo UUID para el identificador único del usuario
from typing import Optional  # Para indicar retornos que pueden ser None

class IUserDAO(ABC):
    """
    Interfaz (contrato) para un DAO (Data Access Object) de usuarios.

    Define las operaciones mínimas esperadas para persistencia/consulta de usuarios,
    permitiendo implementar distintas fuentes de datos (Postgres, Mongo, etc.)
    sin acoplar la lógica de negocio a una tecnología específica.
    """

    @abstractmethod
    def create_user(self, email: str, password_hash: str) -> UUID: ...
        # Crea un usuario nuevo en la capa de persistencia.
        # - email: correo del usuario (normalmente único)
        # - password_hash: hash de la contraseña (nunca guardar el texto plano)
        # Retorna el UUID del usuario creado.

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[dict]: ...
        # Busca un usuario por su email.
        # Retorna:
        # - dict con los datos del usuario (según lo que exponga la implementación)
        # - None si no existe un usuario con ese email
