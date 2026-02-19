"""Centralized cache manager for all cache files."""

import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

module = sys.modules[__name__]

_CACHE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== STEP 1: PLAYER IDS =====
_PLAYER_IDS_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "player_ids.json"
)

# ===== STEP 2: WEEKLY DATA =====
_VALID_OPTIONS_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "valid_options_cache.json"
)
_MANAGER_METADATA_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "manager_metadata_cache.json"
)
_TRANSACTION_IDS_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "transaction_ids.json"
)
_WEEKLY_DATA_PROGRESS_TRACKER_FILE = os.path.join(
    _CACHE_DIR,
    "cached_data",
    "progress_trackers",
    "weekly_data_progress_tracker.json",
)

# ===== STEP 3-4: SCORING DATA =====
_REPLACEMENT_SCORE_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "replacement_score_cache.json"
)

# ==== EXPERIMENTAL ====
_PLAYER_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "player_cache.json"
)
_MANAGER_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "manager_cache.json"
)
_TRANSACTION_CACHE_FILE = os.path.join(
    _CACHE_DIR, "cached_data", "transaction_cache.json"
)


class CacheManager:
    """Centralized cache manager for all cache files.

    - Single place to handle all cache I/O
    - Prevents scattered load_cache/save_cache calls throughout the repo
    - Easy to test (mock this instead of file I/O)
    - Consistent interface for all caches

    Usage:
        from patriot_center_backend.cache import CACHE_MANAGER

        # Load caches
        player_ids_cache = cache_mgr.get_player_ids_cache()

        # Save caches
        CACHE_MANAGER.save_player_ids_cache(player_ids_cache)
        or
        CACHE_MANAGER.save_player_ids_cache()
    """

    def __init__(self):
        """Initialize cache manager (caches are loaded lazily on first access).

        In-memory cache storage is initialized lazily. The cache is loaded
        only when accessed for the first time.
        """
        # In-memory cache storage (loaded lazily)
        self._manager_metadata_cache: dict | None = None
        self._transaction_ids_cache: dict | None = None
        self._player_ids_cache: dict | None = None
        self._replacement_score_cache: dict | None = None
        self._valid_options_cache: dict | None = None
        self._weekly_data_progress_tracker: dict | None = None
        self._player_cache: dict | None = None
        self._manager_cache: dict | None = None
        self._transaction_cache: dict | None = None

    # ===== LOADER AND SAVER =====
    def _load_cache(self, file_path: str) -> dict[str, Any]:
        """Load JSON cache from the specified file path.

        If the file does not exist, return an empty dictionary.

        Args:
            file_path: Target path.

        Returns:
            Existing cache or empty dictionary.
        """
        if os.path.exists(file_path):
            with open(file_path) as file:
                return json.load(file)
        else:
            # Return an empty dictionary if the file does not exist
            return {}

    def _save_cache(self, file_path: str, data: dict[str, Any]) -> None:
        """Persist cache to disk using pretty formatting.

        Args:
            file_path: Target path.
            data: Cache content.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    def _delete_cache(self, file_path: str) -> None:
        """Delete cache file.

        Args:
            file_path: Target path.
        """
        if os.path.exists(file_path):
            os.remove(file_path)

    # ===== MANAGER METADATA CACHE =====
    def get_manager_metadata_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get manager metadata cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Manager metadata cache dictionary
        """
        if self._manager_metadata_cache is None or force_reload:
            self._manager_metadata_cache = self._load_cache(
                _MANAGER_METADATA_CACHE_FILE
            )

        if copy:
            return deepcopy(self._manager_metadata_cache)
        return self._manager_metadata_cache

    def save_manager_metadata_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save manager metadata cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no manager cache data to save
        """
        data_to_save = (
            cache if cache is not None else self._manager_metadata_cache
        )

        if data_to_save is None:
            raise ValueError("No manager cache data to save")

        self._save_cache(_MANAGER_METADATA_CACHE_FILE, data_to_save)
        self._manager_metadata_cache = data_to_save

    def _delete_manager_metadata_cache(self) -> None:
        """Delete manager metadata cache file."""
        self._delete_cache(_MANAGER_METADATA_CACHE_FILE)
        self._manager_metadata_cache = None

    # ===== MANAGER CACHE =====
    def get_manager_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get manager cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Manager cache dictionary
        """
        if self._manager_cache is None or force_reload:
            self._manager_cache = self._load_cache(_MANAGER_CACHE_FILE)

        if copy:
            return deepcopy(self._manager_cache)
        return self._manager_cache

    def save_manager_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save manager cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no manager cache data to save
        """
        data_to_save = cache if cache is not None else self._manager_cache

        if data_to_save is None:
            raise ValueError("No manager cache data to save")

        self._save_cache(_MANAGER_CACHE_FILE, data_to_save)
        self._manager_cache = data_to_save

    def _delete_manager_cache(self) -> None:
        """Delete manager cache file."""
        self._delete_cache(_MANAGER_CACHE_FILE)
        self._manager_cache = None

    # ===== TRANSACTION IDS CACHE =====
    def get_transaction_ids_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get transaction IDs cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Transaction IDs cache dictionary
        """
        if self._transaction_ids_cache is None or force_reload:
            self._transaction_ids_cache = self._load_cache(
                _TRANSACTION_IDS_FILE
            )

        if copy:
            return deepcopy(self._transaction_ids_cache)
        return self._transaction_ids_cache

    def save_transaction_ids_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save transaction IDs cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: No transaction IDs cache data to save
        """
        data_to_save = (
            cache if cache is not None else self._transaction_ids_cache
        )

        if data_to_save is None:
            raise ValueError("No transaction IDs cache data to save")

        self._save_cache(_TRANSACTION_IDS_FILE, data_to_save)
        self._transaction_ids_cache = data_to_save

    def _delete_transaction_ids_cache(self) -> None:
        """Delete transaction IDs cache file."""
        self._delete_cache(_TRANSACTION_IDS_FILE)
        self._transaction_ids_cache = None

    # ===== PLAYER IDS CACHE =====
    def get_player_ids_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get player IDs cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Player IDs cache dictionary
        """
        if self._player_ids_cache is None or force_reload:
            self._player_ids_cache = self._load_cache(_PLAYER_IDS_CACHE_FILE)

        if copy:
            return deepcopy(self._player_ids_cache)
        return self._player_ids_cache

    def save_player_ids_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save player IDs cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no player IDs cache data to save
        """
        data_to_save = cache if cache is not None else self._player_ids_cache

        if data_to_save is None:
            raise ValueError("No player IDs cache data to save")

        self._save_cache(_PLAYER_IDS_CACHE_FILE, data_to_save)
        self._player_ids_cache = data_to_save

    def _delete_player_ids_cache(self) -> None:
        """Delete player IDs cache file."""
        self._delete_cache(_PLAYER_IDS_CACHE_FILE)
        self._player_ids_cache = None

    # ===== REPLACEMENT SCORE CACHE =====
    def get_replacement_score_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, Any]:
        """Get replacement score cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Replacement score cache dictionary
        """
        if self._replacement_score_cache is None or force_reload:
            self._replacement_score_cache = self._load_cache(
                _REPLACEMENT_SCORE_CACHE_FILE
            )

        if copy:
            return deepcopy(self._replacement_score_cache)
        return self._replacement_score_cache

    def save_replacement_score_cache(
        self, cache: dict[str, Any] | None = None
    ) -> None:
        """Save replacement score cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no replacement score cache to save
        """
        data_to_save = (
            cache if cache is not None else self._replacement_score_cache
        )

        if data_to_save is None:
            raise ValueError("No replacement score cache to save")

        self._save_cache(_REPLACEMENT_SCORE_CACHE_FILE, data_to_save)
        self._replacement_score_cache = data_to_save

    def _delete_replacement_score_cache(self) -> None:
        """Delete replacement score cache file."""
        self._delete_cache(_REPLACEMENT_SCORE_CACHE_FILE)
        self._replacement_score_cache = None

    # ===== VALID OPTIONS CACHE =====
    def get_valid_options_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get valid options cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Valid options cache dictionary
        """
        if self._valid_options_cache is None or force_reload:
            self._valid_options_cache = self._load_cache(
                _VALID_OPTIONS_CACHE_FILE
            )

        if copy:
            return deepcopy(self._valid_options_cache)
        return self._valid_options_cache

    def save_valid_options_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save valid options cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no valid options cache to save
        """
        data_to_save = cache if cache is not None else self._valid_options_cache

        if data_to_save is None:
            raise ValueError("No valid options cache to save")

        self._save_cache(_VALID_OPTIONS_CACHE_FILE, data_to_save)
        self._valid_options_cache = data_to_save

    def _delete_valid_options_cache(self) -> None:
        """Delete valid options cache file."""
        self._delete_cache(_VALID_OPTIONS_CACHE_FILE)
        self._valid_options_cache = None

    # ===== WEEKLY DATA PROGRESS TRACKER =====
    def get_weekly_data_progress_tracker(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, Any]:
        """Get weekly data progress tracker.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Weekly data progress tracker dictionary
        """
        if self._weekly_data_progress_tracker is None or force_reload:
            self._weekly_data_progress_tracker = self._load_cache(
                _WEEKLY_DATA_PROGRESS_TRACKER_FILE
            )

        if copy:
            return deepcopy(self._weekly_data_progress_tracker)
        return self._weekly_data_progress_tracker

    def save_weekly_data_progress_tracker(
        self, cache: dict[str, Any] | None = None
    ) -> None:
        """Save weekly data progress tracker to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no weekly data progress tracker to save
        """
        data_to_save = (
            cache if cache is not None else self._weekly_data_progress_tracker
        )

        if data_to_save is None:
            raise ValueError("No weekly data progress tracker to save")

        self._save_cache(_WEEKLY_DATA_PROGRESS_TRACKER_FILE, data_to_save)
        self._weekly_data_progress_tracker = data_to_save

    def _delete_weekly_data_progress_tracker(self) -> None:
        """Delete weekly data progress tracker file."""
        self._delete_cache(_WEEKLY_DATA_PROGRESS_TRACKER_FILE)
        self._weekly_data_progress_tracker = None

    # ===== PLAYER CACHE =====
    def get_player_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get player cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            Player cache dictionary
        """
        if self._player_cache is None or force_reload:
            self._player_cache = self._load_cache(_PLAYER_CACHE_FILE)

        if copy:
            return deepcopy(self._player_cache)
        return self._player_cache

    def save_player_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save player cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no player cache to save
        """
        data_to_save = cache if cache is not None else self._player_cache

        if data_to_save is None:
            raise ValueError("No player cache to save")

        self._save_cache(_PLAYER_CACHE_FILE, data_to_save)
        self._player_cache = data_to_save

    def _delete_player_cache(self) -> None:
        """Delete player cache file."""
        self._delete_cache(_PLAYER_CACHE_FILE)
        self._player_cache = None

    # ===== TRANSACTION CACHE =====
    def get_transaction_cache(
        self, force_reload: bool = False, copy: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Get transaction cache.

        Args:
            force_reload: If True, reload from disk
            copy: If True, return a copy of the cache

        Returns:
            transaction cache dictionary
        """
        if self._transaction_cache is None or force_reload:
            self._transaction_cache = self._load_cache(_TRANSACTION_CACHE_FILE)

        if copy:
            return deepcopy(self._transaction_cache)
        return self._transaction_cache

    def save_transaction_cache(
        self, cache: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """Save transaction cache to disk.

        Args:
            cache: Cache to save (uses in-memory cache if not provided)

        Raises:
            ValueError: If no transaction cache to save
        """
        data_to_save = cache if cache is not None else self._transaction_cache

        if data_to_save is None:
            raise ValueError("No transaction cache to save")

        self._save_cache(_TRANSACTION_CACHE_FILE, data_to_save)
        self._transaction_cache = data_to_save

    def _delete_transaction_cache(self) -> None:
        """Delete transaction cache file."""
        self._delete_cache(_TRANSACTION_CACHE_FILE)
        self._transaction_cache = None


    # ===== UTILITY METHODS =====
    def is_cache_stale(
        self, cache_name: str, max_age: timedelta = timedelta(weeks=1)
    ) -> bool:
        """Check if a cache is stale.

        Args:
            cache_name: Name of the cache
            max_age: Maximum age of the cache

        Returns:
            True if the cache is stale, False otherwise

        Raises:
            ValueError: If the cache name is unknown
        """
        file_name = getattr(module, f"_{cache_name.upper()}_CACHE_FILE", None)

        if file_name is None:
            raise ValueError(f"Unknown cache name: {cache_name}")

        # Get the age of the file
        try:
            file_mtime = os.path.getmtime(file_name)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)

        except FileNotFoundError:
            # If file doesn't exist then this needs to run
            return True

        # If file was modified within the last week, reuse it
        return file_age > max_age

    def reload_all_caches(self) -> None:
        """Clear all in-memory caches.

        Clearing the cache forces a reload from disk on next access.
        """
        self._manager_metadata_cache = None
        self._transaction_ids_cache = None
        self._player_ids_cache = None
        self._replacement_score_cache = None
        self._valid_options_cache = None
        self._weekly_data_progress_tracker = None
        self._player_cache = None
        self._manager_cache = None
        self._transaction_cache = None

    def save_all_caches(self) -> None:
        """Save all loaded caches to disk."""
        if self._manager_metadata_cache is not None:
            self.save_manager_metadata_cache()
        if self._transaction_ids_cache is not None:
            self.save_transaction_ids_cache()
        if self._player_ids_cache is not None:
            self.save_player_ids_cache()
        if self._replacement_score_cache is not None:
            self.save_replacement_score_cache()
        if self._valid_options_cache is not None:
            self.save_valid_options_cache()
        if self._weekly_data_progress_tracker is not None:
            self.save_weekly_data_progress_tracker()
        if self._player_cache is not None:
            self.save_player_cache()
        if self._manager_cache is not None:
            self.save_manager_cache()
        if self._transaction_cache is not None:
            self.save_transaction_cache()

    def restart_all_caches(
        self, restart: Literal["partial", "full"]
    ) -> None:
        """Restart all caches except player ids if partial, or all if full.

        Args:
            restart: If "partial", only restart weekly data caches. If "full",
                restart all.
        """
        self._delete_manager_metadata_cache()
        self._delete_transaction_ids_cache()
        self._delete_replacement_score_cache()
        self._delete_valid_options_cache()
        self._delete_weekly_data_progress_tracker()
        self._delete_player_cache()
        self._delete_manager_cache()
        self._delete_transaction_cache()
        if restart == "full":
            self._delete_player_ids_cache()

        self.reload_all_caches()

# ===== SINGLETON INSTANCE =====
# Create a single instance to be imported throughout the repo
_cache_manager_instance = None


def get_cache_manager() -> CacheManager:
    """Get the singleton CacheManager instance.

    This ensures only one CacheManager exists throughout the application.

    Returns:
        CacheManager instance
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance
