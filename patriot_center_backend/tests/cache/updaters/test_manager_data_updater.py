"""Unit tests for manager_data_updater module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)

MODULE_PATH = "patriot_center_backend.cache.updaters.manager_data_updater"


class TestCacheWeekData:
    """Test ManagerMetadataManager.cache_week_data method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_roster_ids`: `mock_get_roster_ids`
        - `validate_caching_preconditions`: (no-op)
        - `get_playoff_roster_ids`:
            `mock_get_playoff_roster_ids`
        - `get_season_state`: `mock_get_season_state`
        - `TransactionProcessor`: `mock_transaction_processor`
        - `MatchupProcessor`: `mock_matchup_processor`

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.get_roster_ids") as mock_get_roster_ids,
            patch(f"{MODULE_PATH}.validate_caching_preconditions"),
            patch(
                f"{MODULE_PATH}.get_playoff_roster_ids"
            ) as mock_get_playoff_roster_ids,
            patch(f"{MODULE_PATH}.get_season_state") as mock_get_season_state,
            patch(f"{MODULE_PATH}.TransactionProcessor"),
            patch(f"{MODULE_PATH}.MatchupProcessor"),
        ):
            self.mock_get_roster_ids = mock_get_roster_ids
            self.mock_get_roster_ids.return_value = {
                1: "Tommy",
                2: "Jay",
            }

            self.mock_get_playoff_roster_ids = mock_get_playoff_roster_ids
            self.mock_get_playoff_roster_ids.return_value = []

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            yield

    def test_calls_get_roster_ids(self):
        """Test calls get_roster_ids with correct year and week."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        self.mock_get_roster_ids.assert_called_once_with(2024, 5)

    def test_calls_get_playoff_roster_ids(self):
        """Test calls get_playoff_roster_ids."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        self.mock_get_playoff_roster_ids.assert_called_once_with(2024, 5)

    def test_calls_setup_league_settings_for_week_1(self):
        """Test calls _setup_league_settings when week is 1."""
        manager = ManagerMetadataManager()

        def set_league_settings():
            manager._use_faab = False
            manager._playoff_week_start = 15

        with (
            patch.object(manager, "_set_defaults_if_missing"),
            patch.object(
                manager,
                "_setup_league_settings",
                side_effect=set_league_settings,
            ) as mock_setup,
        ):
            manager.cache_week_data("2024", "1")

        mock_setup.assert_called_once()

    def test_does_not_call_setup_league_settings_for_other_weeks(self):
        """Test does not call _setup_league_settings for non-week-1."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with (
            patch.object(manager, "_set_defaults_if_missing"),
            patch.object(manager, "_setup_league_settings") as mock_setup,
        ):
            manager.cache_week_data("2024", "5")

        mock_setup.assert_not_called()

    def test_scrubs_transaction_data(self):
        """Test calls scrub_transaction_data on processor."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        (
            manager._transaction_processor.scrub_transaction_data.assert_called_once()
        )

    def test_scrubs_matchup_data(self):
        """Test calls scrub_matchup_data on processor."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        manager._matchup_processor.scrub_matchup_data.assert_called_once()

    def test_scrubs_playoff_data_during_playoffs(self):
        """Test calls scrub_playoff_data when season state is playoffs."""
        self.mock_get_season_state.return_value = "playoffs"

        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "15")

        manager._matchup_processor.scrub_playoff_data.assert_called_once()

    def test_does_not_scrub_playoff_data_during_regular_season(self):
        """Test does not call scrub_playoff_data in regular season."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        manager._matchup_processor.scrub_playoff_data.assert_not_called()

    def test_clears_session_state_after_processing(self):
        """Test clears year, week, and roster IDs after processing."""
        manager = ManagerMetadataManager()
        manager._use_faab = False
        manager._playoff_week_start = 15

        with patch.object(manager, "_set_defaults_if_missing"):
            manager.cache_week_data("2024", "5")

        assert manager._year is None
        assert manager._week is None
        assert manager._weekly_roster_ids == {}


class TestSetDefaultsIfMissing:
    """Test ManagerMetadataManager._set_defaults_if_missing method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_metadata_cache`:
            `mock_get_manager_cache`
        - `initialize_summary_templates`:
            `mock_initialize_templates`
        - `get_season_state`: `mock_get_season_state`
        - `initialize_faab_template`:
            `mock_initialize_faab_template`
        - `TransactionProcessor`: mocked constructor
        - `MatchupProcessor`: mocked constructor

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
            patch(
                f"{MODULE_PATH}.initialize_summary_templates"
            ) as mock_initialize_templates,
            patch(f"{MODULE_PATH}.get_season_state") as mock_get_season_state,
            patch(
                f"{MODULE_PATH}.initialize_faab_template"
            ) as mock_initialize_faab_template,
            patch(f"{MODULE_PATH}.TransactionProcessor"),
            patch(f"{MODULE_PATH}.MatchupProcessor"),
        ):
            self.mock_manager_cache: dict[str, Any] = {}
            mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_initialize_templates = mock_initialize_templates
            self.mock_initialize_templates.return_value = {
                "top_level_summary_template": {"matchup_data": {}},
                "yearly_summary_template": {"matchup_data": {}},
                "weekly_summary_template": {
                    "matchup_data": {},
                    "transactions": {},
                },
                "weekly_summary_not_in_playoffs_template": {
                    "matchup_data": {},
                    "transactions": {},
                },
            }

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            self.mock_initialize_faab_template = mock_initialize_faab_template

            yield

    def test_raises_when_week_not_set(self):
        """Test raises ValueError when week is not set."""
        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = None

        with pytest.raises(ValueError) as exc_info:
            manager._set_defaults_if_missing()

        assert "Week and year must be set" in str(exc_info.value)

    def test_raises_when_year_not_set(self):
        """Test raises ValueError when year is not set."""
        manager = ManagerMetadataManager()
        manager._year = None
        manager._week = "1"

        with pytest.raises(ValueError) as exc_info:
            manager._set_defaults_if_missing()

        assert "Week and year must be set" in str(exc_info.value)

    def test_creates_manager_entry_if_missing(self):
        """Test creates manager entry in cache if not present."""
        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"
        manager._use_faab = False
        manager._playoff_week_start = 15
        manager._weekly_roster_ids = {1: "Tommy"}
        manager._playoff_roster_ids = []

        with patch.object(manager, "_update_user_id"):
            manager._set_defaults_if_missing()

        assert "Tommy" in self.mock_manager_cache
        assert "summary" in self.mock_manager_cache["Tommy"]
        assert "years" in self.mock_manager_cache["Tommy"]

    def test_creates_year_entry_if_missing(self):
        """Test creates year entry in cache if not present."""
        self.mock_manager_cache["Tommy"] = {
            "summary": {"matchup_data": {}, "user_id": "123"},
            "years": {},
        }

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"
        manager._use_faab = False
        manager._playoff_week_start = 15
        manager._weekly_roster_ids = {1: "Tommy"}
        manager._playoff_roster_ids = []

        manager._set_defaults_if_missing()

        assert "2024" in self.mock_manager_cache["Tommy"]["years"]

    def test_creates_week_entry_if_missing(self):
        """Test creates week entry in cache if not present."""
        self.mock_manager_cache["Tommy"] = {
            "summary": {"matchup_data": {}, "user_id": "123"},
            "years": {
                "2024": {
                    "summary": {"matchup_data": {}},
                    "roster_id": None,
                    "weeks": {},
                },
            },
        }

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"
        manager._use_faab = False
        manager._playoff_week_start = 15
        manager._weekly_roster_ids = {1: "Tommy"}
        manager._playoff_roster_ids = []

        manager._set_defaults_if_missing()

        assert (
            "1" in (self.mock_manager_cache["Tommy"]["years"]["2024"]["weeks"])
        )

    def test_raises_when_roster_id_has_no_manager(self):
        """Test raises ValueError when roster_id maps to empty manager."""
        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"
        manager._use_faab = False
        manager._playoff_week_start = 15
        manager._weekly_roster_ids = {1: ""}
        manager._playoff_roster_ids = []

        with pytest.raises(ValueError) as exc_info:
            manager._set_defaults_if_missing()

        assert "Manager not found" in str(exc_info.value)


