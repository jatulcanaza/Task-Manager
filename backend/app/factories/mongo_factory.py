from app.factories.abstract_factory import AbstractDAOFactory
from app.daos.mongo.log_dao_mongo import MongoLogDAO
from app.daos.mongo.access_log_dao import AccessLogDAO

class MongoFactory(AbstractDAOFactory):
    """
    Fábrica concreta que provee DAOs relacionados a MongoDB.
    MongoDB se usa para logs.
    """

    def __init__(self, mongo_db):
        self.mongo_db = mongo_db

    def user_dao(self):
        raise NotImplementedError("Usuarios se manejan en PostgreSQL")

    def task_dao(self):
        raise NotImplementedError("Tareas se manejan en PostgreSQL")

    def log_dao(self):
        return MongoLogDAO(self.mongo_db)

    def access_log_dao(self):
        return AccessLogDAO(self.mongo_db)
