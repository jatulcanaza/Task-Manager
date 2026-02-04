from uuid import UUID  # Tipo UUID para identificar al owner/usuario y tareas
from app.factories.postgres_factory import PostgresFactory  # Factory para obtener DAOs basados en PostgreSQL (tareas)
from app.factories.mongo_factory import MongoFactory  # Factory para obtener DAOs basados en MongoDB (logs)

class ReportService:
    """
    Servicio de reportes.
    Combina datos de dos fuentes:
    - PostgreSQL: tareas (estado actual, título, etc.)
    - MongoDB: logs (última acción y timestamp)

    Este servicio arma una vista "enriquecida" de las tareas incluyendo su último cambio.
    """

    def __init__(self, pg_factory: PostgresFactory, mongo_factory: MongoFactory):
        # DAO de tareas (PostgreSQL)
        self.tasks = pg_factory.task_dao()

        # DAO de logs (MongoDB)
        self.logs = mongo_factory.log_dao()

    def tasks_with_last_change(self, owner_id: UUID):
        """
        Retorna una lista de tareas del owner con información del último cambio (si existe).
        Flujo:
        1) Obtiene todas las tareas del usuario desde Postgres
        2) Extrae sus ids para consultar logs en batch en Mongo
        3) Obtiene el último log por tarea (en una sola agregación)
        4) Construye la salida combinando:
           - datos de tarea (id, title, status)
           - datos de log (last_action, last_action_at)
        """
        tasks = self.tasks.list_by_owner(owner_id)      # Lista tareas del usuario
        task_ids = [t["id"] for t in tasks]             # Extrae ids para consulta batch de logs
        last_logs = self.logs.last_logs_for_tasks(task_ids)  # Mapa: {task_id_str: last_log_doc}

        out = []  # Lista final de resultados
        for t in tasks:
            # last_logs usa keys como string (porque en Mongo task_id se guarda como str)
            log = last_logs.get(str(t["id"]))

            # Arma el dict de salida por cada tarea
            out.append({
                "task_id": t["id"],                                  # id de la tarea (UUID)
                "title": t["title"],                                 # título actual
                "status": t["status"],                               # estado actual
                "last_action": (log.get("action") if log else None),  # última acción registrada (si hay log)
                "last_action_at": (log.get("timestamp") if log else None),  # timestamp del último log (si hay)
            })
        return out  # Devuelve lista de tareas enriquecidas con su último cambio
