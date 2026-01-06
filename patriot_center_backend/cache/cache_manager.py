"""
Central cache management for Patriot Center backend.

This is the ONLY place where cache files should be loaded or saved.
All other code should use CacheManager methods instead of calling load_cache/save_cache directly.

Single Responsibility: Manage all cache file I/O operations.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from patriot_center_backend.constants import LEAGUE_IDS


_CACHE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== WEEKLY DATA =====
PLAYERS_CACHE_FILE             = os.path.join(_CACHE_DIR, "cached_data", "players_cache.json")
REPLACEMENT_SCORE_CACHE_FILE   = os.path.join(_CACHE_DIR, "cached_data", "replacement_score_cache.json")
STARTERS_CACHE_FILE            = os.path.join(_CACHE_DIR, "cached_data", "starters_cache.json")
PLAYERS_DATA_CACHE_FILE        = os.path.join(_CACHE_DIR, "cached_data", "player_data_cache.json")
VALID_OPTIONS_CACHE_FILE       = os.path.join(_CACHE_DIR, "cached_data", "valid_options_cache.json")

# ===== MANAGER METADATA =====
MANAGER_METADATA_CACHE_FILE    = os.path.join(_CACHE_DIR, "cached_data", "manager_metadata_cache.json")
TRANSACTION_IDS_FILE           = os.path.join(_CACHE_DIR, "cached_data", "transaction_ids.json")

# ===== SLEEPER PLAYER IDS =====
PLAYER_IDS_CACHE_FILE          = os.path.join(_CACHE_DIR, "cached_data", "player_ids.json")


class CacheManager:
    """
    Centralized cache manager for all cache files.
    
    Why this exists:
    - Single place to handle all cache I/O
    - Prevents scattered load_cache/save_cache calls throughout the repo
    - Easy to test (mock this instead of file I/O)
    - Consistent interface for all caches
    
    Usage:
        cache_mgr = CacheManager()
        
        # Load caches
        manager_cache = cache_mgr.get_manager_cache()
        starters = cache_mgr.get_starters_cache()
        
        # Save caches
        cache_mgr.save_manager_cache(manager_cache)
        cache_mgr.save_starters_cache(starters)
    """
    
    def __init__(self):
        """Initialize cache manager (caches are loaded lazily on first access)."""
        # In-memory cache storage (loaded lazily)
        self._manager_cache: Optional[Dict] = None
        self._transaction_ids_cache: Optional[Dict] = None
        self._players_cache: Optional[Dict] = None
        self._player_ids_cache: Optional[Dict] = None
        self._starters_cache: Optional[Dict] = None
        self._player_data_cache: Optional[Dict] = None
        self._replacement_score_cache: Optional[Dict] = None
        self._valid_options_cache: Optional[Dict] = None
    

    # ===== LOADER AND SAVER =====

    def _load_cache(self, file_path: str) -> Dict [str, Any]:
        """
        Load JSON cache or initialize baseline structure.

        Returns:
            dict: Existing cache or empty Dict.
        """
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        
        return {}
    
    def _save_cache(self, file_path: str, data: Dict[str, Any]) -> None:
        """
        Persist cache to disk using pretty formatting.

        Args:
            file_path (str): Target path.
            data (dict): Cache content.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    
    # ===== MANAGER METADATA CACHE =====
    
    def get_manager_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get manager metadata cache.
        
        Args:
            force_reload: If True, reload from disk (ignores in-memory cache)
        
        Returns:
            Manager metadata cache dictionary
        """
        if self._manager_cache is None or force_reload:
            self._manager_cache = self._load_cache(MANAGER_METADATA_CACHE_FILE)
        
        return self._manager_cache
    
    def save_manager_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save manager metadata cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._manager_cache
        
        if data_to_save is None:
            raise ValueError("No manager cache data to save")
        
        self._save_cache(MANAGER_METADATA_CACHE_FILE, data_to_save)
        self._manager_cache = data_to_save
    
    def update_manager_cache(self, cache: Dict[str, Any]) -> None:
        """
        Update the in-memory manager cache (does not save to disk).
        
        Args:
            cache: New cache data
        """
        self._manager_cache = cache
    
    # ===== TRANSACTION IDS CACHE =====
    
    def get_transaction_ids_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get transaction IDs cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Transaction IDs cache dictionary
        """
        if self._transaction_ids_cache is None or force_reload:
            self._transaction_ids_cache = self._load_cache(TRANSACTION_IDS_FILE)
        
        return self._transaction_ids_cache
    
    def save_transaction_ids_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save transaction IDs cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._transaction_ids_cache
        
        if data_to_save is None:
            raise ValueError("No transaction IDs cache data to save")
        
        self._save_cache(TRANSACTION_IDS_FILE, data_to_save)
        self._transaction_ids_cache = data_to_save
    
    def update_transaction_ids_cache(self, cache: Dict[str, Any]) -> None:
        """Update the in-memory transaction IDs cache (does not save to disk)."""
        self._transaction_ids_cache = cache
    
    # ===== PLAYERS CACHE =====
    
    def get_players_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get players cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Players cache dictionary
        """
        if self._players_cache is None or force_reload:
            self._players_cache = self._load_cache(PLAYERS_CACHE_FILE)
        
        return self._players_cache
    
    def save_players_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save players cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._players_cache
        
        if data_to_save is None:
            raise ValueError("No players cache data to save")
        
        self._save_cache(PLAYERS_CACHE_FILE, data_to_save)
        self._players_cache = data_to_save
    
    # ===== PLAYER IDS CACHE =====
    
    def get_player_ids_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get player IDs cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Player IDs cache dictionary
        """
        if self._player_ids_cache is None or force_reload:
            self._player_ids_cache = self._load_cache(PLAYER_IDS_CACHE_FILE)
        
        return self._player_ids_cache
    
    def is_player_ids_cache_stale(self) -> bool:
        # Check file modification time to determine if cache is stale
        try:
            file_mtime = os.path.getmtime(PLAYER_IDS_CACHE_FILE)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)
        except FileNotFoundError:
            # If file doesn't exist then this needs to run
            return True
        # If file was modified within the last week, reuse it
        if file_age > timedelta(weeks=1):
            return True
        
        return False
    
    def save_player_ids_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save player IDs cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._player_ids_cache
        
        if data_to_save is None:
            raise ValueError("No player IDs cache data to save")
        
        self._save_cache(PLAYER_IDS_CACHE_FILE, data_to_save)
        self._player_ids_cache = data_to_save
    
    # ===== STARTERS CACHE =====
    
    def get_starters_cache(self, force_reload: bool = False, for_update = False) -> Dict[str, Any]:
        """
        Get starters cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Starters cache dictionary
        """
        if self._starters_cache is None or force_reload:
            self._starters_cache = self._load_cache(STARTERS_CACHE_FILE)
        
        if for_update:
            if self._starters_cache == {}:
                # Initialize the cache with all years
                self._starters_cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}

                # Initialize an empty dict for each season
                for year in list(LEAGUE_IDS.keys()):
                    self._starters_cache[str(year)] = {}
        
        # Remove metadata fields if we're not using this data to update
        else:
            self._starters_cache.pop("Last_Updated_Season", None)
            self._starters_cache.pop("Last_Updated_Week", None)

        return self._starters_cache
    
    def save_starters_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save starters cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._starters_cache
        
        if data_to_save is None:
            raise ValueError("No starters cache data to save")
        
        self._save_cache(STARTERS_CACHE_FILE, data_to_save)
        self._starters_cache = data_to_save
    
    # ===== PLAYER DATA CACHE (ffWAR) =====
    
    def get_player_data_cache(self, force_reload: bool = False, for_update: bool = False) -> Dict[str, Any]:
        """
        Get player data cache (ffWAR data).
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Player data cache dictionary
        """
        if self._player_data_cache is None or force_reload:
            self._player_data_cache = self._load_cache(PLAYERS_DATA_CACHE_FILE)

        if for_update:
            if self._player_data_cache == {}:
                # Initialize the cache with all years
                self._player_data_cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}

                # Initialize an empty dict for each season
                for year in list(LEAGUE_IDS.keys()):
                    self._player_data_cache[str(year)] = {}
        
        # Remove metadata fields if we're not using this data to update
        else:
            self._player_data_cache.pop("Last_Updated_Season", None)
            self._player_data_cache.pop("Last_Updated_Week", None)
        
        return self._player_data_cache
    
    def save_player_data_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save player data cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._player_data_cache
        
        if data_to_save is None:
            raise ValueError("No player data cache to save")
        
        self._save_cache(PLAYERS_DATA_CACHE_FILE, data_to_save)
        self._player_data_cache = data_to_save
    
    # ===== REPLACEMENT SCORE CACHE =====
    
    def get_replacement_score_cache(self, force_reload: bool = False, for_update: bool = False) -> Dict[str, Any]:
        """
        Get replacement score cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Replacement score cache dictionary
        """
        if self._replacement_score_cache is None or force_reload:
            self._replacement_score_cache = self._load_cache(REPLACEMENT_SCORE_CACHE_FILE)

        
        if for_update:
            if self._replacement_score_cache == {}:
                # If the cache is empty then initialize it with all years (plus historical years for replacement score caches)
                self._replacement_score_cache  = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
                
                years = list(LEAGUE_IDS.keys())
                
                # For replacement score caches, backfill extra seasons to compute multi-year averages
                # Extend years list with prior 3 years (supports 3yr average calc)
                first_year = min(years)
                years.extend([first_year - 3, first_year - 2, first_year - 1])
                years = sorted(years)

                # Initialize an empty dict for each season
                for year in years:
                    self._replacement_score_cache [str(year)] = {}
        
        # Remove metadata fields if we're not using this data to update
        else:
            self._replacement_score_cache.pop("Last_Updated_Season", None)
            self._replacement_score_cache.pop("Last_Updated_Week", None)
        
        return self._replacement_score_cache
    
    def save_replacement_score_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save replacement score cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._replacement_score_cache
        
        if data_to_save is None:
            raise ValueError("No replacement score cache to save")
        
        self._save_cache(REPLACEMENT_SCORE_CACHE_FILE, data_to_save)
        self._replacement_score_cache = data_to_save
    
    # ===== VALID OPTIONS CACHE =====
    
    def get_valid_options_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get valid options cache.
        
        Args:
            force_reload: If True, reload from disk
        
        Returns:
            Valid options cache dictionary
        """
        if self._valid_options_cache is None or force_reload:
            self._valid_options_cache = self._load_cache(VALID_OPTIONS_CACHE_FILE)
        
        return self._valid_options_cache
    
    def save_valid_options_cache(self, cache: Optional[Dict] = None) -> None:
        """
        Save valid options cache to disk.
        
        Args:
            cache: Cache to save (uses in-memory cache if not provided)
        """
        data_to_save = cache if cache is not None else self._valid_options_cache
        
        if data_to_save is None:
            raise ValueError("No valid options cache to save")
        
        self._save_cache(VALID_OPTIONS_CACHE_FILE, data_to_save)
        self._valid_options_cache = data_to_save
    
    # ===== UTILITY METHODS =====
    
    def reload_all_caches(self) -> None:
        """Force reload all caches from disk (clears in-memory caches)."""
        self._manager_cache = None
        self._transaction_ids_cache = None
        self._players_cache = None
        self._player_ids_cache = None
        self._starters_cache = None
        self._player_data_cache = None
        self._replacement_score_cache = None
        self._valid_options_cache = None
    
    def save_all_caches(self) -> None:
        """Save all loaded caches to disk."""
        if self._manager_cache is not None:
            self.save_manager_cache()
        if self._transaction_ids_cache is not None:
            self.save_transaction_ids_cache()
        if self._players_cache is not None:
            self.save_players_cache()
        if self._player_ids_cache is not None:
            self.save_player_ids_cache()
        if self._starters_cache is not None:
            self.save_starters_cache()
        if self._player_data_cache is not None:
            self.save_player_data_cache()
        if self._replacement_score_cache is not None:
            self.save_replacement_score_cache()
        if self._valid_options_cache is not None:
            self.save_valid_options_cache()


# ===== SINGLETON INSTANCE =====
# Create a single instance to be imported throughout the repo
_cache_manager_instance = None

def get_cache_manager() -> CacheManager:
    """
    Get the singleton CacheManager instance.
    
    This ensures only one CacheManager exists throughout the application.
    
    Returns:
        CacheManager instance
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance