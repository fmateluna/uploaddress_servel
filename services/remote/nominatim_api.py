import requests


class NominatimAPI:
    def get_geolocation(self, address: str) -> dict:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
