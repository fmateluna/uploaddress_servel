from repositories.address_repo import AddressRepository
from repositories.report_repo import fetch_address_details
from services.remote.geolocation_service import GeolocationService


class DataService:

    def process_address(self, api_name: str, address: str):
        geo_service = GeolocationService(api_name)
        geolocation_data = geo_service.get_geolocation(address)
        # TODO : Definir un response que retorne todo el trabajo hecho.
        # TODO : Diferenciar si existe un parametro de geocoding.
        # Almacenar datos en la base de datos
        # self.address_repo.save_geolocation(geolocation_data)
        return geolocation_data

    def get_all_info_from_address(self, address: str):
        result = fetch_address_details(address)
        return result
