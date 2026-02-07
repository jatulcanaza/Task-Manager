from pymongo import MongoClient
from app.core.config import settings

_client_a: MongoClient | None = None
_client_b: MongoClient | None = None

def get_mongo_a_client() -> MongoClient:
    global _client_a
    if _client_a is None:
        _client_a = MongoClient(settings.mongo_a_url)
    return _client_a

def get_mongo_b_client() -> MongoClient:
    global _client_b
    if _client_b is None:
        _client_b = MongoClient(settings.mongo_b_url)
    return _client_b

def get_mongo_a_db():
    return get_mongo_a_client()[settings.MONGO_A_DB]

def get_mongo_b_db():
    return get_mongo_b_client()[settings.MONGO_B_DB]

# compat: tu código actual llama get_mongo_db() en A => devolvemos A
def get_mongo_db():
    return get_mongo_a_db()
