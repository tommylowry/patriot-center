from copy import deepcopy, copy

from patriot_center_backend.constants import MANAGER_METADATA_CACHE_FILE, LEAGUE_IDS
from patriot_center_backend.utils.cache_utils import load_cache, save_cache
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data


class ManagerMetadataManager:
    def __init__(self):
        self._cache = {
            # "manager":{
            #     "summary": { ... },
            #     "years": {
            #         "2020": {
            #             "summary": { ... },
            #             "roster_id": 123456,
            #             "weeks": {
            #                 "1": {
            #                     "points_for": 120.5,
            #                     "points_against": 98.3,
            #                     ...
            #                 },
            #             },
            #         },
            #         ...
            #     }
            # }
        }
        self._current_roster_ids = {
            # roster_id: manager
        }




    def load(self):
        """Load the entire manager metadata cache."""
        cache = load_cache(MANAGER_METADATA_CACHE_FILE, initialize_with_last_updated_info=False)
        if cache is not {}:
            self._cache = copy(deepcopy(cache))

    def save(self):
        """Save the entire manager metadata cache."""
        save_cache(MANAGER_METADATA_CACHE_FILE, self._cache)
        self._current_roster_ids = {}


    def set_roster_id(self, manager: str, year: str, week: str, roster_id: int):
        """Set the roster ID for a given manager and year."""

        self._set_defaults_if_missing(manager, year, week)
        self._cache[manager]["years"][year]["roster_id"] = roster_id
    
    
    def cache_week_data(self, year: str, week: str):
        """Cache week-specific data for a given week and year."""
        
        # Ensure preconditions are met
        self._caching_preconditions_met()

        #
        self._scrub_transaction_data(year, week)

        
        
    








    
    
    def _set_defaults_if_missing(self, manager: str, year: str, week: str):
        """Helper to initialize nested structures if missing."""
        if manager not in self._cache:
            self._cache[manager] = {"summary": {}, "years": {}}
        
        if year not in self._cache[manager]["years"]:
            self._cache[manager]["years"][year] = {
                "summary": {},
                "roster_id": None,
                "weeks": {}
            }
        
        if week not in self._cache[manager]["years"][year]["weeks"]:
            self._cache[manager]["years"][year]["weeks"][week] = {}

    def _caching_preconditions_met(self):
        """Check if preconditions for caching week data are met."""
        if len(self._current_roster_ids) == 0:
            # No roster IDs cached yet; nothing to do
            raise ValueError("No roster IDs cached. Cannot cache week data.")
        
        if len(self._current_roster_ids) % 2 == 1:
            # Sanity check: expect even number of rosters for matchups
            raise ValueError("Odd number of roster IDs cached, cannot process matchups.")
        
    
    def _scrub_transaction_data(self, year: str, week: str):
        """Scrub transaction data for all cached roster IDs for a given week."""
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        transactions_dict = fetch_sleeper_data(f"league/{league_id}/transactions/{week}")

        for transaction in transactions_dict:
            print("Transaction:", transaction)