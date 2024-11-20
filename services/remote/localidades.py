import os
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from contextlib import contextmanager
from datetime import datetime
import time

from repositories.address_score_repo import insert_or_update_address_score
from repositories.models import Address, AddressScore, ApiLogs, ApiResponseValues


# Configuración de la base de datos para prototipo_servel
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME_SERVEL", "prototipo_servel"),
    "user": os.getenv("DB_USER", "georoot"),
    "password": os.getenv("DB_PASSWORD", "Servel_IDDQD"),
    "host": os.getenv("DB_HOST", "10.247.119.90"),
    "port": os.getenv("DB_PORT", "5434"),
}

# Crear el motor de conexión
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DATABASE_URL, poolclass=NullPool)

# Crear una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_localidad_session():
    """
    Provee una sesión para interactuar con la base de datos `prototipo_servel`.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class LocalidadesAPI:

    def fetch_location_details(self, direccion: str):
        query = text(
            """
            WITH similarity_scores AS (
                SELECT
                    id,
                    nombre || ' ' || comuna || ' ' || glosa_re AS direccion,
                    COALESCE(
                        similarity(
                            nombre || ' ' || comuna || ' ' || glosa_re || ' Chile',
                            :direccion
                        ),
                        0
                    ) AS score
                FROM localidades
            )
            SELECT
                ss.direccion,
                ss.score AS total_score,
                l.nombre,
                l.comuna,
                l.region,
                l.*
            FROM localidades l
            JOIN similarity_scores ss
                ON l.id = ss.id
            ORDER BY ss.score DESC
            LIMIT 1
            """
        )
        try:
            # Ejecutar la consulta
            with get_localidad_session() as session:
                try:
                    result = session.execute(query, {"direccion": direccion}).fetchone()
                except SQLAlchemyError as e:
                    raise Exception(f"Error ejecutando la consulta SQL: {str(e)}")

            # Convertir el resultado a JSON si existe
            if result:
                try:
                    return dict(result._asdict())
                except AttributeError as e:
                    raise Exception(f"Error al convertir el resultado a JSON: {str(e)}")
            else:
                return None

        except Exception as e:
            # Captura cualquier error general y lo muestra
            print(f"Error en 'fetch_location_details': {str(e)}")
            return None

    def __init__(self):
        self.session = get_localidad_session()  # Usamos la nueva función de sesión

    # address_record.id, "latitud", latitude, response_time, api_log.id
    def _save_api_response_attribute(
        self, address_id, attribute_name, attribute_value, api_logs_id
    ):
        try:
            api_response = ApiResponseValues(
                type_api_id=2,
                api_logs_id=api_logs_id,
                address_id=address_id,
                attribute_name=attribute_name,
                attribute_value=str(attribute_value),
            )
            self.session.add(api_response)
        except SQLAlchemyError as e:
            print(f"Error guardando atributos en ApiResponseValues: {str(e)}")
            self.session.rollback()
            raise

    def get_geolocation(self, address: str, update: bool = False):
        try:
            # Llamamos a `fetch_location_details` para obtener los detalles de la localización
            response_data = self.fetch_location_details(direccion=address)

            if not response_data:
                raise ValueError(
                    f"No se encontró información para la dirección: {address}"
                )

            return response_data

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error en la base de datos: {str(e)}")
            return f"{str(e)}"
        except Exception as e:
            print(f"Error en la llamada a LocalidadesAPI: {str(e)}")
            return f"{str(e)}"
