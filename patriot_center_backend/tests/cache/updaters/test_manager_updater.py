"""Unit tests for manager_metadata_manager module."""

from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from patriot_center_backend.cache.cache_manager import CacheManager
from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.cache.updaters.processors.matchup_processor import (
    MatchupProcessor,
)
from patriot_center_backend.cache.updaters.processors.transactions.base_processor import (  # noqa: E501
    TransactionProcessor,
)


@pytest.fixture(autouse=True)
def globals_setup():
    """Setup common mocks for all tests.

    The mocks are set up to return a pre-defined
    set of values when accessed.
    - `CACHE_MANAGER`: `MagicMock(spec=CacheManager)`
    - `NAME_TO_MANAGER_USERNAME`: `{"Manager 1": "manager1_user"}`

    Yields:
        None
    """
    with (
        patch(
            "patriot_center_backend.managers.manager_metadata_manager"
            ".CACHE_MANAGER",
            MagicMock(spec=CacheManager),
        ),
        patch(
            "patriot_center_backend.managers.manager_metadata_manager"
            ".NAME_TO_MANAGER_USERNAME",
            {"Manager 1": "manager1_user"},
        ),
    ):
        yield


@pytest.fixture
def metadata_manager() -> ManagerMetadataManager:
    """Create ManagerMetadataManager instance.

    Returns:
        ManagerMetadataManager instance
    """
    metadata_manager = ManagerMetadataManager()
    metadata_manager._use_faab = True
    metadata_manager._playoff_week_start = 15
    return metadata_manager


@pytest.fixture
def mock_transaction_processor() -> TransactionProcessor:
    """Create MagicMock for TransactionProcessor.

    Returns:
        A MagicMock with TransactionProcessor's interface.
    """
    return MagicMock(spec=TransactionProcessor)


@pytest.fixture
def mock_matchup_processor() -> MatchupProcessor:
    """Create MagicMock for MatchupProcessor.

    Returns:
        A MagicMock with MatchupProcessor's interface.
    """
    return MagicMock(spec=MatchupProcessor)


@pytest.fixture
def mock_data_exporter() -> DataExporter:
    """Create MagicMock for DataExporter.

    Returns:
        A MagicMock with DataExporter's interface.
    """
    return MagicMock(spec=DataExporter)


class TestManagerMetadataManagerInit:
    """Test ManagerMetadataManager initialization."""

    def test_init_creates_necessary_instances(self):
        """Test that __init__ creates all necessary instances."""
        from patriot_center_backend.cache.updaters.manager_data_updater import (
            ManagerMetadataManager,
        )

        metadata_manager = ManagerMetadataManager()

        assert metadata_manager._data_exporter is not None
        assert metadata_manager._transaction_processor is not None
        assert metadata_manager._matchup_processor is not None

    def test_singleton_pattern(self):
        """Test that get_manager_metadata_manager returns singleton."""
        from patriot_center_backend.managers import MANAGER_METADATA_MANAGER
        from patriot_center_backend.cache.updaters.manager_data_updater import (
            _manager_metadata_instance,
        )

        _manager_metadata_instance = None  # noqa: F811

        mgr1 = MANAGER_METADATA_MANAGER
        mgr2 = MANAGER_METADATA_MANAGER

        # Should be same instance
        assert mgr1 is mgr2


