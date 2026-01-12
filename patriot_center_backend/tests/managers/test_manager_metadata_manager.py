"""
Unit tests for manager_metadata_manager module.

Tests the ManagerMetadataManager class (singleton orchestrator).
All tests mock file I/O and API calls to avoid touching real cache files.
"""
from unittest.mock import MagicMock, call, patch

import pytest

from patriot_center_backend.managers.manager_metadata_manager import (
    ManagerMetadataManager,
    get_manager_metadata_manager,
)


@pytest.fixture(autouse=True)
def patch_caches():
    with patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER', MagicMock()):
        yield


@pytest.fixture
def mock_metadata_manager():
    """Create DataExporter instance with sample caches."""
    return ManagerMetadataManager()


class TestManagerMetadataManagerInit:
    """Test ManagerMetadataManager initialization."""

    def test_init_creates_data_exporter(self):
        """Test that __init__ creates DataExporter instance."""
        mock_metadata_manager = ManagerMetadataManager()

        assert mock_metadata_manager._data_exporter is not None

    def test_init_does_not_create_processors(self):
        """Test that __init__ does not create processors (lazy initialization)."""
        mock_metadata_manager = ManagerMetadataManager()

        assert mock_metadata_manager._transaction_processor is None
        assert mock_metadata_manager._matchup_processor is None

    def test_singleton_pattern(self):
        """Test that get_manager_metadata_manager returns singleton."""
        ManagerMetadataManager._manager_metadata_instance = None

        mgr1 = get_manager_metadata_manager()
        mgr2 = get_manager_metadata_manager()

        # Should be same instance
        assert mgr1 is mgr2


class TestEnsureProcessorsInitialized:
    """Test _ensure_processors_initialized method."""

    def test_initializes_processors_on_first_call(self, mock_metadata_manager):
        """Test that processors are created on first call."""
        mock_metadata_manager._use_faab = True
        mock_metadata_manager._playoff_week_start = 15

        mock_metadata_manager._ensure_processors_initialized()

        assert mock_metadata_manager._transaction_processor is not None
        assert mock_metadata_manager._matchup_processor is not None

    def test_does_not_reinitialize_processors(self, mock_metadata_manager):
        """Test that processors are not recreated on subsequent calls."""
        mock_metadata_manager._use_faab = True
        mock_metadata_manager._playoff_week_start = 15

        mock_metadata_manager._ensure_processors_initialized()
        first_transaction = mock_metadata_manager._transaction_processor
        first_matchup = mock_metadata_manager._matchup_processor

        mock_metadata_manager._ensure_processors_initialized()

        # Should be same instances
        assert mock_metadata_manager._transaction_processor is first_transaction
        assert mock_metadata_manager._matchup_processor is first_matchup

    def test_raises_if_use_faab_not_set(self, mock_metadata_manager):
        """Test that ValueError is raised if use_faab not set."""
        mock_metadata_manager._use_faab = None

        with pytest.raises(ValueError, match="Cannot initialize processors before use_faab is set"):
            mock_metadata_manager._ensure_processors_initialized()


class TestSetRosterId:
    """Test set_roster_id method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER.get_manager_cache') as mock_get_manager_cache, \
             patch('patriot_center_backend.managers.manager_metadata_manager.update_players_cache_with_list') as mock_update_players, \
             patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data') as mock_fetch_sleeper_data, \
             patch('patriot_center_backend.managers.manager_metadata_manager.ManagerMetadataManager._set_defaults_if_missing') as mock_set_defaults, \
             patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"}):
            
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_update_players = mock_update_players

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = {}

            self.mock_set_defaults = mock_set_defaults
            
            yield

    def test_set_roster_id_calls_set_defaults(self, mock_metadata_manager):
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                }
            }
        }

        mock_metadata_manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=1
        )

        self.mock_set_defaults.assert_called_once_with(1)

    def test_set_roster_id_updates_roster_mapping(self, mock_metadata_manager):
        """Test that roster ID is mapped to manager."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                }
            }
        }

        mock_metadata_manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=1
        )

        assert mock_metadata_manager._weekly_roster_ids[1] == "Manager 1"

    def test_set_roster_id_skips_none_roster_id(self, mock_metadata_manager):
        """Test that None roster_id (co-manager) is skipped."""
        mock_metadata_manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=None
        )

        # Should not create any entries
        assert "Manager 1" not in self.mock_manager_cache
        assert not self.mock_fetch_sleeper_data.called

    def test_set_roster_id_fetches_league_settings_week_1(self, mock_metadata_manager):
        """Test that league settings are fetched on week 1."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                }
            }
        }

        mock_metadata_manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=1
        )

        # Should fetch league settings
        assert self.mock_fetch_sleeper_data.called
        assert mock_metadata_manager._use_faab is True
        assert mock_metadata_manager._playoff_week_start == 15

    def test_cache_references_are_consistent(self, mock_metadata_manager):
        """Test that cache references remain consistent."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"settings": {"waiver_type": 1, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "summary": {},
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                }
            }
        }
        

        original_cache = self.mock_manager_cache

        mock_metadata_manager.set_roster_id("Manager 1", "2023", "1", 1)

        # Cache reference should not change
        assert self.mock_manager_cache is original_cache


