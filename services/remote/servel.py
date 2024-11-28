import os

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from contextlib import contextmanager
from datetime import datetime
import time

from repositories.address_score_repo import insert_or_update_address_score
from repositories.database import get_session
from repositories.models import Address, AddressScore, ApiLogs, ApiResponseValues
from services.remote.common import ResponseGeo


# Configuración de la base de datos para prototipo_servel
DB_CONFIG_SERVEL = {
    "dbname": os.getenv("DB_NAME_SERVEL", "prototipo_servel"),
    "user": os.getenv("DB_USER", "georoot"),
    "password": os.getenv("DB_PASSWORD", "Servel_IDDQD"),
    "host": os.getenv("DB_HOST", "10.247.119.90"),
    "port": os.getenv("DB_PORT", "5434"),
}

# Crear el motor de conexión
DATABASE_URL = f"postgresql://{DB_CONFIG_SERVEL['user']}:{DB_CONFIG_SERVEL['password']}@{DB_CONFIG_SERVEL['host']}:{DB_CONFIG_SERVEL['port']}/{DB_CONFIG_SERVEL['dbname']}"
engine = create_engine(DATABASE_URL, poolclass=NullPool)

# Crear una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_servel_session():
    """
    Provee una sesión para interactuar con la base de datos `prototipo_servel`.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class ServelDataBase:
    def tipo_geo_direccion_persona(
        self, direccion: str, numero: str, comuna: str, region: str
    ):
        query = text(
            """
            WITH direcciones AS (
                SELECT
                    dp.id,
                    dp.numero,
                    nombre_via || ' ' || c.comuna || ' ' || c.provincia || ' ' || r.region || ' Chile' AS direccion,
                    COALESCE(SIMILARITY(
                        nombre_via || ' ' || c.comuna || ' ' || c.provincia || ' ' || r.region || ' Chile', :direccion
                    ), 0) * 100 AS score,
                    CASE 
                        WHEN dp.numero = :numero THEN 1
                        ELSE 0
                    END AS prioridad,
                    COALESCE(SIMILARITY(c.comuna, :comuna), 0) AS comuna_score, -- Comparación flexible para comuna
                    COALESCE(SIMILARITY(r.region, :region), 0) AS region_score -- Comparación flexible para región
                FROM
                    direccion_persona AS dp
                INNER JOIN
                    regiones AS r ON r.cut_reg = dp.cut_region
                INNER JOIN
                    comunas AS c ON c.cut_com = dp.cut_comuna
                WHERE
                    SIMILARITY(c.comuna, :comuna) > 0.2 AND -- Umbral para coincidencia en comuna
                    SIMILARITY(r.region, :region) > 0.2 -- Umbral para coincidencia en región
            )
            SELECT
                id,
                numero,
                direccion,
                score,
                comuna_score,
                region_score
            FROM
                direcciones
            WHERE 
                score > 80
            ORDER BY
                score DESC,        -- Prioriza el mayor puntaje en dirección
                comuna_score DESC, -- Luego, mayor coincidencia en comuna
                region_score DESC, -- Luego, mayor coincidencia en región
                prioridad DESC     -- Finalmente, coincidencia exacta en número
            LIMIT 1;
            """
        )
        try:
            # Ejecutar la consulta
            with get_servel_session() as session:
                try:
                    result = session.execute(
                        query,
                        {
                            "direccion": direccion,
                            "numero": numero,
                            "comuna": comuna,
                            "region": region,
                        },
                    ).fetchone()
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
            print(f"Error en 'tipo_geo_direccion_persona': {str(e)}")
            return None

    def tipo_geo_localidades(self, direccion: str):
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
                        ) * 100 AS score -- Convertimos el score a porcentaje
                    FROM localidades
                )
                SELECT
                    ss.direccion,
                    TO_CHAR(ss.score::NUMERIC(5, 2), 'FM999990.00') AS score, 
                    l.nombre,
                    l.comuna,
                    l.region,
                    l.id,
                    l.geom,                          
                    l.objectid,
                    l.id_localid,
                    l.cod_comuna,
                    l.comuna,
                    l.region,
                    l.glosa_re,      
                    l.nombre,
                    l.longitud,
                    l.latitud,
                    l.tipo,
                    l.estado,
                    l.circuns,
                    l.codigo_cir,
                    l.glosacircu,
                    l.principal,
                    l.revisado,
                    l.created_user,
                    l.last_edited_user,
                    l.globalid 
                FROM localidades l
                JOIN similarity_scores ss
                    ON l.id = ss.id
                ORDER BY ss.score DESC
                LIMIT 1;



            """
        )
        try:
            # Ejecutar la consulta
            with get_servel_session() as session:
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
            print(f"Error en 'tipo_geo_localidades': {str(e)}")
            return None

    def __init__(self):
        self.session = get_session()  # Usamos la nueva función de sesión

    # address_record.id, "latitud", latitude, response_time, api_log.id
    def _save_api_response_attribute(
        self, address_id, attribute_name, attribute_value, api_logs_id
    ):
        try:
            api_response = ApiResponseValues(
                type_api_id=3,
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

    def get_geolocation(self, address_record: Address) -> ResponseGeo:
        response_geo_servel = ResponseGeo()
        response_data_query = {}
        origen = ""
        try:

            if address_record.servel_tipo_geo.upper() in ["SNRU", "SN", None]:
                response_data_query = self.tipo_geo_localidades(
                    direccion=address_record.full_address
                )
                origen = "Localidades"

            if address_record.servel_tipo_geo.upper() in ["A1", "A2", "A3"]:
                response_data_query = self.tipo_geo_direccion_persona(
                    direccion=address_record.full_address,
                    comuna=address_record.commune,
                    region=address_record.region,
                    numero=address_record.house_number,
                )
                origen = "DireccionPersona"

            if not response_data_query:
                print(
                    "[!] Servel no se encontró data para "
                    + address_record.servel_tipo_geo
                    + " en "
                    + origen
                )
                raise ValueError(
                    f"No se encontró información para la dirección: {address_record.full_address}"
                )
            else:
                print(origen)
                if origen == "DireccionPersona":
                    print("EXITO!!!!")
                    print(response_data_query)

            # Registrar en ApiLogs
            response_time = datetime.now()
            api_log = ApiLogs(
                address_id=address_record.id,
                request_payload=address_record.full_address,
                response_payload=response_data_query,
                created_at=datetime.now(),
                status_code=200,
                response_time_ms=(datetime.now() - response_time).microseconds // 1000,
            )
            self.session.add(api_log)

            # Procesar los datos de la respuesta
            display_name = response_data_query.get(
                "direccion"
            )  # Tomamos el primer resultado
            latitude = float(response_data_query.get("latitud"))
            longitude = float(response_data_query.get("longitud"))

            self._save_api_response_attribute(
                address_record.id, "latitud", latitude, api_log.id
            )
            self._save_api_response_attribute(
                address_record.id, "longitude", longitude, api_log.id
            )
            self._save_api_response_attribute(
                address_record.id, "address", display_name, api_log.id
            )

            # El porcentaje de calidad tiene que ver con la
            # direccion vs comuna + region + nombre y su porcentaje de similitud
            quality_score = response_data_query.get("score")

            # Registrar en AddressScore
            insert_or_update_address_score(address_record.id, "Servel", quality_score)
            self.session.commit()

            response_geo_servel.latitud = latitude
            response_geo_servel.longitud = longitude
            response_geo_servel.origen = origen
            response_geo_servel.address = response_data_query.get("direccion")
            return response_geo_servel

        except SQLAlchemyError as e:
            self.session.rollback()
            # print(f"Error en la base de datos de Servel: {str(e)}")
            return response_geo_servel
        except Exception as e:
            # print(f"Error en la llamada a Servel: {str(e)}")
            return response_geo_servel
