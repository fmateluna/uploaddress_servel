import os
import requests
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import time

from repositories.address_score_repo import insert_or_update_address_score
from repositories.database import get_session
from repositories.models import Address, AddressScore, ApiLogs, ApiResponseValues

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class GoogleMapsAPI:
    def __init__(self):
        self.session = get_session()

    def _save_api_response_attribute(
        self,
        address_id,
        attribute_name,
        attribute_value,
        api_logs_id,
    ):
        api_response = ApiResponseValues(
            type_api_id=1,
            api_logs_id=api_logs_id,
            address_id=address_id,
            attribute_name=attribute_name,
            attribute_value=str(attribute_value),
        )
        self.session.add(api_response)

    def get_geolocation(self, address: str, update: bool = False) -> dict:
        # Verifica si ya existe una entrada para la dirección en la base de datos
        address_record = (
            self.session.query(Address).filter_by(full_address=address).first()
        )

        # Si existe y no se solicita una actualización, se devuelve el último response almacenado
        if address_record and not update:
            print(
                "Usando la respuesta en caché de la base de datos para evitar el uso de tokens."
            )
            api_response = (
                self.session.query(ApiLogs)
                .filter_by(address_id=address_record.id, type_api_id=1)
                .first()
            )
            if api_response:
                return api_response.response_payload

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
            self._log_error(params, str(e), 500, 0)
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
        original_address: str,
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

            """
            ROOFTOP: Alta precisión; la ubicación está directamente en la dirección específica.
            RANGE_INTERPOLATED: Dirección aproximada; generalmente obtenida a partir de interpolación entre dos puntos conocidos en la calle.
            GEOMETRIC_CENTER: Exactitud media; el punto está en el centro geométrico de una zona (como una calle o vecindario).
            APPROXIMATE: Baja precisión; es una ubicación aproximada, posiblemente solo a nivel de ciudad o región.
            """

            quality_score = result["geometry"].get("location_type")

            try:
                # Busca o crea la dirección en la tabla 'address'
                address_record = (
                    self.session.query(Address)
                    .filter_by(full_address=original_address)
                    .first()
                )
                if not address_record:
                    address_record = Address(full_address=full_address)
                    self.session.add(address_record)
                    self.session.flush()

                # Registrar en la tabla `AddressScore`
                insert_or_update_address_score(address_record.id, "Google", quality_score)

                # Definir los atributos importantes a extraer del response de Nominatim

                # Registrar en la tabla `ApiLogs`
                api_log = ApiLogs(
                    address_id=address_record.id,
                    request_payload=request_payload,
                    response_payload=response_data,
                    created_at=datetime.now(),
                    status_code=status_code,
                    response_time_ms=response_time,
                )
                self.session.add(api_log)
                self.session.flush()

                latitude = result["geometry"]["location"]["lat"]
                longitude = result["geometry"]["location"]["lng"]

                # Usar el método auxiliar para guardar los atributos en `ApiResponse`
                # address_id, attribute_name, attribute_value, created_at, api_logs_id
                self._save_api_response_attribute(
                    address_record.id, "latitud", latitude, api_log.id
                )
                self._save_api_response_attribute(
                    address_record.id, "longitude", longitude, api_log.id
                )
                self._save_api_response_attribute(
                    address_record.id, "address", full_address, api_log.id
                )

                # Confirmar los cambios en la base de datos
                self.session.commit()

            except SQLAlchemyError as e:
                # Deshacer cambios en la sesión si ocurre algún error
                self.session.rollback()
                # Opcional: Loggear el error o manejarlo según tus necesidades
                print(f"Error al hacer commit en la base de datos: {e}")
                # Puedes lanzar la excepción nuevamente si necesitas que el error se propague
                raise

    def _log_error(
        self,
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
