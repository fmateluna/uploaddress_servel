import asyncio
from fastapi.encoders import jsonable_encoder
from repositories.address_repo import AddressRepository
from repositories.database import get_session
from repositories.models import Address
from repositories.report_repo import fetch_address_details
from services.remote.geolocation_service import GeolocationService


class DataService:

    def __init__(self):
        self.session = get_session()

    async def process_address(self, api_name: str, address: str):
        geo_service = GeolocationService(api_name)
        geolocation_data = await geo_service.get_geolocation(
            address
        )  # Asegúrate de que esta función sea async
        return geolocation_data

    async def _save_address(self, address: str, remote_ip: str):
        # Verificar si la dirección ya existe
        existing_address = (
            self.session.query(Address)
            .filter_by(full_address=address, input_type_id=8)
            .first()
        )

        # Si no existe, proceder a agregarla
        if not existing_address:
            address_from_endpoint = Address(
                full_address=address, input_type_id=8, ip_address=remote_ip
            )
            self.session.add(address_from_endpoint)
            self.session.commit()  # Confirmar los cambios en la base de datos
            print(f"Address '{address}' registrada exitosamente.")
        else:
            print(f"Address '{address}' ya existe en la base de datos.")

    async def generate_info_address(self, address: str, remote_ip: str):

        await self._save_address(address, remote_ip)

        # Ejecutar ambas llamadas a process_address en paralelo, ignorando errores individuales
        results = await asyncio.gather(
            self.process_address("google", address=address),
            self.process_address("nominatim", address=address),
            return_exceptions=True,
        )

        # Procesar los resultados, verificando si hubo excepciones
        for result in results:
            if isinstance(result, Exception):
                print(f"Error en una de las APIs: {result}")

        result = fetch_address_details(address)
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