class TestUpdateUserId:
    """Test ManagerMetadataManager._update_user_id method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_metadata_cache`:
            `mock_get_manager_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `NAME_TO_MANAGER_USERNAME`: mock mapping

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                f"{MODULE_PATH}.NAME_TO_MANAGER_USERNAME",
                {"Tommy": "tommylowry", "Jay": "Jrazzam"},
            ),
            patch(f"{MODULE_PATH}.TransactionProcessor"),
            patch(f"{MODULE_PATH}.MatchupProcessor"),
        ):
            self.mock_manager_cache: dict[str, Any] = {
                "Tommy": {"summary": {}},
            }
            mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = {
                "user_id": "123456789",
            }

            yield

    def test_sets_user_id_in_manager_cache(self):
        """Test sets user_id in manager cache summary."""
        manager = ManagerMetadataManager()

        manager._update_user_id("Tommy")

        assert (
            self.mock_manager_cache["Tommy"]["summary"]["user_id"]
            == "123456789"
        )

    def test_raises_when_no_username_mapping(self):
        """Test raises ValueError when no username mapping found."""
        manager = ManagerMetadataManager()

        with pytest.raises(ValueError) as exc_info:
            manager._update_user_id("Unknown")

        assert "No username mapping found" in str(exc_info.value)

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.return_value = "not_a_dict"

        manager = ManagerMetadataManager()

        with pytest.raises(ValueError) as exc_info:
            manager._update_user_id("Tommy")

        assert "Failed to fetch" in str(exc_info.value)

    def test_raises_when_user_id_missing_from_response(self):
        """Test raises ValueError when user_id not in response."""
        self.mock_fetch_sleeper_data.return_value = {"display_name": "tommy"}

        manager = ManagerMetadataManager()

        with pytest.raises(ValueError) as exc_info:
            manager._update_user_id("Tommy")

        assert "Failed to fetch" in str(exc_info.value)


class TestSetupLeagueSettings:
    """Test ManagerMetadataManager._setup_league_settings method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_league_info`: `mock_get_league_info`

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.get_league_info") as mock_get_league_info,
            patch(f"{MODULE_PATH}.TransactionProcessor"),
            patch(f"{MODULE_PATH}.MatchupProcessor"),
        ):
            self.mock_get_league_info = mock_get_league_info
            self.mock_get_league_info.return_value = {
                "settings": {
                    "waiver_type": 2,
                    "playoff_week_start": 15,
                },
            }

            yield

    def test_sets_use_faab_true_when_waiver_type_2(self):
        """Test sets _use_faab to True when waiver_type is 2."""
        manager = ManagerMetadataManager()
        manager._year = "2024"

        manager._setup_league_settings()

        assert manager._use_faab is True

    def test_sets_use_faab_false_when_waiver_type_1(self):
        """Test sets _use_faab to False when waiver_type is 1."""
        self.mock_get_league_info.return_value = {
            "settings": {
                "waiver_type": 1,
                "playoff_week_start": 15,
            },
        }

        manager = ManagerMetadataManager()
        manager._year = "2024"

        manager._setup_league_settings()

        assert manager._use_faab is False

    def test_sets_playoff_week_start(self):
        """Test sets _playoff_week_start from league settings."""
        manager = ManagerMetadataManager()
        manager._year = "2024"

        manager._setup_league_settings()

        assert manager._playoff_week_start == 15

    def test_raises_when_year_not_set(self):
        """Test raises ValueError when year is not set."""
        manager = ManagerMetadataManager()
        manager._year = None

        with pytest.raises(ValueError) as exc_info:
            manager._setup_league_settings()

        assert "Year must be set" in str(exc_info.value)


class TestClearWeeklyMetadata:
    """Test ManagerMetadataManager._clear_weekly_metadata method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.TransactionProcessor"),
            patch(f"{MODULE_PATH}.MatchupProcessor"),
        ):
            yield

    def test_clears_week_year_and_roster_ids(self):
        """Test clears _week, _year, and _weekly_roster_ids."""
        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "5"
        manager._weekly_roster_ids = {1: "Tommy"}

        manager._clear_weekly_metadata()

        assert manager._year is None
        assert manager._week is None
        assert manager._weekly_roster_ids == {}

    def test_clears_processor_session_states(self):
        """Test clears session state on both processors."""
        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "5"
        manager._weekly_roster_ids = {}

        manager._clear_weekly_metadata()

        manager._transaction_processor.clear_session_state.assert_called_once()
        manager._matchup_processor.clear_session_state.assert_called_once()
