from pydantic_settings import BaseSettings  # Base para definir configuración leída desde variables de entorno

class Settings(BaseSettings):
    """
    Centraliza la configuración de la aplicación usando Pydantic Settings.
    - Por defecto, Pydantic leerá estos valores desde variables de entorno.
    - Los tipos (str/int) sirven para validar y castear automáticamente.
    """

    # ---------- Configuración de PostgreSQL ----------
    POSTGRES_USER: str            # Usuario de conexión a PostgreSQL
    POSTGRES_PASSWORD: str        # Contraseña de conexión a PostgreSQL
    POSTGRES_DB: str              # Nombre de la base de datos PostgreSQL
    POSTGRES_HOST: str            # Host/IP del servidor PostgreSQL
    POSTGRES_PORT: int            # Puerto del servidor PostgreSQL

    # ---------- Configuración de MongoDB ----------
    MONGO_INITDB_ROOT_USERNAME: str  # Usuario root/administrador de MongoDB (init)
    MONGO_INITDB_ROOT_PASSWORD: str  # Password del usuario root/administrador de MongoDB (init)
    MONGO_HOST: str                  # Host/IP del servidor MongoDB
    MONGO_PORT: int                  # Puerto del servidor MongoDB
    MONGO_DB: str                    # Nombre de la base de datos MongoDB (si aplica en tu app)

    # ---------- Configuración de JWT / Seguridad ----------
    JWT_SECRET: str              # Secreto para firmar/verificar tokens JWT (NO debe ir hardcodeado)
    JWT_EXPIRES_MIN: int = 60    # Minutos de expiración del JWT (valor por defecto: 60)

    # ---------- Configuración de CORS ----------
    CORS_ORIGINS: str = "http://localhost:8080"  # Origen permitido para CORS (ej: frontend local)

    @property
    def postgres_url(self) -> str:
        """
        Construye la URL de conexión a PostgreSQL en formato SQLAlchemy.
        Usa driver psycopg2:
          postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB
        """
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def mongo_url(self) -> str:
        """
        Construye la URL de conexión a MongoDB autenticando contra la base 'admin'.
        Formato:
          mongodb://USER:PASSWORD@HOST:PORT/?authSource=admin
        """
        return (
            f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:{self.MONGO_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/?authSource=admin"
        )

settings = Settings()  # Instancia la configuración leyendo automáticamente desde variables de entorno
