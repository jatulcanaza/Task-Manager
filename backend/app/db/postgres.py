from sqlalchemy import create_engine  # Crea el "engine" (conexión/configuración base) hacia la BD
from sqlalchemy.orm import sessionmaker  # Fábrica de sesiones para trabajar con SQLAlchemy ORM
from app.core.config import settings  # Configuración (incluye postgres_url)

# Engine de SQLAlchemy:
# - settings.postgres_url contiene la URL completa de conexión (usuario, pass, host, puerto, db)
# - pool_pre_ping=True verifica que la conexión del pool siga viva antes de usarla (evita conexiones "muertas")
engine = create_engine(settings.postgres_url, pool_pre_ping=True)

# SessionLocal es una fábrica para crear sesiones de BD.
# - autoflush=False: no hace flush automático antes de ciertas operaciones (más control explícito)
# - autocommit=False: las transacciones se confirman manualmente con commit()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """
    Dependency generator para FastAPI (o cualquier capa que use inyección de dependencias).
    - Crea una sesión por request/uso
    - La "yield" para que el caller la use
    - Asegura el cierre de la sesión al final (finally), evitando fugas de conexión
    """
    db = SessionLocal()  # Crea una nueva sesión (unidad de trabajo) contra la BD
    try:
        yield db  # Entrega la sesión al endpoint/servicio que la necesite
    finally:
        db.close()  # Cierra la sesión y libera la conexión al pool