class TestCacheWeekData:
    """Test cache_week_data method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.validate_caching_preconditions') as mock_validate, \
             patch('patriot_center_backend.managers.manager_metadata_manager.ManagerMetadataManager._ensure_processors_initialized') as mock_ensure_init, \
             patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state') as mock_get_season_state:
            
            self.mock_validate = mock_validate
            self.mock_ensure_init = mock_ensure_init
            self.mock_get_season_state = mock_get_season_state
            
            yield

    def test_cache_week_data_processes_matchups_and_transactions(self, mock_metadata_manager):
        """Test that cache_week_data processes both matchups and transactions."""
        mock_metadata_manager._transaction_processor = MagicMock()
        mock_metadata_manager._matchup_processor = MagicMock()

        mock_metadata_manager.cache_week_data("2023", "1")

        # Should process both
        assert mock_metadata_manager._transaction_processor.scrub_transaction_data.called
        assert mock_metadata_manager._matchup_processor.scrub_matchup_data.called

    def test_cache_week_data_checks_for_reversals(self, mock_metadata_manager):
        """Test that cache_week_data checks for transaction reversals."""
        mock_metadata_manager._transaction_processor = MagicMock()
        mock_metadata_manager._matchup_processor = MagicMock()

        mock_metadata_manager.cache_week_data("2023", "1")

        # Should check for reversals
        assert mock_metadata_manager._transaction_processor.check_for_reverse_transactions.called

    def test_cache_week_data_processes_playoff_data(self, mock_metadata_manager):
        """Test that playoff data is processed during playoff weeks."""
        self.mock_get_season_state.return_value = "playoffs"
        
        mock_metadata_manager._transaction_processor = MagicMock()
        mock_metadata_manager._matchup_processor = MagicMock()

        mock_metadata_manager.cache_week_data("2023", "15")

        # Should process playoff data
        assert mock_metadata_manager._matchup_processor.scrub_playoff_data.called

    def test_cache_week_data_clears_state_after(self, mock_metadata_manager):
        """Test that session state is cleared after processing."""
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        mock_metadata_manager._transaction_processor = MagicMock()
        mock_metadata_manager._matchup_processor = MagicMock()

        mock_metadata_manager.cache_week_data("2023", "1")

        # Should clear processors
        mock_metadata_manager._transaction_processor.clear_session_state.called
        mock_metadata_manager._matchup_processor.clear_session_state.called

        # Should clear state
        assert mock_metadata_manager._year is None
        assert mock_metadata_manager._week is None
        assert mock_metadata_manager._weekly_roster_ids == {}


class TestSetPlayoffPlacements:
    """Test set_playoff_placements method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER.get_manager_cache') as mock_get_manager:
            
            self.mock_manager_cache = {}
            self.mock_get_manager = mock_get_manager
            self.mock_get_manager.return_value = self.mock_manager_cache
            
            yield

    def test_set_playoff_placements_updates_cache(self, mock_metadata_manager):
        """Test that playoff placements are added to cache."""
        placements = {
            "Manager 1": 1,
            "Manager 2": 2
        }
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "overall_data": {
                        "placement": {}
                    }
                }
            }
        })

        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        mock_metadata_manager.set_playoff_placements(placements, "2023")

        assert self.mock_manager_cache["Manager 1"]["summary"]["overall_data"]["placement"]["2023"] == 1

    def test_set_playoff_placements_skips_unknown_managers(self, mock_metadata_manager):
        """Test that unknown managers are skipped."""
        placements = {
            "Unknown Manager": 1
        }

        # Should not raise error
        mock_metadata_manager.set_playoff_placements(placements, "2023")