class TestSetRosterId:
    """Test set_roster_id method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `update_players_cache_with_list`: `mock_update_players`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `ManagerMetadataManager._set_defaults_if_missing`: `mock_set_defaults`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".update_players_cache_with_list"
            ) as mock_update_players,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".ManagerMetadataManager._set_defaults_if_missing"
            ) as mock_set_defaults,
        ):
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_update_players = mock_update_players

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = {}

            self.mock_set_defaults = mock_set_defaults

            yield

    def test_set_roster_id_calls_set_defaults(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that _set_defaults_if_missing is called.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"},
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                },
            }
        }

        metadata_manager.set_roster_id(
            manager="Manager 1", year="2023", week="1", roster_id=1
        )

        self.mock_set_defaults.assert_called_once_with(1)

    def test_set_roster_id_updates_roster_mapping(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that roster ID is mapped to manager.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"},
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                },
            }
        }

        metadata_manager.set_roster_id(
            manager="Manager 1", year="2023", week="1", roster_id=1
        )

        assert metadata_manager._weekly_roster_ids[1] == "Manager 1"

    def test_set_roster_id_skips_none_roster_id(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that None roster_id (co-manager) is skipped.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        metadata_manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=None,  # type: ignore
        )

        # Should not create any entries
        assert "Manager 1" not in self.mock_manager_cache
        assert not self.mock_fetch_sleeper_data.called

    def test_set_roster_id_fetches_league_settings_week_1(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that league settings are fetched on week 1.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"},
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                },
            }
        }

        metadata_manager.set_roster_id(
            manager="Manager 1", year="2023", week="1", roster_id=1
        )

        # Should fetch league settings
        assert self.mock_fetch_sleeper_data.called
        assert metadata_manager._use_faab is True
        assert metadata_manager._playoff_week_start == 15

    def test_cache_references_are_consistent(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that cache references remain consistent.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 1, "playoff_week_start": 15}},
            {"user_id": "user123"},
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                },
            }
        }

        original_cache = self.mock_manager_cache

        metadata_manager.set_roster_id("Manager 1", "2023", "1", 1)

        # Cache reference should not change
        assert self.mock_manager_cache is original_cache


class TestCacheWeekData:
    """Test cache_week_data method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `validate_caching_preconditions`: `mock_validate`
        - `get_season_state`: `mock_get_season_state`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".validate_caching_preconditions"
            ) as mock_validate,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".get_season_state"
            ) as mock_get_season_state,
        ):
            self.mock_validate = mock_validate
            self.mock_get_season_state = mock_get_season_state

            yield

    def test_cache_week_data_processes_matchups_and_transactions(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_transaction_processor: TransactionProcessor,
        mock_matchup_processor: MatchupProcessor,
    ):
        """Test that cache_week_data processes both matchups and transactions.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_transaction_processor: Mock TransactionProcessor instance
            mock_matchup_processor: Mock MatchupProcessor instance
        """
        metadata_manager._transaction_processor = mock_transaction_processor
        metadata_manager._matchup_processor = mock_matchup_processor

        metadata_manager.cache_week_data("2023", "1")

        # Should process both
        transaction_processor = metadata_manager._transaction_processor
        assert transaction_processor.scrub_transaction_data.called

        matchup_processor = metadata_manager._matchup_processor
        assert matchup_processor.scrub_matchup_data.called

    def test_cache_week_data_checks_for_reversals(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_transaction_processor: TransactionProcessor,
        mock_matchup_processor: MatchupProcessor,
    ):
        """Test that cache_week_data checks for transaction reversals.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_transaction_processor: Mock TransactionProcessor instance
            mock_matchup_processor: Mock MatchupProcessor instance
        """
        metadata_manager._transaction_processor = mock_transaction_processor
        metadata_manager._matchup_processor = mock_matchup_processor

        metadata_manager.cache_week_data("2023", "1")

        # Should check for reversals
        transaction_processor = metadata_manager._transaction_processor
        assert transaction_processor.check_for_reverse_transactions.called

    def test_cache_week_data_processes_playoff_data(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_transaction_processor: TransactionProcessor,
        mock_matchup_processor: MatchupProcessor,
    ):
        """Test that playoff data is processed during playoff weeks.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_transaction_processor: Mock TransactionProcessor instance
            mock_matchup_processor: Mock MatchupProcessor instance
        """
        self.mock_get_season_state.return_value = "playoffs"

        metadata_manager._transaction_processor = mock_transaction_processor
        metadata_manager._matchup_processor = mock_matchup_processor

        metadata_manager.cache_week_data("2023", "15")

        # Should process playoff data
        matchup_processor = metadata_manager._matchup_processor
        assert matchup_processor.scrub_playoff_data.called

    def test_cache_week_data_clears_state_after(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_transaction_processor: TransactionProcessor,
        mock_matchup_processor: MatchupProcessor,
    ):
        """Test that session state is cleared after processing.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_transaction_processor: Mock TransactionProcessor instance
            mock_matchup_processor: Mock MatchupProcessor instance
        """
        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        metadata_manager._transaction_processor = mock_transaction_processor
        metadata_manager._matchup_processor = mock_matchup_processor

        metadata_manager.cache_week_data("2023", "1")

        # Should clear processors
        transaction_processor = metadata_manager._transaction_processor
        assert transaction_processor.clear_session_state.called

        matchup_processor = metadata_manager._matchup_processor
        assert matchup_processor.clear_session_state.called

        # Should clear state
        assert metadata_manager._year is None
        assert metadata_manager._week is None
        assert metadata_manager._weekly_roster_ids == {}


