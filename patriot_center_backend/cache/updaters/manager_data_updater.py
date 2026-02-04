"""Central manager metadata orchestration."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._templates import (
    initialize_faab_template,
    initialize_summary_templates,
)
from patriot_center_backend.cache.updaters._validators import (
    validate_caching_preconditions,
)
from patriot_center_backend.cache.updaters.image_urls_updater import (
    update_image_urls_cache,
)
from patriot_center_backend.cache.updaters.processors.matchup_processor import (
    MatchupProcessor,
)
from patriot_center_backend.cache.updaters.processors.transactions.base_processor import (  # noqa: E501
    TransactionProcessor,
)
from patriot_center_backend.constants import (
    NAME_TO_MANAGER_USERNAME,
)
from patriot_center_backend.playoffs.playoff_tracker import (
    get_playoff_roster_ids,
)
from patriot_center_backend.utils.formatters import get_season_state
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_league_info,
    get_roster_ids,
)


class ManagerMetadataManager:
    """Central orchestrator for all manager metadata operations (Singleton).

    This is the ONLY entry point for manager metadata management.
    Coordinates between specialized processors and manages cache persistence.

    Architecture:
    - Singleton pattern ensures single source of truth
    - Facade pattern provides simplified API
    - Lazy initialization for processors (created when configuration known)
    - Session state management during week processing

    Coordinates:
    - TransactionProcessor: Handles trades, adds, drops, FAAB, reversal
        detection
    - MatchupProcessor: Handles matchups, win/loss records, playoff tracking
    - CacheManager: Handles cache loading/saving

    Workflow:
    1. set_roster_id() - Called for each manager to establish roster mapping
    2. cache_week_data() - Processes transactions and matchups for the week
    3. set_playoff_placements() - Records final season standings
    4. save() - Persists all caches to disk

    Access via get_manager_metadata_manager() singleton function.
    """

    def __init__(self) -> None:
        """Initializes the ManagerMetadataManager singleton.

        Sets configuration state, initializes templates, and sets session state.
        Also initializes sub-processors transaction_processor matchup_processor
        """
        # Configuration state
        self._use_faab: bool
        self._playoff_week_start: int

        # Initialize templates
        self._templates: dict[str, dict[str, Any]] = {}

        # Initialize data_exporter subprocesser
        self._needs_faab_image_urls_update = True

        # Session state
        self._year: str | None = None
        self._week: str | None = None
        self._weekly_roster_ids: dict[int, str] = {}
        self._playoff_roster_ids: list[int] = []

        # Initialize sub-processors (will be created when needed)
        self._transaction_processor = TransactionProcessor()
        self._matchup_processor = MatchupProcessor()

    # ========== Update Cache Functions ==========
    def cache_week_data(self, year: str, week: str) -> None:
        """Process and cache all data for a specific week.

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
        """
        self._weekly_roster_ids = get_roster_ids(int(year), int(week))

        validate_caching_preconditions(self._weekly_roster_ids, year, week)

        self._year = year
        self._week = week

        self._playoff_roster_ids = get_playoff_roster_ids(
            int(self._year), int(self._week)
        )

        if self._week == "1":
            self._setup_league_settings()

        # Initialize weekly metadata
        self._set_defaults_if_missing()

        # Set session state in processors BEFORE processing
        self._transaction_processor.set_session_state(
            year=year,
            week=week,
            weekly_roster_ids=self._weekly_roster_ids,
            use_faab=self._use_faab,
        )
        self._matchup_processor.set_session_state(
            year=year,
            week=week,
            weekly_roster_ids=self._weekly_roster_ids,
            playoff_roster_ids=self._playoff_roster_ids,
            playoff_week_start=self._playoff_week_start,
        )

        # Scrub transaction data for the week
        self._transaction_processor.scrub_transaction_data()

        # Joke trades, add drop by accident, etc
        self._transaction_processor.check_for_reverse_transactions()

        # Scrub matchup data for the week
        self._matchup_processor.scrub_matchup_data()

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

    # ========== PRIVATE HELPER METHODS ==========
    def _set_defaults_if_missing(self) -> None:
        """Initialize cache structure for manager/year/week if not present.

        Creates:
        - Manager entry (if first time seen)
        - Year entry (if new season)
        - Week entry (with appropriate template for playoff vs regular season)
        - FAAB template (if league uses FAAB)

        Uses deep copies of templates to prevent reference sharing.

        Raises:
            ValueError: If week or year is not set
                or `roster_id` not found in self._weekly_roster_ids
        """
        if not self._week or not self._year:
            raise ValueError(
                "Week and year must be set before setting week data."
            )

        manager_cache = CACHE_MANAGER.get_manager_cache()
        image_urls_cache = CACHE_MANAGER.get_image_urls_cache()

        if not self._templates:
            self._templates = initialize_summary_templates(
                use_faab=self._use_faab
            )

        for roster_id in self._weekly_roster_ids:
            manager = self._weekly_roster_ids.get(roster_id, None)
            if not manager:
                raise ValueError(
                    f"Manager not found for roster ID {roster_id}."
                )

            if manager not in manager_cache:
                manager_cache[manager] = {
                    "summary": deepcopy(
                        self._templates["top_level_summary_template"]
                    ),
                    "years": {},
                }

            if self._year not in manager_cache[manager]["years"]:
                manager_cache[manager]["years"][self._year] = {
                    "summary": deepcopy(
                        self._templates["yearly_summary_template"]
                    ),
                    "roster_id": None,
                    "weeks": {},
                }

            # Initialize week template if missing
            weeks_level = manager_cache[manager]["years"][self._year]["weeks"]
            if self._week not in weeks_level:
                # Differentiate between playoff and non-playoff weeks
                season_state = get_season_state(
                    self._week, self._year, self._playoff_week_start
                )

                if (
                    season_state == "playoffs"
                    and roster_id not in self._playoff_roster_ids
                ):
                    weeks_level[self._week] = deepcopy(
                        self._templates[
                            "weekly_summary_not_in_playoffs_template"
                        ]
                    )

                else:  # season_state == "regular_season"
                    weeks_level[self._week] = deepcopy(
                        self._templates["weekly_summary_template"]
                    )

            if self._use_faab:
                initialize_faab_template(manager, self._year, self._week)

            manager_cache[manager]["years"][self._year]["roster_id"] = roster_id

            if "user_id" not in manager_cache[manager]["summary"]:
                self._update_user_id(manager)

    def _update_user_id(self, manager: str) -> None:
        manager_cache = CACHE_MANAGER.get_manager_cache()
        username = NAME_TO_MANAGER_USERNAME.get(manager, "")
        if not username:  # No username mapping
            raise ValueError(
                f"No username mapping found for manager {manager}."
            )

        user_payload = fetch_sleeper_data(f"user/{username}")
        if not isinstance(user_payload, dict) or "user_id" not in user_payload:
            raise ValueError(  # User data fetch failed
                f"Failed to fetch 'user_id' for manager "
                f"{manager} with username {username}."
            )

        # Add user_id to manager cache
        manager_cache[manager]["summary"]["user_id"] = user_payload["user_id"]

        update_image_urls_cache(manager)

    def _setup_league_settings(self) -> None:
        # Fetch league settings to determine FAAB usage at start of
        # season
        if not self._year:
            raise ValueError(
                "Year must be set before setting up league settings."
            )

        league_info = get_league_info(int(self._year))
        league_settings = league_info.get("settings", {})

        # Set use_faab to True if waiver_type == 2
        waiver_type = league_settings.get("waiver_type", 1)
        self._use_faab = waiver_type == 2

        # Set playoff_week_start
        self._playoff_week_start = league_settings.get("playoff_week_start")

    def _clear_weekly_metadata(self) -> None:
        """Clear weekly session state after processing.

        Resets year, week, and roster ID mappings to prevent state leakage.
        Also clears processor session state if processors exist.
        """
        self._weekly_roster_ids = {}
        self._week = None
        self._year = None

        # Clear processor session state
        if self._transaction_processor:
            self._transaction_processor.clear_session_state()
        if self._matchup_processor:
            self._matchup_processor.clear_session_state()
