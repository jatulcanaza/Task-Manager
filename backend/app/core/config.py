from pydantic_settings import BaseSettings

# -----------------------------------------------------------------------------
# SETTINGS CENTRALIZADOS DE LA APLICACIÓN
# -----------------------------------------------------------------------------
# Esta clase:
# - Lee variables de entorno automáticamente (Docker, .env, CI/CD).
# - Valida tipos (str, int, etc.).
# - Centraliza TODA la configuración sensible del sistema.
#
# BaseSettings (Pydantic):
# - Permite inyectar config sin hardcodear credenciales.
# - Es ideal para microservicios y despliegues en contenedores.
# -----------------------------------------------------------------------------
class Settings(BaseSettings):

    # =========================================================================
    # POSTGRESQL (Base de datos relacional principal)
    # =========================================================================
    # Usada normalmente para:
    # - Usuarios
    # - Tasks
    # - Roles
    # - Entidades transaccionales
    #
    # Separa credenciales, host y puerto para mayor flexibilidad.
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # =========================================================================
    # MONGO A – task_logs
    # =========================================================================
    # Base de datos NoSQL dedicada a:
    # - Logs de eventos de tareas
    # - Historial
    # - Auditoría funcional
    #
    # Patrón: "Database per concern"
    # (No mezclamos datos operativos con logs)
    MONGO_A_INITDB_ROOT_USERNAME: str
    MONGO_A_INITDB_ROOT_PASSWORD: str
    MONGO_A_HOST: str
    MONGO_A_PORT: int
    MONGO_A_DB: str

    # =========================================================================
    # MONGO B – access_logs
    # =========================================================================
    # Segunda base Mongo separada exclusivamente para:
    # - Logs de accesos
    # - SSO
    # - Tokens
    # - Auditoría de seguridad
    #
    # Esto permite:
    # - Aislar seguridad de lógica de negocio
    # - Escalar logs sin afectar performance
    MONGO_B_INITDB_ROOT_USERNAME: str
    MONGO_B_INITDB_ROOT_PASSWORD: str
    MONGO_B_HOST: str
    MONGO_B_PORT: int
    MONGO_B_DB: str

    # =========================================================================
    # JWT – AUTENTICACIÓN Y AUTORIZACIÓN
    # =========================================================================
    # JWT_SECRET:
    # - Clave usada para firmar tokens
    # - CRÍTICA para seguridad
    #
    # JWT_EXPIRES_MIN:
    # - Tiempo de vida del token
    # - Default: 60 minutos
    JWT_SECRET: str
    JWT_EXPIRES_MIN: int = 60

    # =========================================================================
    # RABBITMQ – BUS DE EVENTOS
    # =========================================================================
    # Usado para:
    # - Comunicación asíncrona
    # - Eventos (task.created, task.updated, etc.)
    # - Desacoplar servicios
    #
    # Defaults pensados para Docker Compose
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"

    # =========================================================================
    # MQTT – TIEMPO REAL
    # =========================================================================
    # Usado para:
    # - Comunicación en tiempo real
    # - Dashboard
    # - WebSockets indirectos
    #
    # Flujo:
    # RabbitMQ → Bridge → MQTT → Backend B → WebSocket → Frontend
    MQTT_HOST: str = "mosquitto"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "task/events"

    # =========================================================================
    # SMTP – NOTIFICACIONES (EMAIL)
    # =========================================================================
    # Usado para:
    # - Notificaciones administrativas
    # - Alertas de eventos críticos
    #
    # Diseño defensivo:
    # - Si USER/PASS están vacíos, el sistema NO falla
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "TaskManager <nutrygym.uce@gmail.com>"
    ADMIN_NOTIFY_TO: str = ""

    # =========================================================================
    # CORS
    # =========================================================================
    # Controla qué orígenes pueden consumir la API
    # (Frontend web, dashboard, etc.)
    #
    # En producción normalmente se amplía o se parametriza
    CORS_ORIGINS: str = "http://localhost:8080"

    # =========================================================================
    # PROPIEDAD: URL COMPLETA DE POSTGRES
    # =========================================================================
    # Construye la URL de conexión a Postgres dinámicamente.
    #
    # Ventajas:
    # - No se repite lógica en el código
    # - Cambios de host/puerto no rompen nada
    # - Compatible con SQLAlchemy
    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # =========================================================================
    # PROPIEDAD: URL DE MONGO A (task_logs)
    # =========================================================================
    # authSource=admin:
    # - Autenticación contra la base admin
    # - Práctica estándar en Mongo con usuarios root
    @property
    def mongo_a_url(self) -> str:
        return (
            f"mongodb://{self.MONGO_A_INITDB_ROOT_USERNAME}:{self.MONGO_A_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_A_HOST}:{self.MONGO_A_PORT}/?authSource=admin"
        )

    # =========================================================================
    # PROPIEDAD: URL DE MONGO B (access_logs)
    # =========================================================================
    # Se mantiene totalmente independiente de Mongo A
    # (principio de aislamiento)
    @property
    def mongo_b_url(self) -> str:
        return (
            f"mongodb://{self.MONGO_B_INITDB_ROOT_USERNAME}:{self.MONGO_B_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_B_HOST}:{self.MONGO_B_PORT}/?authSource=admin"
        )


# -----------------------------------------------------------------------------
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# -----------------------------------------------------------------------------
# Esta instancia:
# - Se importa en cualquier parte del proyecto
# - Se carga UNA sola vez
# - Centraliza TODA la config del sistema
#
# Ejemplo de uso:
# settings.postgres_url
# settings.JWT_SECRET
# settings.MQTT_TOPIC
settings = Settings()
