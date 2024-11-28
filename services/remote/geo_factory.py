from repositories.report_repo import fetch_address_details
from services.remote.common import ResponseGeo
from services.remote.google_maps_api import GoogleMapsAPI
from services.remote.servel import ServelDataBase
from services.remote.nominatim_api import NominatimAPI


class GeolocationService:
    def __init__(self, api_name: str):
        self.geo_api = GeoAPIFactory.create_geo_api(api_name)

    def get_geolocation(self, address: str) -> ResponseGeo:
        return self.geo_api.get_geolocation(address)

    def get_all_info(self, address: str) -> dict:
        result = fetch_address_details(address)
        if result:
            return result
        else:
            return {}


class GeoAPIFactory:
    @staticmethod
    def create_geo_api(api_name: str):
        if api_name == "Google":
            return GoogleMapsAPI()
        elif api_name == "Nominatim":
            return NominatimAPI()
        elif api_name == "Servel":
            return ServelDataBase()
        else:
            raise ValueError(f"API '{api_name}' no es soportada.")
