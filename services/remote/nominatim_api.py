import os
import requests
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import time

from repositories.database import get_session
from repositories.models import Address, AddressScore, ApiLogs, ApiResponse


class NominatimAPI:

    def __init__(self):
        self.session = get_session()  # Obtenemos la sesión para la base de datos

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

    def get_geolocation(self, address: str):
        try:
            response_data = self.call_api(
                address
            )  # Llamamos directamente a NominatimAPI
            status_code = 200
            response_time = datetime.now()

            # Procesar los datos de la respuesta
            display_name = response_data[0].get(
                "display_name"
            )  # Tomamos el primer resultado
            latitude = float(response_data[0].get("lat"))
            longitude = float(response_data[0].get("lon"))
            quality_score = response_data[0].get("importance")

            # Buscar o crear el registro de dirección
            address_record = (
                self.session.query(Address).filter_by(full_address=display_name).first()
            )
            if not address_record:
                address_record = Address(full_address=display_name)
                self.session.add(address_record)
                self.session.commit()

            # Registrar en AddressScore
            address_score = AddressScore(
                address_id=address_record.id,
                quality_label="Nominatim",
                score=quality_score,
            )
            self.session.add(address_score)

            # Registrar en ApiResponse
            api_response = ApiResponse(
                type_api_id=2,
                address_id=address_record.id,
                attribute_name="coordinates",
                attribute_value=f"Lat: {latitude}, Lng: {longitude}",
                created_at=datetime.now(),
            )
            self.session.add(api_response)
            self.session.commit()

            # Registrar en ApiLogs
            api_log = ApiLogs(
                api_response_id=api_response.id,
                address_id=address_record.id,
                request_payload=request_payload,
                response_payload=response_data,
                created_at=datetime.now(),
                status_code=status_code,
                response_time_ms=(datetime.now() - response_time).microseconds // 1000,
            )
            self.session.add(api_log)
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error en la base de datos: {str(e)}")
        except Exception as e:
            print(f"Error en la llamada a Nominatim: {str(e)}")
