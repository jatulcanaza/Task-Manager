from abc import ABC, abstractmethod  # ABC para clases abstractas; abstractmethod para obligar implementación en subclases
from uuid import UUID  # Tipo UUID para identificar entidades (tareas/usuarios)
from typing import Optional, Dict, List  # Tipos para anotaciones (mejor legibilidad y validación estática)

class ILogDAO(ABC):
    """
    Interfaz (contrato) para un DAO (Data Access Object) de logs.

    La idea es desacoplar la lógica de negocio del almacenamiento:
    - Cualquier implementación concreta (PostgreSQL, MongoDB, archivo, etc.)
      debe implementar estos métodos con la misma firma.
    """

    @abstractmethod
    def write(self, task_id: UUID, owner_id: UUID, action: str, detail: Dict) -> None: ...
        # Registra un log asociado a una tarea y a un propietario (owner).
        # - task_id: identificador de la tarea
        # - owner_id: identificador del usuario/propietario que ejecuta la acción
        # - action: nombre/clave de la acción realizada (ej. "CREATED", "UPDATED", etc.)
        # - detail: diccionario con información adicional relevante (payload del evento)
        # No retorna nada; su objetivo es persistir el log.

    @abstractmethod
    def last_log_for_task(self, task_id: UUID) -> Optional[dict]: ...
        # Devuelve el último log registrado para una tarea específica.
        # Retorna:
        # - dict con el log si existe
        # - None si no hay logs para esa tarea

    @abstractmethod
    def last_logs_for_tasks(self, task_ids: List[UUID]) -> Dict[str, dict]: ...
        # Devuelve el último log para cada task_id de una lista.
        # Retorna un diccionario indexado por algún identificador (normalmente el task_id en string)
        # con el log correspondiente como dict.
        # Útil para consultas en lote evitando N llamadas individuales.