class TestGetManagersList:
    """Test get_managers_list method."""

    def test_get_managers_list_delegates_to_exporter(self, mock_metadata_manager):
        """Test that get_managers_list delegates to data exporter."""
        mock_metadata_manager._data_exporter = MagicMock()
        mock_metadata_manager._data_exporter.get_managers_list.return_value = {"managers": []}

        result = mock_metadata_manager.get_managers_list(active_only=True)

        mock_metadata_manager._data_exporter.get_managers_list.assert_called_once_with(active_only=True)
        assert result == {"managers": []}


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    def test_get_manager_summary_delegates_to_exporter(self, mock_metadata_manager):
        """Test that get_manager_summary delegates to data exporter."""
        mock_metadata_manager._data_exporter = MagicMock()
        mock_metadata_manager._data_exporter.get_manager_summary.return_value = {"manager_name": "Manager 1"}

        mock_metadata_manager.get_manager_summary("Manager 1", year="2023")

        mock_metadata_manager._data_exporter.get_manager_summary.assert_called_once_with("Manager 1", year="2023")


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    def test_get_head_to_head_delegates_to_exporter(self, mock_metadata_manager):
        """Test that get_head_to_head delegates to data exporter."""
        mock_metadata_manager._data_exporter = MagicMock()
        mock_metadata_manager._data_exporter.get_head_to_head.return_value = {}

        mock_metadata_manager.get_head_to_head("Manager 1", "Manager 2", year="2023")

        mock_metadata_manager._data_exporter.get_head_to_head.assert_called_once_with("Manager 1", "Manager 2", year="2023")


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    def test_get_manager_transactions_delegates_to_exporter(self, mock_metadata_manager):
        """Test that get_manager_transactions delegates to data exporter."""
        mock_metadata_manager._data_exporter = MagicMock()
        mock_metadata_manager._data_exporter.get_manager_transactions.return_value = {}

        mock_metadata_manager.get_manager_transactions("Manager 1", year="2023")

        mock_metadata_manager._data_exporter.get_manager_transactions.assert_called_once_with("Manager 1", year="2023")


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    def test_get_manager_awards_delegates_to_exporter(self, mock_metadata_manager):
        """Test that get_manager_awards delegates to data exporter."""
        mock_metadata_manager._data_exporter = MagicMock()
        mock_metadata_manager._data_exporter.get_manager_awards.return_value = {}

        mock_metadata_manager.get_manager_awards("Manager 1")

        mock_metadata_manager._data_exporter.get_manager_awards.assert_called_once_with("Manager 1")


