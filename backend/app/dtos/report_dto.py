from pydantic import BaseModel  # BaseModel para definir DTOs/Esquemas de datos con validación
from uuid import UUID  # Tipo UUID para el identificador de la tarea
from typing import Optional  # Para campos opcionales (pueden ser None)
from datetime import datetime  # Tipo datetime para representar fecha/hora del último cambio

class TaskWithLastChangeDTO(BaseModel):
    """
    DTO que representa una tarea junto con información del último cambio (log/acción más reciente).

    Útil para endpoints que listan tareas e incluyen metadata de auditoría:
    - Qué acción fue la última (last_action)
    - Cuándo ocurrió (last_action_at)
    """
    task_id: UUID                      # Identificador único de la tarea
    title: str                         # Título de la tarea
    status: str                        # Estado actual de la tarea
    last_action: Optional[str] = None  # Última acción registrada (ej. "CREATED", "UPDATED"), si existe
    last_action_at: Optional[datetime] = None  # Timestamp del último cambio, si existe
