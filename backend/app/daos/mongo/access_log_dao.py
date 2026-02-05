from datetime import datetime

class AccessLogDAO:
    def __init__(self, db):
        self.col = db["access_logs"]

    def write(self, owner_id: str, access_type: str):
        self.col.insert_one({
            "owner_id": owner_id,
            "access_type": access_type,  # "SSO_TOKEN" | "NORMAL_LOGIN"
            "timestamp": datetime.utcnow()
        })

    def stats(self):
        pipeline = [
            {"$group": {"_id": "$access_type", "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "access_type": "$_id", "count": 1}}
        ]
        return list(self.col.aggregate(pipeline))
