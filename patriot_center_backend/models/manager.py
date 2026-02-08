"""Manager class."""

from copy import deepcopy
from time import time
from typing import Any, ClassVar

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.sleeper_helpers import fetch_user_metadata


class Manager:
    """Manager class."""

    _instances: ClassVar[dict[str, "Manager"]] = {}

    def __new__(cls, user_id: str) -> "Manager":
        """Create a new manager instance or return the existing one.

        Args:
            user_id: The user ID of the manager

        Returns:
            The manager instance
        """
        if user_id in cls._instances:
            return cls._instances[user_id]
        instance = super().__new__(cls)
        cls._instances[user_id] = instance
        return instance

    def __init__(self, user_id: str) -> None:
        """Manager class.

        Args:
            user_id: The user ID of the manager
        """
        if hasattr(self, "_initialized"):
            return  # Already initialized
        self._initialized = True

        self.user_id = user_id

        self._load_from_cache()

    def __str__(self) -> str:
        """String representation of the manager.

        Returns:
            The user ID of the manager
        """
        return self.user_id

    def _load_from_cache(self) -> None:
        """Loads manager data from cache."""
        manager_cache = CACHE_MANAGER.get_manager_cache()

        # Get manager data
        manager_data = deepcopy(manager_cache.get(self.user_id, {}))

        self._overall_data: dict[str, Any] = manager_data.get(
            "overall_data", {}
        )
        self._data: dict[str, dict[str, Any]] = manager_data.get("data", {})
        self._summary: dict[str, Any] = manager_data.get("summary", {})

        self._fetch_and_apply_user_metadata(initial=True)

        self._apply_to_cache()


    def _apply_to_cache(self) -> None:
        """Applies the manager data to the cache."""
        manager_cache = CACHE_MANAGER.get_manager_cache()

        manager_cache[self.user_id] = {
            "real_name": self.real_name,  # Not read but used for display
            "overall_data": deepcopy(self._overall_data),
            "data": deepcopy(self._data),
            "summary": deepcopy(self._summary),
        }

    def _fetch_and_apply_user_metadata(self, initial: bool = False) -> None:
        """Fetches and applies user metadata to the manager.

        Args:
            initial: If True, skips user metadata fetch if it is less than an
                hour old.
        """
        # If manager has been updated within the last hour, skip
        if not initial and self._time_updated + 3600 > time():
            return

        user_metadata = fetch_user_metadata(self.user_id, bypass_cache=True)

        self.username = user_metadata["display_name"]
        self.image_url = (
            f"https://sleepercdn.com/avatars/{user_metadata['avatar']}"
        )

        # TODO: change to cached data and make dynamic with user entry
        if self.username in USERNAME_TO_REAL_NAME:
            self.real_name = USERNAME_TO_REAL_NAME[self.username]
        else:
            self.real_name = self.username

        self._time_updated = time()