class TestSave:
    """Test save method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER.save_all_caches') as mock_save_caches:
            
            self.mock_save_caches = mock_save_caches
            
            yield

    def test_save_writes_all_caches(self, mock_metadata_manager):
        """Test that save writes all caches to disk."""
            
        mock_metadata_manager.save()

        assert self.mock_save_caches.called


class TestSetDefaultsIfMissing:
    """Test _set_defaults_if_missing method - unit tests calling function directly."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER.get_manager_cache') as mock_get_manager_cache, \
             patch('patriot_center_backend.managers.manager_metadata_manager.initialize_summary_templates') as mock_init_templates, \
             patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state') as mock_get_season_state, \
             patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template') as mock_init_faab:
            
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_init_templates = mock_init_templates

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            self.mock_init_faab = mock_init_faab


            
            yield

    def test_set_defaults_creates_manager_entry(self, mock_metadata_manager):
        """Test _set_defaults_if_missing creates manager entry if not exists."""
        self.mock_get_season_state.return_value = "return_value"
        
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._use_faab = False
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = []
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        mock_metadata_manager._templates = MagicMock()
        
        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Should create manager entry
        assert "Manager 1" in self.mock_manager_cache
        assert "summary" in self.mock_manager_cache["Manager 1"]
        assert "years" in self.mock_manager_cache["Manager 1"]

        # 4 calls, 1 if its populated, 2 manager, 3 yearly, 4 weekly
        assert len(mock_metadata_manager._templates.mock_calls) == 4

    def test_set_defaults_creates_year_entry(self, mock_metadata_manager):
        """Test _set_defaults_if_missing creates year entry if not exists."""
        self.mock_get_season_state.return_value = "return_value"

        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._use_faab = False
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = []
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        mock_metadata_manager._templates = MagicMock()
            
        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Should create year entry
        assert "2023" in self.mock_manager_cache["Manager 1"]["years"]
        assert "summary" in self.mock_manager_cache["Manager 1"]["years"]["2023"]
        assert "weeks" in self.mock_manager_cache["Manager 1"]["years"]["2023"]

        # Yearly template should be called to be used 
        calls = mock_metadata_manager._templates.__getitem__.call_args_list
        assert call('yearly_summary_template') in calls

    def test_set_defaults_creates_week_entry(self, mock_metadata_manager):
        """Test _set_defaults_if_missing creates week entry with correct template."""
        self.mock_get_season_state.return_value = "regular_season"
            
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._use_faab = False
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = []
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1"}

        mock_metadata_manager._templates = MagicMock()

        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Should create week entry
        assert "1" in self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]
        
        # Non-playoff weekly template should be called to be used
        calls = mock_metadata_manager._templates.__getitem__.call_args_list
        assert call('weekly_summary_template') in calls

    def test_set_defaults_uses_playoff_template_when_not_in_playoffs(self, mock_metadata_manager):
        """Test _set_defaults_if_missing uses playoff template for non-playoff teams."""
        self.mock_get_season_state.return_value = "playoffs"
            
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "15"
        mock_metadata_manager._use_faab = False
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = [2, 3]
        mock_metadata_manager._weekly_roster_ids[1] = "Manager 1"
        
        mock_metadata_manager._templates = MagicMock()
        
        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Check if the not in playoffs template was used and NOT the normal one
        calls = mock_metadata_manager._templates.__getitem__.call_args_list
        assert call('weekly_summary_not_in_playoffs_template') in calls
        assert call('weekly_summary_template') not in calls

    def test_set_defaults_skips_existing_entries(self, mock_metadata_manager):
        """Test _set_defaults_if_missing does not overwrite existing data."""
        
        # Initialize with proper template structure plus custom data
        self.mock_manager_cache.update({
            "Manager 1": {
                "existing": "data",
                "summary": {},
                "years": {}
            }
        })
        self.mock_get_season_state.return_value = "regular_season"
            
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._use_faab = False
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = [2, 3]
        mock_metadata_manager._weekly_roster_ids[1] = "Manager 1"

        mock_metadata_manager._templates = MagicMock()

        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Should not overwrite existing key
        assert self.mock_manager_cache["Manager 1"]["existing"] == "data"

        calls = mock_metadata_manager._templates.__getitem__.call_args_list

        # top level summary template NOT called for
        assert call('top_level_summary_template') not in calls

        # yearly and weekly summary templates called for
        assert call('yearly_summary_template') in calls
        assert call('weekly_summary_template') in calls

    def test_set_defaults_initializes_faab_when_enabled(self, mock_metadata_manager):
        """Test _set_defaults_if_missing initializes FAAB template when FAAB is enabled."""
        self.mock_get_season_state.return_value = "regular_season"

        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._use_faab = True
        mock_metadata_manager._playoff_week_start = 15
        mock_metadata_manager._playoff_roster_ids = []
        mock_metadata_manager._weekly_roster_ids[1] = "Manager 1"

        mock_metadata_manager._templates = MagicMock()

        # Call directly
        mock_metadata_manager._set_defaults_if_missing(1)

        # Should call initialize_faab_template
        self.mock_init_faab.assert_called_once_with("Manager 1", "2023", "1")


class TestClearWeeklyMetadata:
    """Test _clear_weekly_metadata method."""

    def test_clear_weekly_metadata_resets_year_and_week(self, mock_metadata_manager):
        """Test _clear_weekly_metadata resets year and week to None."""
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "5"

        mock_metadata_manager._clear_weekly_metadata()

        assert mock_metadata_manager._year is None
        assert mock_metadata_manager._week is None

    def test_clear_weekly_metadata_special_case_2024_week_17(self, mock_metadata_manager):
        """Test _clear_weekly_metadata clears roster IDs for 2024 week 17."""
        mock_metadata_manager._year = "2024"
        mock_metadata_manager._week = "17"
        mock_metadata_manager._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        mock_metadata_manager._clear_weekly_metadata()

        # Should clear roster IDs for this special case
        assert mock_metadata_manager._weekly_roster_ids == {}
        assert mock_metadata_manager._year is None
        assert mock_metadata_manager._week is None

    def test_clear_weekly_metadata_clears_processor_state(self, mock_metadata_manager):
        """Test _clear_weekly_metadata calls clear_session_state on processors."""
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"

        # Create processor instances
        mock_metadata_manager._transaction_processor = MagicMock()
        mock_metadata_manager._matchup_processor = MagicMock()

        mock_metadata_manager._clear_weekly_metadata()

        # Should call clear_session_state on both processors
        mock_metadata_manager._transaction_processor.clear_session_state.assert_called_once()
        mock_metadata_manager._matchup_processor.clear_session_state.assert_called_once()

    def test_clear_weekly_metadata_handles_no_processors(self, mock_metadata_manager):
        """Test _clear_weekly_metadata handles None processors gracefully."""
        mock_metadata_manager._year = "2023"
        mock_metadata_manager._week = "1"
        mock_metadata_manager._transaction_processor = None
        mock_metadata_manager._matchup_processor = None

        # Should not raise exception
        mock_metadata_manager._clear_weekly_metadata()

        assert mock_metadata_manager._year is None
        assert mock_metadata_manager._week is None