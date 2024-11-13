from fastapi.encoders import jsonable_encoder
from repositories.address_repo import AddressRepository
from repositories.report_repo import fetch_address_details
from services.remote.geolocation_service import GeolocationService


class DataService:

    def process_address(self, api_name: str, address: str):
        geo_service = GeolocationService(api_name)
        geolocation_data = geo_service.get_geolocation(address)
        return geolocation_data

    def get_all_info_from_address(self, address: str):
        result = fetch_address_details(address)
        if result:
            # Convertir el diccionario a un formato JSON serializable
            return jsonable_encoder(result)
        else:
            return {
                "message": "No se encontraron datos para la dirección especificada."
            }
