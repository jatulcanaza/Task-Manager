from datetime import datetime
# datetime:
#   - Se utiliza para registrar la fecha/hora del acceso
#   - Se guarda en UTC para consistencia entre servicios y zonas horarias


# -----------------------------------------------------------------------------
# ACCESS LOG DAO (MongoDB)
# -----------------------------------------------------------------------------
# DAO = Data Access Object
#
# Responsabilidad:
# - Encapsular el acceso a la colección MongoDB "access_logs"
# - Registrar accesos al sistema
# - Proveer estadísticas agregadas de acceso
#
# Esta clase NO contiene lógica de negocio,
# solo persistencia y consultas.
# -----------------------------------------------------------------------------
class AccessLogDAO:

    def __init__(self, db):
        """
        Constructor del DAO.

        Parámetro:
        - db:
            Referencia a una base de datos MongoDB ya conectada
            (ej. client[MONGO_B_DB])

        Se selecciona la colección "access_logs".
        """

        # Colección Mongo donde se guardan los accesos
        self.col = db["access_logs"]

    # -------------------------------------------------------------------------
    # REGISTRAR ACCESO
    # -------------------------------------------------------------------------
    def write(self, owner_id: str, access_type: str):
        """
        Inserta un registro de acceso en MongoDB.

        Parámetros:
        - owner_id:
            Identificador del usuario (ej. UUID como string)
        - access_type:
            Tipo de acceso:
            - "SSO_TOKEN"
            - "NORMAL_LOGIN"

        Cada registro incluye:
        - Identidad del usuario
        - Tipo de acceso
        - Timestamp en UTC
        """

        self.col.insert_one({
            "owner_id": owner_id,
            "access_type": access_type,
            "timestamp": datetime.utcnow()
        })

    # -------------------------------------------------------------------------
    # ESTADÍSTICAS DE ACCESO
    # -------------------------------------------------------------------------
    def stats(self):
        """
        Retorna estadísticas agregadas de accesos por tipo.

        Utiliza un pipeline de agregación de MongoDB:

        1) $group:
           - Agrupa documentos por access_type
           - Cuenta cuántos registros existen por tipo

        2) $project:
           - Renombra campos
           - Oculta el campo _id interno de MongoDB

        Retorno:
        - Lista de documentos con formato:
          [
            {"access_type": "SSO_TOKEN", "count": 12},
            {"access_type": "NORMAL_LOGIN", "count": 45}
          ]
        """

        pipeline = [
            {
                "$group": {
                    "_id": "$access_type",
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "access_type": "$_id",
                    "count": 1
                }
            }
        ]

        return list(self.col.aggregate(pipeline))
