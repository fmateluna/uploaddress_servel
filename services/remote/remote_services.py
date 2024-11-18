from repositories.report_repo import fetch_address_details
from services.remote.geo_factory import GeoAPIFactory


class GeolocationService:
    def __init__(self, api_name: str):
        self.geo_api = GeoAPIFactory.create_geo_api(api_name)

    def get_geolocation(self, address: str) -> dict:
        return self.geo_api.get_geolocation(address, False)

    def get_all_info(self, address: str) -> dict:
        result = fetch_address_details(address)
        if result:
            return result
        else:
            return {}
