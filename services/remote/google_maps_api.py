import os
import requests
from sqlalchemy.orm import Session

from datetime import datetime
import time

from repositories.database import get_session
from repositories.models import Address, AddressScore, ApiLogs, ApiResponse

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class GoogleMapsAPI:
    def __init__(self):
        self.session = get_session()

    def get_geolocation(self, address: str) -> dict:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": GOOGLE_API_KEY}

        # Registrar el inicio de la solicitud para calcular el tiempo de respuesta
        start_time = time.time()
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            response_data = response.json()
            status_code = response.status_code
        except requests.RequestException as e:
            # Manejo de errores en caso de fallos en la solicitud
            self._log_error(address, params, str(e), 500, 0)
            raise

        # Calcular el tiempo de respuesta
        response_time = int((time.time() - start_time) * 1000)  # en milisegundos

        # Procesar y registrar los datos de la respuesta
        self._register_api_response(
            address, params, response_data, status_code, response_time
        )

        return response_data

    def _register_api_response(
        self,
        address: str,
        request_payload: dict,
        response_data: dict,
        status_code: int,
        response_time: int,
    ):
        # Extraer y registrar la información relevante
        if response_data.get("status") == "OK":
            result = response_data["results"][0]  # Toma el primer resultado

            # Obtiene atributos de respuesta importantes
            full_address = result.get("formatted_address")
            latitude = result["geometry"]["location"]["lat"]
            longitude = result["geometry"]["location"]["lng"]
            quality_score = result.get(
                "location_type"
            )  # Campo que se asigna para darle SCORE al resultado

            # Busca o crea la dirección en la tabla 'address'
            address_record = (
                self.session.query(Address).filter_by(full_address=full_address).first()
            )
            if not address_record:
                address_record = Address(full_address=full_address)
                self.session.add(address_record)
                self.session.commit()

            # Registrar en la tabla `AddressScore`
            address_score = AddressScore(
                address_id=address_record.id,
                score=quality_score,  # Podría ajustarse según tus necesidades
            )
            self.session.add(address_score)

            # Registrar en la tabla `ApiResponse`
            api_response = ApiResponse(
                type_api_id=1,  # Suponiendo que '1' corresponde a Google Maps en `type_api_geocord`
                address_id=address_record.id,
                attribute_name="coordinates",
                attribute_value=f"Lat: {latitude}, Lng: {longitude}",
                created_at=datetime.now(),
            )
            self.session.add(api_response)

            # Registrar en la tabla `ApiLogs`
            api_log = ApiLogs(
                api_response_id=api_response.id,
                address_id=address_record.id,
                request_payload=request_payload,
                response_payload=response_data,
                created_at=datetime.now(),
                status_code=status_code,
                response_time_ms=response_time,
            )
            self.session.add(api_log)

            # Confirmar los cambios en la base de datos
            self.session.commit()
            self.session.close()

    def _log_error(
        self,
        address: str,
        request_payload: dict,
        error_message: str,
        status_code: int,
        response_time: int,
    ):
        # Función auxiliar para registrar errores en la tabla ApiLogs
        api_log = ApiLogs(
            api_response_id=None,
            address_id=None,
            request_payload=request_payload,
            response_payload={"error": error_message},
            created_at=datetime.now(),
            status_code=status_code,
            response_time_ms=response_time,
        )
        self.session.add(api_log)
        self.session.commit()
