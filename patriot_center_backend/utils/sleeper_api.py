"""This module provides a client for interacting with the Sleeper API."""

from typing import Any

import requests

SLEEPER_API_URL = "https://api.sleeper.app/v1"


class SleeperApiClient:
    """A client for interacting with the Sleeper API."""
    def __init__(self):
        """Initialize the Sleeper API client."""
        self._cache: dict[str, Any] = {}

    def fetch(
        self, endpoint: str, bypass_cache: bool = False
    ) -> dict[str, Any] | list[Any]:
        """Fetch data from the Sleeper API.

        Args:
            endpoint: The endpoint to call on the Sleeper API.
            bypass_cache: Whether to bypass the cache.

        Returns:
            The parsed JSON response from the Sleeper API.

        Raises:
            ConnectionAbortedError: If the request to the Sleeper API fails.
        """
        if endpoint not in self._cache or bypass_cache:
            data = requests.get(f"{SLEEPER_API_URL}/{endpoint}")

            if data.status_code != 200:
                raise ConnectionAbortedError(
                    f"Failed to fetch data from "
                    f"Sleeper API with call to {endpoint}"
                )

            # Return parsed JSON
            self._cache[endpoint] = data.json()

        return self._cache[endpoint]

    def clear_cache(self):
        """Clear the cache."""
        self._cache = {}


_client_instance = None

def get_sleeper_client() -> SleeperApiClient:
    """Get the singleton SleeperApiClient instance.

    This ensures only one SleeperApiClient exists throughout the application.

    Returns:
        SleeperApiClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = SleeperApiClient()
    return _client_instance

SLEEPER_CLIENT = get_sleeper_client()
