from app.daos.interfaces.log_dao import ILogDAO  # Interfaz/contrato que esta implementación debe cumplir
from uuid import UUID  # Tipo UUID para ids de tareas/usuarios
from typing import Optional, Dict, List  # Tipos para anotaciones
from datetime import datetime  # Para timestamp en UTC


def _mongo_safe(obj):
    """
    Normaliza objetos para que sean serializables/compatibles con MongoDB.
    - Convierte UUID -> str
    - Recorre estructuras anidadas (dict/list) para convertir UUIDs internos también
    - Devuelve el objeto sin cambios si no requiere transformación
    """
    # Convierte UUID nativo a string (y recorre dict/list)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _mongo_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mongo_safe(x) for x in obj]
    return obj


class MongoLogDAO(ILogDAO):
    """
    Implementación de ILogDAO usando MongoDB.

    Almacena logs en la colección `task_logs` con un índice compuesto:
    - task_id ascendente
    - timestamp descendente
    Esto facilita obtener rápidamente el último log por tarea.
    """

    def __init__(self, mongo_db):
        # Acceso a la colección donde se guardan los logs de tareas
        self.col = mongo_db["task_logs"]

        # Índice para acelerar consultas del tipo:
        # - buscar por task_id
        # - ordenar por timestamp desc para obtener "el último"
        self.col.create_index([("task_id", 1), ("timestamp", -1)])

    def write(self, task_id: UUID, owner_id: UUID, action: str, detail: Dict) -> None:
        """
        Inserta un log de acción asociado a una tarea.
        - Guarda task_id/owner_id como string para consistencia en Mongo
        - detail se normaliza con _mongo_safe para evitar UUIDs no serializables
        - timestamp se guarda en UTC
        """
        doc = {
            "task_id": str(task_id),      # <- SIEMPRE string
            "owner_id": str(owner_id),    # <- SIEMPRE string
            "action": action,             # Acción realizada (ej. "CREATED", "UPDATED", etc.)
            "detail": _mongo_safe(detail),# Detalle adicional (puede venir con UUIDs anidados)
            "timestamp": datetime.utcnow()# Momento del evento en UTC
        }
        self.col.insert_one(doc)  # Inserta el documento en la colección

    def last_log_for_task(self, task_id: UUID) -> Optional[dict]:
        """
        Obtiene el último log para una tarea específica.
        - Filtra por task_id (guardado como string)
        - Ordena por timestamp desc y retorna el primero
        Retorna:
        - dict con el documento encontrado
        - None si no existe ningún log para esa tarea
        """
        return self.col.find_one({"task_id": str(task_id)}, sort=[("timestamp", -1)])

    def last_logs_for_tasks(self, task_ids: List[UUID]) -> Dict[str, dict]:
        """
        Obtiene el último log para cada tarea en una lista, en una sola consulta (batch).
        Usa un pipeline de agregación:
        1) $match: filtra solo task_id dentro de la lista
        2) $sort: ordena por timestamp desc (para que el más reciente quede primero)
        3) $group: agrupa por task_id y toma el primer documento ($first) de cada grupo
        Retorna un dict:
        - clave: task_id (string)
        - valor: documento de log (dict) correspondiente al último log de esa tarea
        """
        ids = [str(tid) for tid in task_ids]  # Mongo guarda task_id como string, se convierte la lista completa

        pipeline = [
            {"$match": {"task_id": {"$in": ids}}},                 # Filtra por las tareas solicitadas
            {"$sort": {"timestamp": -1}},                          # Ordena logs por más reciente primero
            {"$group": {"_id": "$task_id", "doc": {"$first": "$$ROOT"}}}  # Toma el primer doc por task_id
        ]

        out = {}  # Mapa final: {task_id_str: last_log_doc}
        for row in self.col.aggregate(pipeline):
            out[row["_id"]] = row["doc"]  # row["_id"] es el task_id; row["doc"] es el último log
        return out
