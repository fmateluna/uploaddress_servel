from repositories.address_repo import AddressRepository
from services.remote.geolocation_service import GeolocationService


class DataService:

    def process_address(self, api_name: str, address: str):
        geo_service = GeolocationService(api_name)
        geolocation_data = geo_service.get_geolocation(address)
        # Almacenar datos en la base de datos
        # self.address_repo.save_geolocation(geolocation_data)
        return geolocation_data
