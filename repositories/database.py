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


def load_query(filename):
    # Ruta completa al archivo de consulta SQL
    base_path = os.path.join(os.path.dirname(__file__), "queries")
    file_path = os.path.join(base_path, filename)

    with open(file_path, "r") as file:
        return file.read()
