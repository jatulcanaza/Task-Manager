from pymongo import MongoClient
# MongoClient:
#   - Cliente oficial de MongoDB para Python
#   - Maneja el pool de conexiones internamente

from app.core.config import settings
# settings:
#   - Contiene las URLs de conexión y nombres de base de datos
#   - Centraliza configuración (mongo_a_url, mongo_b_url, etc.)


# -----------------------------------------------------------------------------
# CLIENTES MONGO (SINGLETON POR PROCESO)
# -----------------------------------------------------------------------------
# Se definen variables globales privadas para:
# - Reutilizar conexiones
# - Evitar crear múltiples clientes MongoClient innecesarios
#
# MongoClient es thread-safe y mantiene su propio pool,
# por lo que esta estrategia es correcta y eficiente.
_client_a: MongoClient | None = None
_client_b: MongoClient | None = None


# -----------------------------------------------------------------------------
# OBTENER CLIENTE MONGO A
# -----------------------------------------------------------------------------
def get_mongo_a_client() -> MongoClient:
    """
    Retorna el cliente MongoDB para la base A (task_logs).

    Estrategia:
    - Lazy initialization:
        El cliente se crea solo la primera vez que se solicita.
    - Singleton por proceso:
        El mismo cliente se reutiliza en toda la aplicación.
    """

    global _client_a

    # Si el cliente aún no existe, se crea
    if _client_a is None:
        _client_a = MongoClient(settings.mongo_a_url)

    return _client_a


# -----------------------------------------------------------------------------
# OBTENER CLIENTE MONGO B
# -----------------------------------------------------------------------------
def get_mongo_b_client() -> MongoClient:
    """
    Retorna el cliente MongoDB para la base B (access_logs).

    Mantener A y B separados permite:
    - Aislar logs funcionales de logs de seguridad
    - Escalar independientemente
    """

    global _client_b

    if _client_b is None:
        _client_b = MongoClient(settings.mongo_b_url)

    return _client_b


# -----------------------------------------------------------------------------
# OBTENER BASE DE DATOS MONGO A
# -----------------------------------------------------------------------------
def get_mongo_a_db():
    """
    Retorna la base de datos Mongo A.

    Flujo:
    - get_mongo_a_client() → MongoClient
    - [settings.MONGO_A_DB] → Database
    """

    return get_mongo_a_client()[settings.MONGO_A_DB]


# -----------------------------------------------------------------------------
# OBTENER BASE DE DATOS MONGO B
# -----------------------------------------------------------------------------
def get_mongo_b_db():
    """
    Retorna la base de datos Mongo B.

    Usada principalmente para:
    - Auditoría
    - Logs de accesos
    """

    return get_mongo_b_client()[settings.MONGO_B_DB]


# -----------------------------------------------------------------------------
# FUNCIÓN DE COMPATIBILIDAD
# -----------------------------------------------------------------------------
def get_mongo_db():
    """
    Función de compatibilidad retroactiva.

    Motivo:
    - Código antiguo llama a get_mongo_db()
    - Para no romper nada, se mapea a Mongo A

    Esto permite refactorizar gradualmente
    sin afectar funcionalidad existente.
    """

    return get_mongo_a_db()
