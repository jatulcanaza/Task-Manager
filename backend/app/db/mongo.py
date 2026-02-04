from pymongo import MongoClient  # Cliente oficial de MongoDB para Python
from app.core.config import settings  # Configuración (incluye mongo_url y MONGO_DB)

# Cliente global para reutilizar la conexión (patrón "singleton" simple a nivel de módulo)
_client = None

def get_mongo_client() -> MongoClient:
    """
    Devuelve una instancia única (reutilizable) de MongoClient.
    - Usa una variable global _client para no crear múltiples conexiones.
    - Si aún no existe, la crea usando la URL construida en settings.mongo_url.
    """
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_url)  # Conecta usando credenciales/host/puerto definidos en settings
    return _client

def get_mongo_db():
    """
    Devuelve la base de datos de Mongo configurada en settings.MONGO_DB.
    - Obtiene primero el cliente (reutilizado).
    - Accede a la DB por nombre como si fuera un diccionario: client["db_name"].
    """
    client = get_mongo_client()
    return client[settings.MONGO_DB]
