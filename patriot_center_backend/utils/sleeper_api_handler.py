"""Thin HTTP client for Sleeper API.

Provides a single helper to fetch JSON from Sleeper endpoints, normalizing
success/error responses for upstream utilities.
"""
import requests
import patriot_center_backend.constants as consts

def fetch_sleeper_data(endpoint: str):
    """
    Fetch JSON from a Sleeper API endpoint.

    Args:
        endpoint (str): Endpoint path appended to base URL (e.g., "league/{id}").

    Returns:
        tuple: (payload: dict|list|{"error": str}, status_code: int)
               Returns 200 with parsed JSON on success, otherwise ({"error": ...}, 500).

    Notes:
        - This function does not raise exceptions for HTTP errors; it returns a (payload, code) tuple.
        - Callers should check status_code and branch accordingly.
    """
    # Construct full URL from configured base and endpoint
    url = f"{consts.SLEEPER_API_URL}/{endpoint}"
    response = requests.get(url)
    if response.status_code != 200:
        # Normalize error shape for consistent downstream handling
        error_string = f"Failed to fetch data from Sleeper API with call to {url}"
        return {"error": error_string}, 500

    # Return parsed JSON along with success status
    return response.json(), 200