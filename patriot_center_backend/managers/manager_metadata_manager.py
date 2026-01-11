"""
Central manager metadata orchestration.

This is the ONLY place where manager metadata operations should be coordinated.
All other code should use ManagerMetadataManager methods.

Single Responsibility: Orchestrate sub-processors and manage persistence.
"""
from copy import deepcopy
from typing import Any, Dict, Optional

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.managers.data_exporter import DataExporter
from patriot_center_backend.managers.formatters import get_season_state
from patriot_center_backend.managers.matchup_processor import MatchupProcessor
from patriot_center_backend.managers.templates import (
    initialize_faab_template,
    initialize_summary_templates,
)
from patriot_center_backend.managers.transaction_processing.base_processor import (
    TransactionProcessor,
)
from patriot_center_backend.managers.validators import validate_caching_preconditions
from patriot_center_backend.utils.player_cache_updater import update_players_cache_with_list
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data


class ManagerMetadataManager:
    """
    Central orchestrator for all manager metadata operations (Singleton).

    This is the ONLY entry point for manager metadata management.
    Coordinates between specialized processors and manages cache persistence.

    Architecture:
    - Singleton pattern ensures single source of truth
    - Facade pattern provides simplified API
    - Lazy initialization for processors (created when configuration known)
    - Session state management during week processing

    Coordinates:
    - TransactionProcessor: Handles trades, adds, drops, FAAB, reversal detection
    - MatchupProcessor: Handles matchups, win/loss records, playoff tracking
    - DataExporter: Provides public read-only API
    - CacheManager: Handles cache loading/saving

    Workflow:
    1. set_roster_id() - Called for each manager to establish roster mapping
    2. cache_week_data() - Processes transactions and matchups for the week
    3. set_playoff_placements() - Records final season standings
    4. save() - Persists all caches to disk

    Access via get_manager_metadata_manager() singleton function.
    """

    def __init__(self) -> None:

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

        # Initialize data_exporter subprocesser
        self._data_exporter = DataExporter()
        
        # Image URL cache
        self._image_urls_cache: Dict[str, str] = {}
        
        # Initialize sub-processors (will be created when needed)
        self._transaction_processor: Optional[TransactionProcessor] = None
        self._matchup_processor: Optional[MatchupProcessor] = None
    
    def _ensure_processors_initialized(self) -> None:
        """
        Lazy initialization of processors once league configuration is known.

        Processors require use_faab and playoff_week_start, which are fetched
        during the first set_roster_id() call. This ensures processors are
        only created after configuration is available.

        Raises:
            ValueError: If use_faab not set before initialization attempt
        """
        if self._transaction_processor is None:
            if self._use_faab is None:
                raise ValueError("Cannot initialize processors before use_faab is set")
            
            self._transaction_processor = TransactionProcessor(
                use_faab = self._use_faab
            )
            
            self._matchup_processor = MatchupProcessor(
                playoff_week_start = self._playoff_week_start
            )
    
    # ========== Update Cache Functions ==========
    
    def set_roster_id(self, manager: str, year: str, week: str, roster_id: int,
                     playoff_roster_ids: dict = {}, matchups: dict = {}) -> None:
        """
        Establish roster ID mapping and initialize manager data structures.

        Must be called for each manager before cache_week_data().
        On first call (week 1), fetches league settings to determine FAAB usage
        and playoff configuration.

        Args:
            manager: Manager name
            year: Season year as string
            week: Week number as string
            roster_id: Sleeper roster ID for this manager (None for co-managers)
            playoff_roster_ids: Dict with playoff bracket roster IDs (optional)
            matchups: Matchup data for updating players cache (optional)

        Raises:
            ValueError: If user data fetch fails or no username mapping found
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        if roster_id == None:
            # Co-manager scenario; skip
            return
        
        if matchups:
            update_players_cache_with_list(matchups)

        self._year = year
        self._week = week
        self._playoff_roster_ids = playoff_roster_ids

        if week == "1" or self._use_faab == None or self._playoff_week_start == None:
            # Fetch league settings to determine FAAB usage at start of season
            league_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")
            self._use_faab = True if league_settings.get("settings", {}).get("waiver_type", 1)==2 else False
            self._playoff_week_start = league_settings.get("settings", {}).get("playoff_week_start", None)

        self._weekly_roster_ids[roster_id] = manager
        self._set_defaults_if_missing(roster_id)
        manager_cache[manager]["years"][year]["roster_id"] = roster_id

        if "user_id" not in manager_cache[manager]["summary"]:
            username = NAME_TO_MANAGER_USERNAME.get(manager, "")
            if username:
                user_payload = fetch_sleeper_data(f"user/{username}")
                if "user_id" in user_payload:
                    manager_cache[manager]["summary"]["user_id"] = user_payload["user_id"]
                else:
                    raise ValueError(f"Failed to fetch 'user_id' for manager {manager} with username {username}.")
            else:
                raise ValueError(f"No username mapping found for manager {manager}.")
    
    def cache_week_data(self, year: str, week: str) -> None:
        """
        Process and cache all data for a specific week.

        Main orchestration method that:
        1. Validates preconditions (roster IDs set, even number of teams, etc.)
        2. Initializes processors if needed
        3. Processes transactions (trades, adds, drops, FAAB)
        4. Checks for transaction reversals
        5. Processes matchups (win/loss records, points)
        6. Processes playoff appearances (if playoff week)
        7. Clears session state to prevent leakage

        Args:
            year: Season year as string
            week: Week number as string

        Raises:
            ValidationError: If preconditions not met
        """
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
        """
        Record final season placements for all managers.

        Should be called after season completion to record final standings.
        Only sets placement if not already set for the year (prevents overwrites).

        Args:
            placement_dict: Dict mapping manager names to placement (1=champion, 2=runner-up, etc.)
            year: Season year as string
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        for manager in placement_dict:
            if manager not in manager_cache:
                continue
            
            if year not in manager_cache[manager]["summary"]["overall_data"]["placement"]:
                manager_cache[manager]["summary"]["overall_data"]["placement"][year] = placement_dict[manager]

    # ===== API Export Functions =====
    
    def get_managers_list(self, active_only: bool) -> Dict[str, Any]:
        """Get list of all managers."""
        return self._data_exporter.get_managers_list(active_only=active_only)
    
    def get_manager_summary(self, manager: str, year: str|None = None) -> Dict[str, Any]:
        """Get manager summary."""
        return self._data_exporter.get_manager_summary(manager, year=year)
    
    def get_head_to_head(self, manager1: str, manager2: str, year: str|None = None) -> Dict[str, Any]:
        """Get head-to-head data."""
        return self._data_exporter.get_head_to_head(manager1, manager2, year=year)
    
    def get_manager_transactions(self, manager_name: str, year: str|None = None) -> Dict[str, Any]:
        """Get manager transactions."""
        return self._data_exporter.get_manager_transactions(manager_name, year=year)
    
    def get_manager_awards(self, manager: str) -> Dict[str, Any]:
        """Get manager awards."""
        return self._data_exporter.get_manager_awards(manager)
    
    # ===== SAVE TO DISK =====
    
    def save(self) -> None:
        """Save all caches to disk."""
        CACHE_MANAGER.save_all_caches()
    
    # ========== PRIVATE HELPER METHODS ==========
    
    def _set_defaults_if_missing(self, roster_id: int) -> None:
        """
        Initialize cache structure for manager/year/week if not already present.

        Creates:
        - Manager entry (if first time seen)
        - Year entry (if new season)
        - Week entry (with appropriate template for playoff vs regular season)
        - FAAB template (if league uses FAAB)

        Uses deep copies of templates to prevent reference sharing.

        Args:
            roster_id: Roster ID to map to manager name
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        if not self._templates:
            self._templates = initialize_summary_templates(use_faab=self._use_faab)

        manager = self._weekly_roster_ids.get(roster_id, None)

        if manager not in manager_cache:
            manager_cache[manager] = {"summary": deepcopy(self._templates['top_level_summary_template']), "years": {}}
        
        if self._year not in manager_cache[manager]["years"]:
            manager_cache[manager]["years"][self._year] = {
                "summary": deepcopy(self._templates['yearly_summary_template']),
                "roster_id": None,
                "weeks": {}
            }
        
        # Initialize week template if missing
        if self._week not in manager_cache[manager]["years"][self._year]["weeks"]:

            # Differentiate between playoff and non-playoff weeks
            season_state = get_season_state(self._week, self._year, self._playoff_week_start)
            if season_state == "playoffs" and roster_id not in self._playoff_roster_ids:
                manager_cache[manager]["years"][self._year]["weeks"][self._week] = deepcopy(self._templates['weekly_summary_not_in_playoffs_template'])
            else:
                manager_cache[manager]["years"][self._year]["weeks"][self._week] = deepcopy(self._templates['weekly_summary_template'])
        
        if self._use_faab:
            initialize_faab_template(manager, self._year, self._week)
    
    def _clear_weekly_metadata(self) -> None:
        """
        Clear weekly session state after processing.

        Resets year, week, and roster ID mappings to prevent state leakage.
        Also clears processor session state if processors exist.
        """
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