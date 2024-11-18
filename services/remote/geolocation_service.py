from repositories.models import Address
from services.remote.geo_factory import GeoAPIFactory


class GeoResponse:
    def __init__(self) -> None:
        address = Address()
        self.address = address


class GeolocationService:
    def __init__(self, api_name: str):
        self.geo_api = GeoAPIFactory.create_geo_api(api_name)

    async def get_geolocation(self, address: str) -> dict:
        return self.geo_api.get_geolocation(address, False)
