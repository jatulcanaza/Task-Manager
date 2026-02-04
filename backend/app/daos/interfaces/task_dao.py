from abc import ABC, abstractmethod  # ABC para definir interfaces; abstractmethod fuerza implementación en subclases
from uuid import UUID  # Tipo UUID para identificar usuarios y tareas
from typing import Optional, List  # Tipos para anotaciones de retorno/parametros

class ITaskDAO(ABC):
    """
    Interfaz (contrato) para un DAO (Data Access Object) de tareas.

    Objetivo:
    - Estandarizar cómo se crean/leen/actualizan/eliminan tareas (CRUD)
    - Permitir distintas implementaciones de persistencia (Postgres, Mongo, etc.)
      sin cambiar la lógica de negocio.
    """

    @abstractmethod
    def create(self, owner_id: UUID, data: dict) -> dict: ...
        # Crea una nueva tarea asociada a un owner (usuario).
        # - owner_id: identificador del usuario dueño de la tarea
        # - data: diccionario con los campos necesarios para crear la tarea
        # Retorna la tarea creada (como dict), normalmente incluyendo su id generado.

    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[dict]: ...
        # Lista todas las tareas pertenecientes a un usuario (owner).
        # Retorna una lista de dicts, cada uno representando una tarea.

    @abstractmethod
    def get(self, owner_id: UUID, task_id: UUID) -> Optional[dict]: ...
        # Obtiene una tarea por id, validando que pertenezca al owner indicado.
        # Retorna:
        # - dict con la tarea si existe y pertenece al owner
        # - None si no existe o no corresponde a ese owner

    @abstractmethod
    def update(self, owner_id: UUID, task_id: UUID, data: dict) -> Optional[dict]: ...
        # Actualiza una tarea por id, validando pertenencia por owner.
        # - data: campos a actualizar (parcial o completo según la implementación)
        # Retorna:
        # - dict con la tarea actualizada si se pudo actualizar
        # - None si no existe o no pertenece al owner

    @abstractmethod
    def delete(self, owner_id: UUID, task_id: UUID) -> bool: ...
        # Elimina una tarea por id, validando pertenencia por owner.
        # Retorna True si se eliminó, False si no existía/no pertenecía/no se pudo eliminar.
