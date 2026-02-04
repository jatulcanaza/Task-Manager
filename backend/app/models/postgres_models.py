from __future__ import annotations  # Permite usar anotaciones de tipos como strings (forward refs) y '|' sin problemas de orden

import uuid  # Para generar UUIDs por defecto (uuid.uuid4)
from datetime import datetime  # Tipo datetime para campos de fecha/hora

from sqlalchemy import String, ForeignKey, DateTime, func  # Tipos/constraints SQL y funciones (func.now)
from sqlalchemy.dialects.postgresql import UUID  # Tipo UUID específico de PostgreSQL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship  # Base declarativa y mapeo ORM tipado


class Base(DeclarativeBase):
    """
    Clase base declarativa para modelos SQLAlchemy.
    Todas las entidades ORM heredan de aquí.
    """
    pass


class User(Base):
    """
    Modelo ORM para la tabla 'users'.
    Representa a un usuario del sistema.
    """
    __tablename__ = "users"  # Nombre de la tabla en la BD

    # Clave primaria UUID (as_uuid=True hace que Python use uuid.UUID en lugar de str)
    # default=uuid.uuid4 genera un UUID automáticamente al crear el registro
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email único, indexado para búsquedas rápidas, no nulo
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)

    # Hash de contraseña (nunca almacenar password en texto plano)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Fecha de creación con timezone; server_default=func.now() lo setea en la BD al insertar
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relación 1:N con Task (un usuario tiene muchas tareas)
    # - back_populates enlaza con Task.owner
    # - cascade="all, delete-orphan" elimina tareas asociadas si se elimina el usuario
    #   y también elimina "huérfanas" si se desvinculan de la relación
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class Task(Base):
    """
    Modelo ORM para la tabla 'tasks'.
    Representa una tarea perteneciente a un usuario.
    """
    __tablename__ = "tasks"  # Nombre de la tabla en la BD

    # Clave primaria UUID autogenerada
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK al usuario dueño de la tarea:
    # - ForeignKey("users.id") crea la relación a la tabla users
    # - index=True mejora consultas por owner_id
    # - nullable=False obliga a que toda tarea tenga un dueño
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )

    # Campos propios de la tarea
    title: Mapped[str] = mapped_column(String(80), nullable=False)                 # Título obligatorio
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)   # Descripción opcional
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # Estado por defecto

    # Fecha de creación (seteada por la BD al insertar)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Fecha de actualización:
    # - server_default=func.now() la inicializa al crear
    # - onupdate=func.now() hace que la BD la actualice automáticamente en cada UPDATE
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relación N:1 hacia User (muchas tareas pertenecen a un usuario)
    # back_populates enlaza con User.tasks
    owner: Mapped["User"] = relationship("User", back_populates="tasks")