class TestSetPlayoffPlacements:
    """Test set_playoff_placements method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager,
        ):
            self.mock_manager_cache = {}
            self.mock_get_manager = mock_get_manager
            self.mock_get_manager.return_value = self.mock_manager_cache

            yield

    def test_set_playoff_placements_updates_cache(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that playoff placements are added to cache.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        placements = {"Manager 1": 1, "Manager 2": 2}
        self.mock_manager_cache.update(
            {"Manager 1": {"summary": {"overall_data": {"placement": {}}}}}
        )

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        metadata_manager.set_playoff_placements(placements, "2023")

        manager_summary = self.mock_manager_cache["Manager 1"]["summary"]
        assert manager_summary["overall_data"]["placement"]["2023"] == 1

    def test_set_playoff_placements_skips_unknown_managers(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that unknown managers are skipped.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        placements = {"Unknown Manager": 1}

        # Should not raise error
        metadata_manager.set_playoff_placements(placements, "2023")


class TestGetManagersList:
    """Test get_managers_list method."""

    def test_get_managers_list_delegates_to_exporter(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_data_exporter: DataExporter,
    ):
        """Test that get_managers_list delegates to data exporter.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_data_exporter: Mock DataExporter instance
        """
        metadata_manager._data_exporter = mock_data_exporter
        metadata_manager._data_exporter.get_managers_list.return_value = {
            "managers": []
        }

        result = metadata_manager.get_managers_list(active_only=True)

        data_exporter = metadata_manager._data_exporter
        data_exporter.get_managers_list.assert_called_once_with(
            active_only=True
        )
        assert result == {"managers": []}


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    def test_get_manager_summary_delegates_to_exporter(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_data_exporter: DataExporter,
    ):
        """Test that get_manager_summary delegates to data exporter.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_data_exporter: Mock DataExporter instance
        """
        mock_data_exporter.get_manager_summary.return_value = {
            "manager_name": "Manager 1"
        }
        metadata_manager._data_exporter = mock_data_exporter

        metadata_manager.get_manager_summary("Manager 1", year="2023")

        data_exporter = metadata_manager._data_exporter
        data_exporter.get_manager_summary.assert_called_once_with(
            "Manager 1", year="2023"
        )


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    def test_get_head_to_head_delegates_to_exporter(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_data_exporter: DataExporter,
    ):
        """Test that get_head_to_head delegates to data exporter.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_data_exporter: Mock DataExporter instance
        """
        mock_data_exporter.get_head_to_head.return_value = {}
        metadata_manager._data_exporter = mock_data_exporter

        metadata_manager.get_head_to_head("Manager 1", "Manager 2", year="2023")

        data_exporter = metadata_manager._data_exporter
        data_exporter.get_head_to_head.assert_called_once_with(
            "Manager 1", "Manager 2", year="2023"
        )


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    def test_get_manager_transactions_delegates_to_exporter(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_data_exporter: DataExporter,
    ):
        """Test that get_manager_transactions delegates to data exporter.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_data_exporter: Mock DataExporter instance
        """
        mock_data_exporter.get_manager_transactions.return_value = {}
        metadata_manager._data_exporter = mock_data_exporter

        metadata_manager.get_manager_transactions("Manager 1", year="2023")

        data_exporter = metadata_manager._data_exporter
        data_exporter.get_manager_transactions.assert_called_once_with(
            "Manager 1", year="2023"
        )


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    def test_get_manager_awards_delegates_to_exporter(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_data_exporter: DataExporter,
    ):
        """Test that get_manager_awards delegates to data exporter.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_data_exporter: Mock DataExporter instance
        """
        metadata_manager._data_exporter = mock_data_exporter
        metadata_manager._data_exporter.get_manager_awards.return_value = {}

        metadata_manager.get_manager_awards("Manager 1")

        data_exporter = metadata_manager._data_exporter
        data_exporter.get_manager_awards.assert_called_once_with("Manager 1")


class TestSave:
    """Test save method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.save_all_caches`: `mock_save_caches`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".CACHE_MANAGER.save_all_caches"
            ) as mock_save_caches,
        ):
            self.mock_save_caches = mock_save_caches

            yield

    def test_save_writes_all_caches(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test that save writes all caches to disk.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        metadata_manager.save()

        assert self.mock_save_caches.called


class TestSetDefaultsIfMissing:
    """Test _set_defaults_if_missing method tests calling function directly."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `initialize_summary_templates`: `mock_init_templates`
        - `get_season_state`: `mock_get_season_state`
        - `initialize_faab_template`: `mock_init_faab`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".initialize_summary_templates"
            ) as mock_init_templates,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".get_season_state"
            ) as mock_get_season_state,
            patch(
                "patriot_center_backend.managers.manager_metadata_manager"
                ".initialize_faab_template"
            ) as mock_init_faab,
        ):
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_init_templates = mock_init_templates

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            self.mock_init_faab = mock_init_faab

            yield

    def test_set_defaults_creates_manager_entry(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _set_defaults_if_missing creates manager entry if not exists.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_get_season_state.return_value = "return_value"

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._use_faab = False
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = []
        metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        metadata_manager._templates = MagicMock()

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Should create manager entry
        assert "Manager 1" in self.mock_manager_cache
        assert "summary" in self.mock_manager_cache["Manager 1"]
        assert "years" in self.mock_manager_cache["Manager 1"]

        # 4 calls, 1 if its populated, 2 manager, 3 yearly, 4 weekly
        assert len(metadata_manager._templates.mock_calls) == 4

    def test_set_defaults_creates_year_entry(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _set_defaults_if_missing creates year entry if not exists.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_get_season_state.return_value = "return_value"

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._use_faab = False
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = []
        metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        metadata_manager._templates = MagicMock(spec=dict[str, Any])

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Should create year entry
        years_entry = self.mock_manager_cache["Manager 1"]["years"]
        assert "2023" in years_entry
        assert "summary" in years_entry["2023"]
        assert "weeks" in years_entry["2023"]

        # Yearly template should be called to be used
        calls = metadata_manager._templates.__getitem__.call_args_list
        assert call("yearly_summary_template") in calls

    def test_set_defaults_creates_week_entry(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test function creates week entry with correct template.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_get_season_state.return_value = "regular_season"

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._use_faab = False
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = []
        metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        metadata_manager._templates = MagicMock(spec=dict[str, Any])

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Should create week entry
        weeks = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]
        assert "1" in weeks

        # Non-playoff weekly template should be called to be used
        calls = metadata_manager._templates.__getitem__.call_args_list
        assert call("weekly_summary_template") in calls

    def test_set_defaults_uses_playoff_template_when_not_in_playoffs(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test function uses playoff template for non-playoff teams.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_get_season_state.return_value = "playoffs"

        metadata_manager._year = "2023"
        metadata_manager._week = "15"
        metadata_manager._use_faab = False
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = [2, 3]
        metadata_manager._weekly_roster_ids[1] = "Manager 1"

        metadata_manager._templates = MagicMock(spec=dict[str, Any])

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Check if the not in playoffs template was used and NOT the normal one
        calls = metadata_manager._templates.__getitem__.call_args_list
        assert call("weekly_summary_not_in_playoffs_template") in calls
        assert call("weekly_summary_template") not in calls

    def test_set_defaults_skips_existing_entries(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _set_defaults_if_missing does not overwrite existing data.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        # Initialize with proper template structure plus custom data
        self.mock_manager_cache.update(
            {"Manager 1": {"existing": "data", "summary": {}, "years": {}}}
        )
        self.mock_get_season_state.return_value = "regular_season"

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._use_faab = False
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = [2, 3]
        metadata_manager._weekly_roster_ids[1] = "Manager 1"

        metadata_manager._templates = MagicMock(spec=dict[str, Any])

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Should not overwrite existing key
        assert self.mock_manager_cache["Manager 1"]["existing"] == "data"

        calls = metadata_manager._templates.__getitem__.call_args_list

        # top level summary template NOT called for
        assert call("top_level_summary_template") not in calls

        # yearly and weekly summary templates called for
        assert call("yearly_summary_template") in calls
        assert call("weekly_summary_template") in calls

    def test_set_defaults_initializes_faab_when_enabled(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test function initializes FAAB template when FAAB is enabled.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        self.mock_get_season_state.return_value = "regular_season"

        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._use_faab = True
        metadata_manager._playoff_week_start = 15
        metadata_manager._playoff_roster_ids = []
        metadata_manager._weekly_roster_ids[1] = "Manager 1"

        metadata_manager._templates = MagicMock(spec=dict[str, Any])

        # Call directly
        metadata_manager._set_defaults_if_missing(1)

        # Should call initialize_faab_template
        self.mock_init_faab.assert_called_once_with("Manager 1", "2023", "1")


class TestClearWeeklyMetadata:
    """Test _clear_weekly_metadata method."""

    def test_clear_weekly_metadata_resets_year_and_week(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _clear_weekly_metadata resets year and week to None.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        metadata_manager._year = "2023"
        metadata_manager._week = "5"

        metadata_manager._clear_weekly_metadata()

        assert metadata_manager._year is None
        assert metadata_manager._week is None

    def test_clear_weekly_metadata_special_case_2024_week_17(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _clear_weekly_metadata clears roster IDs for 2024 week 17.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        metadata_manager._year = "2024"
        metadata_manager._week = "17"
        metadata_manager._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        metadata_manager._clear_weekly_metadata()

        # Should clear roster IDs for this special case
        assert metadata_manager._weekly_roster_ids == {}
        assert metadata_manager._year is None
        assert metadata_manager._week is None

    def test_clear_weekly_metadata_clears_processor_state(
        self,
        metadata_manager: ManagerMetadataManager,
        mock_transaction_processor: TransactionProcessor,
        mock_matchup_processor: MatchupProcessor,
    ):
        """Test _clear_weekly_metadata calls clear_session_state on processors.

        Args:
            metadata_manager: ManagerMetadataManager instance
            mock_transaction_processor: Mock TransactionProcessor instance
            mock_matchup_processor: Mock MatchupProcessor instance
        """
        metadata_manager._year = "2023"
        metadata_manager._week = "1"

        # Create processor instances
        metadata_manager._transaction_processor = mock_transaction_processor
        metadata_manager._matchup_processor = mock_matchup_processor

        metadata_manager._clear_weekly_metadata()

        # Should call clear_session_state on both processors
        transaction_processor = metadata_manager._transaction_processor
        transaction_processor.clear_session_state.assert_called_once()

        matchup_processor = metadata_manager._matchup_processor
        matchup_processor.clear_session_state.assert_called_once()

    def test_clear_weekly_metadata_handles_no_processors(
        self, metadata_manager: ManagerMetadataManager
    ):
        """Test _clear_weekly_metadata handles None processors gracefully.

        Args:
            metadata_manager: ManagerMetadataManager instance
        """
        metadata_manager._year = "2023"
        metadata_manager._week = "1"
        metadata_manager._transaction_processor = None  # type: ignore
        metadata_manager._matchup_processor = None  # type: ignore

        # Should not raise exception
        metadata_manager._clear_weekly_metadata()

        assert metadata_manager._year is None
        assert metadata_manager._week is None
