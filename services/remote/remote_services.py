from services.remote.geo_factory import GeoAPIFactory


class GeolocationService:
    def __init__(self, api_name: str):
        self.geo_api = GeoAPIFactory.create_geo_api(api_name)

    def get_geolocation(self, address: str) -> dict:
        return self.geo_api.get_geolocation(address)
