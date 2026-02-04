from sqlalchemy.orm import Session  # Sesión de SQLAlchemy para ejecutar operaciones contra la BD
from uuid import UUID  # Tipo UUID para ids de usuario y tarea
from typing import Optional, List  # Tipos para anotaciones de retorno
from app.models.postgres_models import Task  # Modelo ORM de Task (tabla en PostgreSQL)
from app.daos.interfaces.task_dao import ITaskDAO  # Interfaz que define el contrato del DAO de tareas

class PostgresTaskDAO(ITaskDAO):
    """
    Implementación concreta de ITaskDAO usando PostgreSQL (vía SQLAlchemy ORM).

    Responsabilidades:
    - CRUD de tareas (crear, listar, obtener, actualizar, eliminar)
    - Restringir accesos por owner_id (multitenant básico: cada usuario ve solo sus tareas)
    - Retornar representaciones simples (dict) en lugar de objetos ORM
    """

    def __init__(self, db: Session):
        # Guarda la sesión de BD inyectada (normalmente proviene de Depends(get_db))
        self.db = db

    def create(self, owner_id: UUID, data: dict) -> dict:
        """
        Crea una tarea nueva para el owner indicado.
        - Construye el objeto ORM Task usando owner_id + data (campos del request)
        - Persiste (add + commit)
        - refresh para obtener valores generados (id, defaults, etc.)
        - Retorna un dict con campos relevantes
        """
        t = Task(owner_id=owner_id, **data)  # Crea instancia ORM con los campos proporcionados
        self.db.add(t)                       # Marca para inserción
        self.db.commit()                     # Ejecuta INSERT en la BD
        self.db.refresh(t)                   # Recarga desde BD (por si se generó id/fechas/etc.)
        return {"id": t.id, "title": t.title, "description": t.description, "status": t.status}

    def list_by_owner(self, owner_id: UUID) -> List[dict]:
        """
        Lista todas las tareas del owner, ordenadas por fecha de creación (más nuevas primero).
        - query(Task) obtiene la tabla/modelo
        - filter limita por owner_id
        - order_by(created_at.desc()) ordena descendente por fecha de creación
        - all() ejecuta y devuelve todas las filas
        - Mapea cada fila ORM a dict
        """
        rows = self.db.query(Task).filter(Task.owner_id == owner_id).order_by(Task.created_at.desc()).all()
        return [{"id": r.id, "title": r.title, "description": r.description, "status": r.status} for r in rows]

    def get(self, owner_id: UUID, task_id: UUID) -> Optional[dict]:
        """
        Obtiene una tarea específica por id, asegurando que pertenezca al owner.
        - first() devuelve la primera coincidencia o None si no existe
        Retorna:
        - dict si se encuentra
        - None si no existe o no pertenece al owner
        """
        r = self.db.query(Task).filter(Task.owner_id == owner_id, Task.id == task_id).first()
        if not r:
            return None
        return {"id": r.id, "title": r.title, "description": r.description, "status": r.status}

    def update(self, owner_id: UUID, task_id: UUID, data: dict) -> Optional[dict]:
        """
        Actualiza una tarea existente (si pertenece al owner).
        - Busca la tarea por owner_id + task_id
        - Si no existe, retorna None
        - Aplica los cambios dinámicamente con setattr por cada key/value en data
        - commit para persistir UPDATE
        - refresh para reflejar valores finales
        - Retorna dict con campos relevantes
        """
        r = self.db.query(Task).filter(Task.owner_id == owner_id, Task.id == task_id).first()
        if not r:
            return None
        for k, v in data.items():
            setattr(r, k, v)  # Actualiza cada campo recibido (p. ej., title, description, status, etc.)
        self.db.commit()      # Ejecuta UPDATE en la BD
        self.db.refresh(r)    # Refresca el objeto ORM desde BD
        return {"id": r.id, "title": r.title, "description": r.description, "status": r.status}

    def delete(self, owner_id: UUID, task_id: UUID) -> bool:
        """
        Elimina una tarea si existe y pertenece al owner.
        - Busca la tarea por owner_id + task_id
        - Si no existe, retorna False
        - delete + commit para ejecutar DELETE en la BD
        - Retorna True si se eliminó
        """
        r = self.db.query(Task).filter(Task.owner_id == owner_id, Task.id == task_id).first()
        if not r:
            return False
        self.db.delete(r)   # Marca la fila para eliminación
        self.db.commit()    # Ejecuta DELETE en la BD
        return True
