from services.remote.google_maps_api import GoogleMapsAPI
from services.remote.nominatim_api import NominatimAPI


class GeoAPIFactory:
    @staticmethod
    def create_geo_api(api_name: str):
        if api_name == "google":
            return GoogleMapsAPI()
        elif api_name == "nominatim":
            return NominatimAPI()
        else:
            raise ValueError(f"API '{api_name}' no es soportada.")