import os
import requests
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import time

from repositories.address_score_repo import insert_or_update_address_score
from repositories.database import get_session
from repositories.models import Address, AddressScore, ApiLogs, ApiResponseValues


class NominatimAPI:

    def __init__(self):
        self.session = get_session()  # Obtenemos la sesión para la base de datos

    # address_record.id, "latitud", latitude, response_time, api_log.id
    def _save_api_response_attribute(
        self, address_id, attribute_name, attribute_value, api_logs_id
    ):
        api_response = ApiResponseValues(
            type_api_id=2,
            api_logs_id=api_logs_id,
            address_id=address_id,
            attribute_name=attribute_name,
            attribute_value=str(attribute_value),
        )
        self.session.add(api_response)

    def call_api(self, address: str) -> dict:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "MiApp/1.0 (contacto@miapp.com)"}
        params = {"q": address, "format": "json", "limit": 1}

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        # Comprobamos si la respuesta tiene datos
        data = response.json()
        if not data:
            raise ValueError(
                "No se encontraron resultados para la dirección proporcionada."
            )

        return data[0]  # Toma el primer resultado en caso de varios

    def get_geolocation(self, address_record: Address) -> dict:
        # Verifica si ya existe una entrada para la dirección en la base de datos

        # Si existe y no se solicita una actualización, se devuelve el último response almacenado
        if address_record:
            api_response_from_logs = (
                self.session.query(ApiLogs)
                .filter_by(address_id=address_record.id, type_api_id=2)
                .first()
            )
            if api_response_from_logs:
                return api_response_from_logs.response_payload
        try:
            response_data = self.call_api(
                address_record.full_address
            )  # Llamamos directamente a NominatimAPI

            # Procesar los datos de la respuesta
            display_name = response_data.get(
                "display_name"
            )  # Tomamos el primer resultado
            latitude = float(response_data.get("lat"))
            longitude = float(response_data.get("lon"))
            # https://nominatim.org/release-docs/develop/customize/Ranking/
            # Mapeo de categorías (address_type) y puntajes de exactitud sugeridos para Nominatim:
            #
            # Categoría           | Descripción                                   | Puntaje de Exactitud Sugerido (%)
            # -------------------------------------------------------------------------------------------
            # "house"             | Ubicación exacta de una casa                  | 100
            # "building"          | Edificio específico                           | 95
            # "road"              | Calle o carretera                             | 85
            # "neighbourhood"     | Barrio o vecindario                           | 80
            # "suburb"            | Suburbio o sector dentro de una ciudad        | 75
            # "city"              | Ciudad o municipio                            | 70
            # "county"            | Condado o división administrativa mayor       | 60
            # "state"             | Estado o provincia                            | 50
            # "country"           | País                                          | 40
            # "continent"         | Continente                                    | 30
            #
            # Este mapeo asigna un puntaje de exactitud a cada categoría, donde los valores más altos representan
            # ubicaciones más específicas (ej. "house" o "building") y valores más bajos representan áreas amplias
            # o menos específicas (ej. "country" o "continent").

            quality_score = response_data.get("addresstype")

            # Registrar en AddressScore
            insert_or_update_address_score(
                address_record.id, "Nominatim", quality_score
            )

            # Registrar en ApiLogs
            response_time = datetime.now()
            api_log = ApiLogs(
                address_id=address_record.id,
                request_payload=address_record.full_address,
                response_payload=response_data,
                created_at=datetime.now(),
                status_code=200,
                response_time_ms=(datetime.now() - response_time).microseconds // 1000,
            )
            self.session.add(api_log)
            self.session.flush()
            # Usar el método auxiliar para guardar los atributos en `ApiResponse`
            self._save_api_response_attribute(
                address_record.id, "latitud", latitude, api_log.id
            )
            self._save_api_response_attribute(
                address_record.id, "longitude", longitude, api_log.id
            )
            self._save_api_response_attribute(
                address_record.id, "address", display_name, api_log.id
            )

            self.session.commit()
            return response_data

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error en la base de datos: {str(e)}")
            return f"{str(e)}"
        except Exception as e:
            print(f"Error en la llamada a Nominatim: {str(e)}")
            return f"{str(e)}"
