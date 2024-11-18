import asyncio
from fastapi.encoders import jsonable_encoder
from repositories.address_repo import AddressRepository
from repositories.database import get_session
from repositories.models import Address
from repositories.report_repo import fetch_address_details, fetch_report_by_process_id
from services.remote.geolocation_service import GeolocationService


class DataService:

    def __init__(self):
        self.session = get_session()
        self.new_address = False

    async def process_address(self, api_name: str, address: str,new_address: bool = False):
        self.new_address = new_address
        geo_service = GeolocationService(api_name)
        geolocation_data = await geo_service.get_geolocation(
            address
        )  
        return geolocation_data

    async def _save_address(self, address: str, remote_ip: str):
        if self.new_address:
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

    async def generate_info_address(self, address: str, remote_ip: str, new_address: bool = False):
        if new_address:
            await self._save_address(address, remote_ip)

        # Ejecutar ambas llamadas a process_address en paralelo, ignorando errores individuales
        results = await asyncio.gather(
            self.process_address("google", address=address, new_address=new_address),
            self.process_address("nominatim", address=address,new_address=new_address),
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
            
    def report(self, process_id: str):
        result = fetch_report_by_process_id(process_id)
        if result:
            # Convertir el diccionario a un formato JSON serializable
            return jsonable_encoder(result)
        else:
            return {
                "message": "No se encontraron datos para la dirección especificada."
            }            
