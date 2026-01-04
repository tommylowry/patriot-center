"""
Central manager metadata orchestration.

This is the ONLY place where manager metadata operations should be coordinated.
All other code should use ManagerMetadataManager methods.

Single Responsibility: Orchestrate sub-processors and manage persistence.
"""
from copy import deepcopy
from typing import Dict, Optional, List

from patriot_center_backend.cache.cache_manager import get_cache_manager
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data

from patriot_center_backend.managers.templates import initialize_summary_templates, initialize_faab_template
from patriot_center_backend.managers.transaction_processor import TransactionProcessor
from patriot_center_backend.managers.matchup_processor import MatchupProcessor
from patriot_center_backend.managers.data_exporter import DataExporter
from patriot_center_backend.managers.utilities import update_players_cache
from patriot_center_backend.managers.validators import validate_caching_preconditions
from patriot_center_backend.managers.formatters import get_season_state


class ManagerMetadataManager:
    """
    Main orchestrator for manager metadata operations.
    
    Coordinates between:
    - TransactionProcessor: Handles transaction processing
    - MatchupProcessor: Handles matchup/playoff processing
    - DataExporter: Provides public read API
    - CacheManager: Handles persistence
    """
    
    def __init__(self):
        # Get cache manager instance
        self._cache_mgr = get_cache_manager()
        
        # Load caches
        self._cache = self._cache_mgr.get_manager_cache()
        if not self._cache:
            self._cache = {}
        
        # Configuration state
        self._use_faab: Optional[bool] = None
        self._playoff_week_start: Optional[int] = None
        
        # Initialize templates
        self._templates = {}  # Will be set when use_faab is known
        
        # Session state
        self._year: Optional[str] = None
        self._week: Optional[str] = None
        self._weekly_roster_ids: Dict[int, str] = {}
        self._playoff_roster_ids: Dict[int, str] = {}
        
        # External data caches
        self._player_ids            = self._cache_mgr.get_player_ids_cache()
        self._transaction_ids_cache = self._cache_mgr.get_transaction_ids_cache()
        self._players_cache         = self._cache_mgr.get_players_cache()
        self._valid_options_cache   = self._cache_mgr.get_valid_options_cache()
        self._starters_cache        = self._cache_mgr.get_starters_cache()

        # Initialize data_exporter subprocesser
        #   NOTE: all data stays the same unless an update occurs in which case the
        #   initialization of this file is re-ran by the api controller)
        self._data_exporter = DataExporter(
            cache                 = self._cache,
            transaction_ids_cache = self._transaction_ids_cache,
            players_cache         = self._players_cache,
            valid_options_cache   = self._valid_options_cache,
            starters_cache        = self._starters_cache,
            player_ids            = self._player_ids
        )
        
        # Image URL cache
        self._image_urls_cache: Dict[str, str] = {}
        
        # Initialize sub-processors (will be created when needed)
        self._transaction_processor: Optional[TransactionProcessor] = None
        self._matchup_processor: Optional[MatchupProcessor] = None
    
    def _ensure_processors_initialized(self) -> None:
        """Lazy initialization of processors once configuration is known."""
        if self._transaction_processor is None:
            if self._use_faab is None:
                raise ValueError("Cannot initialize processors before use_faab is set")
            
            self._transaction_processor = TransactionProcessor(
                cache                  = self._cache,
                transaction_ids_cache  = self._transaction_ids_cache,
                players_cache          = self._players_cache,
                player_ids             = self._player_ids,
                use_faab               = self._use_faab
            )
            
            self._matchup_processor = MatchupProcessor(
                cache              = self._cache,
                playoff_week_start = self._playoff_week_start
            )
    
    # ========== Update Cache Functions ==========
    
    def set_roster_id(self, manager: str, year: str, week: str, roster_id: int,
                     playoff_roster_ids: dict = {}, matchups: dict = {}) -> None:
        """Set the roster ID for a given manager and year."""
        if roster_id == None:
            # Co-manager scenario; skip
            return
        
        if matchups:
            update_players_cache(matchups, self._players_cache, self._player_ids)

        self._year = year
        self._week = week
        self._playoff_roster_ids = playoff_roster_ids

        if week == "1" or self._use_faab == None or self._playoff_week_start == None:
            # Fetch league settings to determine FAAB usage at start of season
            league_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")[0]
            self._use_faab = True if league_settings.get("settings", {}).get("waiver_type", 1)==2 else False
            self._playoff_week_start = league_settings.get("settings", {}).get("playoff_week_start", None)

        self._weekly_roster_ids[roster_id] = manager
        self._set_defaults_if_missing(roster_id)
        self._cache[manager]["years"][year]["roster_id"] = roster_id

        if "user_id" not in self._cache[manager]["summary"]:
            username = NAME_TO_MANAGER_USERNAME.get(manager, "")
            if username:
                user_payload, status_code = fetch_sleeper_data(f"user/{username}")
                if status_code == 200 and "user_id" in user_payload:
                    self._cache[manager]["summary"]["user_id"] = user_payload["user_id"]
                else:
                    raise ValueError(f"Failed to fetch user data for manager {manager} with username {username}.")
            else:
                raise ValueError(f"No username mapping found for manager {manager}.")
    
    def cache_week_data(self, year: str, week: str) -> None:
        """Cache week-specific data for a given week and year."""
        validate_caching_preconditions(self._weekly_roster_ids, year, week)

        self._ensure_processors_initialized()

        # Set session state in processors BEFORE processing
        self._transaction_processor.set_session_state(
            year=year,
            week=week,
            weekly_roster_ids=self._weekly_roster_ids,
            use_faab=self._use_faab
        )
        self._matchup_processor.set_session_state(
            year=year,
            week=week,
            weekly_roster_ids=self._weekly_roster_ids,
            playoff_roster_ids=self._playoff_roster_ids,
            playoff_week_start=self._playoff_week_start
        )

        # Scrub transaction data for the week
        self._transaction_processor.scrub_transaction_data(year, week)

        # Joke trades, add drop by accident, etc
        self._transaction_processor.check_for_reverse_transactions()

        # Scrub matchup data for the week
        self._matchup_processor.scrub_matchup_data(year, week)

        # Scrub playoff data for the week if applicable
        if get_season_state(week, year, self._playoff_week_start) == "playoffs":
            self._matchup_processor.scrub_playoff_data()

        # Clear weekly metadata
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}

        # Clear processor session state
        self._transaction_processor.clear_session_state()
        self._matchup_processor.clear_session_state()

    
    def set_playoff_placements(self, placement_dict: dict, year: str) -> None:
        """Set playoff placements for managers."""
        for manager in placement_dict:
            if manager not in self._cache:
                continue
            
            if year not in self._cache[manager]["summary"]["overall_data"]["placement"]:
                self._cache[manager]["summary"]["overall_data"]["placement"][year] = placement_dict[manager]

    # ===== API Export Functions =====
    
    def get_managers_list(self, active_only: bool) -> List[str]:
        """Get list of all managers."""
        return self._data_exporter.get_managers_list(active_only=active_only)
    
    def get_manager_summary(self, manager: str, year: str = None) -> Dict:
        """Get manager summary."""
        return self._data_exporter.get_manager_summary(manager, year=year)
    
    def get_manager_yearly_data(self, manager: str, year: str) -> Dict:
        """Get manager yearly data."""
        return self._data_exporter.get_manager_yearly_data(manager, year)
    
    def get_head_to_head(self, manager1: str, manager2: str, year: str = None) -> Dict:
        """Get head-to-head data."""
        return self._data_exporter.get_head_to_head(manager1, manager2, year=year)
    
    def get_manager_transactions(self, manager_name: str, year: str = None, 
                                transaction_type: str = None, limit: int = 50, 
                                offset: int = 0) -> Dict:
        """Get manager transactions."""
        return self._data_exporter.get_manager_transactions(manager_name, year=year,
                                                            transaction_type=transaction_type,
                                                            limit=limit, offset=offset)
    
    def get_manager_awards(self, manager: str) -> Dict:
        """Get manager awards."""
        return self._data_exporter.get_manager_awards(manager)
    
    # ===== SAVE TO DISK =====
    
    def save(self):
        """Save all caches to disk."""
        self._cache_mgr.save_manager_cache(self._cache)
        self._cache_mgr.save_transaction_ids_cache(self._transaction_ids_cache)
        self._cache_mgr.save_players_cache(self._players_cache)
    
    # ========== PRIVATE HELPER METHODS ==========
    
    def _set_defaults_if_missing(self, roster_id: int):
        """Set default cache structure if missing."""
        if not self._templates:
            self._templates = initialize_summary_templates(use_faab=self._use_faab)

        manager = self._weekly_roster_ids.get(roster_id, None)

        if manager not in self._cache:
            self._cache[manager] = {"summary": deepcopy(self._templates['top_level_summary_template']), "years": {}}
        
        if self._year not in self._cache[manager]["years"]:
            self._cache[manager]["years"][self._year] = {
                "summary": deepcopy(self._templates['yearly_summary_template']),
                "roster_id": None,
                "weeks": {}
            }
        
        # Initialize week template if missing
        if self._week not in self._cache[manager]["years"][self._year]["weeks"]:

            # Differentiate between playoff and non-playoff weeks
            season_state = get_season_state(self._week, self._year, self._playoff_week_start)
            if season_state == "playoffs" and roster_id not in self._playoff_roster_ids:
                self._cache[manager]["years"][self._year]["weeks"][self._week] = deepcopy(self._templates['weekly_summary_not_in_playoffs_template'])
            else:
                self._cache[manager]["years"][self._year]["weeks"][self._week] = deepcopy(self._templates['weekly_summary_template'])
        
        if self._use_faab:
            self._cache = initialize_faab_template(manager, self._year, self._week, self._cache)
    
    def _clear_weekly_metadata(self):
        """Clear weekly session state."""
        if self._year == "2024" and self._week == "17":
            self._weekly_roster_ids = {}
        self._week = None
        self._year = None

        # Clear processor session state
        if self._transaction_processor:
            self._transaction_processor.clear_session_state()
        if self._matchup_processor:
            self._matchup_processor.clear_session_state()


# ===== SINGLETON INSTANCE =====
_manager_metadata_instance = None

def get_manager_metadata_manager() -> ManagerMetadataManager:
    """
    Get the singleton ManagerMetadataManager instance.
    
    Returns:
        ManagerMetadataManager instance
    """
    global _manager_metadata_instance
    if _manager_metadata_instance is None:
        _manager_metadata_instance = ManagerMetadataManager()
    return _manager_metadata_instance