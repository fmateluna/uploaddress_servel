import asyncio
from fastapi.encoders import jsonable_encoder
from repositories.address_repo import AddressRepository
from repositories.database import get_session
from repositories.models import Address
from repositories.report_repo import fetch_address_details, fetch_report_by_process_id
from services.remote.geo_factory import GeolocationService
from services.remote.common import ResponseGeo


class DataService:

    def __init__(self):
        self.session = get_session()
        self.addres_repo = AddressRepository(self.session)

    def process_address(self, api_name: str, address: str) -> ResponseGeo:
        geo_service = GeolocationService(api_name)
        response_geo = geo_service.get_geolocation(address)
        return response_geo

    # Procesar las direcciones de forma secuencial
    def process_sequentially(self, address_record):
        responses = {}

        try:
            # Ejecutar Servel
            servel_result = self.process_address("Servel", address=address_record)

            responses["Servel"] = servel_result
            if servel_result.origen != "":
                print(f"Respuesta de Servel: {servel_result.address}")
            else:
                # Ejecutar Nominatim
                nominatim_result = self.process_address(
                    "Nominatim", address=address_record
                )
                responses["Nominatim"] = nominatim_result
                print(f"Respuesta de Nominatim: {nominatim_result.address}")

            """
            # Ejecutar Google
            google_result =  self.process_address("Google", address=address_record)
            responses["Google"] = google_result
            print(f"Respuesta de Google: {google_result}")
            """
        except Exception as e:
            print(f"Error durante la ejecución de las APIs: {e}")

        return responses

    async def generate_info_address(self, address_id: int):

        address_record = self.addres_repo.get_address_by_id(address_id)

        # TODO : Ir en secuencias segun resultado
        # Ejecutar todas las llamadas a process_address en paralelo, ignorando errores individuales

        responses = self.process_sequentially(address_record)

        """
        #Forma antigua de ejecutar, se conserva en caso de volver
        results =  asyncio.gather(
            self.process_address("Google", address=address_record),
            self.process_address("Nominatim", address=address_record),
            self.process_address("Servel", address=address_record),
            return_exceptions=True,
        )

        # Procesar los resultados, verificando si hubo excepciones
        for result in results:
            if isinstance(result, Exception):
                print(f"Error en una de las APIs: {result}")
        """

        result = fetch_address_details(address_record.full_address)
        if result:
            return jsonable_encoder(result)
        else:
            return {
                "message": "No se encontraron datos para la dirección especificada."
            }

    def get_all_info_from_address(self, address: str):
        result = fetch_address_details(address)
        if result:
            # Convertir el diccionario a un formato JSON serializable
            return jsonable_encoder(result)
        else:
            return {
                "message": "No se encontraron datos para la dirección especificada."
            }

    def report(self, process_id: str):
        result = fetch_report_by_process_id(process_id)
        if result:
            # Convertir el diccionario a un formato JSON serializable
            return jsonable_encoder(result)
        else:
            return {
                "message": "No se encontraron datos para la dirección especificada."
            }
