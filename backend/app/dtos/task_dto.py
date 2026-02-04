from pydantic import BaseModel, Field  # BaseModel para DTOs; Field para constraints/metadata de validación
from typing import Optional, Literal  # Optional para campos opcionales; Literal para restringir valores permitidos
from uuid import UUID  # Tipo UUID para el id de salida

# Alias de tipo para restringir el estado de una tarea a valores específicos
TaskStatus = Literal["PENDING", "IN_PROGRESS", "DONE"]

class TaskCreateDTO(BaseModel):
    """
    DTO para crear una tarea.
    - Define restricciones de validación con Field (longitudes, opcionalidad, defaults).
    - 'status' usa el tipo TaskStatus para permitir solo valores conocidos.
    """
    title: str = Field(min_length=3, max_length=80)                # Título obligatorio (3-80 caracteres)
    description: Optional[str] = Field(default=None, max_length=300) # Descripción opcional (máx 300)
    status: TaskStatus = "PENDING"                                 # Estado por defecto al crear

class TaskUpdateDTO(BaseModel):
    """
    DTO para actualizar una tarea (actualización parcial).
    - Todos los campos son opcionales para permitir PATCH-like updates.
    - Si un campo viene como None / no viene, la lógica de negocio decide si se ignora.
    """
    title: Optional[str] = Field(default=None, min_length=3, max_length=80)     # Título opcional con constraints
    description: Optional[str] = Field(default=None, max_length=300)            # Descripción opcional con constraints
    status: Optional[TaskStatus] = None                                         # Estado opcional (si viene, debe ser válido)

class TaskOutDTO(BaseModel):
    """
    DTO de salida (respuesta) para representar una tarea.
    - Normalmente se usa en respuestas de endpoints (create/get/list/update).
    """
    id: UUID                  # Identificador único de la tarea
    title: str                # Título de la tarea
    description: Optional[str]# Descripción (puede ser None)
    status: str               # Estado actual (string; podría tiparse como TaskStatus si quieres restringir también salida)
