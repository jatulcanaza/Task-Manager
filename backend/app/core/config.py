from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ---------- PostgreSQL ----------
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # ---------- Mongo A (task_logs) ----------
    MONGO_A_INITDB_ROOT_USERNAME: str
    MONGO_A_INITDB_ROOT_PASSWORD: str
    MONGO_A_HOST: str
    MONGO_A_PORT: int
    MONGO_A_DB: str

    # ---------- Mongo B (access_logs) ----------
    MONGO_B_INITDB_ROOT_USERNAME: str
    MONGO_B_INITDB_ROOT_PASSWORD: str
    MONGO_B_HOST: str
    MONGO_B_PORT: int
    MONGO_B_DB: str

    # ---------- JWT ----------
    JWT_SECRET: str
    JWT_EXPIRES_MIN: int = 60

    # RabbitMQ / MQTT / SMTP (igual que tienes)
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"

    MQTT_HOST: str = "mosquitto"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "task/events"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "TaskManager <nutrygym.uce@gmail.com>"
    ADMIN_NOTIFY_TO: str = ""

    CORS_ORIGINS: str = "http://localhost:8080"

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def mongo_a_url(self) -> str:
        return (
            f"mongodb://{self.MONGO_A_INITDB_ROOT_USERNAME}:{self.MONGO_A_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_A_HOST}:{self.MONGO_A_PORT}/?authSource=admin"
        )

    @property
    def mongo_b_url(self) -> str:
        return (
            f"mongodb://{self.MONGO_B_INITDB_ROOT_USERNAME}:{self.MONGO_B_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_B_HOST}:{self.MONGO_B_PORT}/?authSource=admin"
        )

settings = Settings()
