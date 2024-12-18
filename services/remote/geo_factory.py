from services.remote.google_maps_api import GoogleMapsAPI
from services.remote.localidades import LocalidadesAPI
from services.remote.nominatim_api import NominatimAPI


class GeoAPIFactory:
    @staticmethod
    def create_geo_api(api_name: str):
        if api_name == "Google":
            return GoogleMapsAPI()
        elif api_name == "Nominatim":
            return NominatimAPI()
        elif api_name == "Localidades":
            return LocalidadesAPI()
        else:
            raise ValueError(f"API '{api_name}' no es soportada.")
