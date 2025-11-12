import requests
import patriot_center_backend.constants as consts

def fetch_sleeper_data(endpoint: str):
    url = f"{consts.SLEEPER_API_URL}/{endpoint}"
    response = requests.get(url)
    if response.status_code != 200:
        error_string = f"Failed to fetch data from Sleeper API with call to {url}"
        return {"error": error_string}, 500

    return response.json(), 200