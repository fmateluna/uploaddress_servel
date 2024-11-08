from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Configuración para conectar a PostgreSQL usando variables de entorno
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "Geo"),
    "user": os.getenv("DB_USER", "doomguy"),
    "password": os.getenv("DB_PASSWORD", "IDDQD"),
    "host": os.getenv("DB_HOST", "10.247.119.90"),
    "port": os.getenv("DB_PORT", "5434"),
}

# Crear el motor de SQLAlchemy
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """Función para obtener una sesión de base de datos."""
    return SessionLocal()


def load_query(filename):
    # Ruta completa al archivo de consulta SQL
    base_path = os.path.join(os.path.dirname(__file__), "queries")
    file_path = os.path.join(base_path, filename)

    with open(file_path, "r") as file:
        return file.read()
