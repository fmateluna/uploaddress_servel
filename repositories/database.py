 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Configuración para conectar a PostgreSQL
DB_CONFIG = {
    "dbname": "Geo",
    "user": "georoot",
    "password": "servel2024_",
    "host": "10.247.119.90",
    "port": "5434",
}


DATABASE_URL = "postgresql://georoot:servel2024_@10.247.119.90:5434/Geo"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_query(filename):
    # Ruta completa al archivo de consulta SQL
    base_path = os.path.join(os.path.dirname(__file__), 'queries')
    file_path = os.path.join(base_path, filename)
    
    with open(file_path, 'r') as file:
        return file.read()



