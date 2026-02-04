from app.factories.abstract_factory import AbstractDAOFactory  # Interfaz/base de la fábrica de DAOs (Abstract Factory)
from app.daos.mongo.log_dao_mongo import MongoLogDAO  # Implementación concreta del DAO de logs en MongoDB

class MongoFactory(AbstractDAOFactory):
    """
    Fábrica concreta que provee DAOs relacionados a MongoDB.

    En este diseño, MongoDB se usa únicamente para logs:
    - user_dao y task_dao NO aplican aquí (se gestionan en PostgreSQL)
    - log_dao sí se provee mediante MongoLogDAO
    """

    def __init__(self, mongo_db):
        # Guarda la referencia a la base de datos Mongo ya inicializada/conectada
        self.mongo_db = mongo_db

    def user_dao(self):
        # Esta fábrica no soporta usuarios porque el sistema los maneja con PostgreSQL
        raise NotImplementedError("Usuarios se manejan en PostgreSQL")

    def task_dao(self):
        # Esta fábrica no soporta tareas porque el sistema las maneja con PostgreSQL
        raise NotImplementedError("Tareas se manejan en PostgreSQL")

    def log_dao(self):
        # Devuelve el DAO concreto para logs en Mongo, usando la DB inyectada
        return MongoLogDAO(self.mongo_db)
