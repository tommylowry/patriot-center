"""
Unit tests for manager_metadata_manager module.

Tests the ManagerMetadataManager class (singleton orchestrator).
All tests mock file I/O and API calls to avoid touching real cache files.
"""
import pytest
from unittest.mock import patch, MagicMock, call

from patriot_center_backend.managers.transaction_processor import TransactionProcessor
from patriot_center_backend.managers.matchup_processor import MatchupProcessor


@pytest.fixture(autouse=True)
def patch_caches():
    with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}), \
         patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER', MagicMock()):
        yield


@pytest.fixture
def manager():
    """Create DataExporter instance with sample caches."""
    from patriot_center_backend.managers.manager_metadata_manager import ManagerMetadataManager
    return ManagerMetadataManager()


class TestManagerMetadataManagerInit:
    """Test ManagerMetadataManager initialization."""

    def test_init_creates_data_exporter(self):
        """Test that __init__ creates DataExporter instance."""
        from patriot_center_backend.managers.manager_metadata_manager import ManagerMetadataManager
        mgr = ManagerMetadataManager()

        assert mgr._data_exporter is not None

    def test_init_does_not_create_processors(self):
        """Test that __init__ does not create processors (lazy initialization)."""
        from patriot_center_backend.managers.manager_metadata_manager import ManagerMetadataManager
        mgr = ManagerMetadataManager()

        assert mgr._transaction_processor is None
        assert mgr._matchup_processor is None

    def test_singleton_pattern(self):
        """Test that get_manager_metadata_manager returns singleton."""
        from patriot_center_backend.managers.manager_metadata_manager import get_manager_metadata_manager
        
        import patriot_center_backend.managers.manager_metadata_manager as mmm
        mmm._manager_metadata_instance = None

        mgr1 = get_manager_metadata_manager()
        mgr2 = get_manager_metadata_manager()

        # Should be same instance
        assert mgr1 is mgr2


class TestEnsureProcessorsInitialized:
    """Test _ensure_processors_initialized method."""

    def test_initializes_processors_on_first_call(self, manager):
        """Test that processors are created on first call."""
        manager._use_faab = True
        manager._playoff_week_start = 15

        manager._ensure_processors_initialized()

        assert manager._transaction_processor is not None
        assert manager._matchup_processor is not None

    def test_does_not_reinitialize_processors(self, manager):
        """Test that processors are not recreated on subsequent calls."""
        manager._use_faab = True
        manager._playoff_week_start = 15

        manager._ensure_processors_initialized()
        first_transaction = manager._transaction_processor
        first_matchup = manager._matchup_processor

        manager._ensure_processors_initialized()

        # Should be same instances
        assert manager._transaction_processor is first_transaction
        assert manager._matchup_processor is first_matchup

    def test_raises_if_use_faab_not_set(self, manager):
        """Test that ValueError is raised if use_faab not set."""
        manager._use_faab = None

        with pytest.raises(ValueError, match="Cannot initialize processors before use_faab is set"):
            manager._ensure_processors_initialized()


class TestSetRosterId:
    """Test set_roster_id method."""

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_roster_id_calls_set_defaults(self, mock_season_state, mock_fetch):
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        mock_season_state.return_value = "regular_season"

        from patriot_center_backend.managers.templates import initialize_summary_templates
        templates = initialize_summary_templates(use_faab=True)

        sample_manager_cache = {
            "Manager 1": {
                "summary": templates['top_level_summary_template'],
                "years": {
                    "2023": {"summary": {}, "roster_id": None, "weeks": {}}
                }
            }
        }

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.manager_metadata_manager import ManagerMetadataManager
            set_roster_id_calls_set_defaults_manager = ManagerMetadataManager()

            with patch.object(set_roster_id_calls_set_defaults_manager, '_set_defaults_if_missing') as mock_defaults:
                # Need to set up minimal cache structure since _set_defaults_if_missing is mocked
                set_roster_id_calls_set_defaults_manager.set_roster_id(
                    manager="Manager 1",
                    year="2023",
                    week="1",
                    roster_id=1
                )

                mock_defaults.assert_called_once_with(1)

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_set_roster_id_updates_roster_mapping(self, mock_initialize_faab_template, mock_fetch, manager):
        """Test that roster ID is mapped to manager."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=1
        )

        assert manager._weekly_roster_ids[1] == "Manager 1"

    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    def test_set_roster_id_skips_none_roster_id(self, mock_fetch):
        """Test that None roster_id (co-manager) is skipped."""
        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            set_roster_id_skips_none_roster_id_manager = manager_metadata_manager.ManagerMetadataManager()
            set_roster_id_skips_none_roster_id_manager.set_roster_id(
                manager="Manager 1",
                year="2023",
                week="1",
                roster_id=None
            )

            # Should not create any entries
            assert "Manager 1" not in manager_metadata_manager.MANAGER_CACHE
            assert not mock_fetch.called

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_set_roster_id_fetches_league_settings_week_1(self, mock_initialize_faab_template, mock_fetch, manager):
        """Test that league settings are fetched on week 1."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        manager.set_roster_id(
            manager="Manager 1",
            year="2023",
            week="1",
            roster_id=1
        )

        # Should fetch league settings
        assert mock_fetch.called
        assert manager._use_faab is True
        assert manager._playoff_week_start == 15


class TestCacheWeekData:
    """Test cache_week_data method."""

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.validate_caching_preconditions')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_cache_week_data_processes_matchups_and_transactions(self, mock_initialize_faab_template, mock_validate, mock_fetch, manager):
        """Test that cache_week_data processes both matchups and transactions."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        manager.set_roster_id("Manager 1", "2023", "1", 1)

        with patch.object(manager, '_ensure_processors_initialized'):
            manager._transaction_processor = MagicMock()
            manager._matchup_processor = MagicMock()

            manager.cache_week_data("2023", "1")

            # Should process both
            assert manager._transaction_processor.scrub_transaction_data.called
            assert manager._matchup_processor.scrub_matchup_data.called

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.validate_caching_preconditions')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_cache_week_data_checks_for_reversals(self, mock_initialize_faab_template, mock_validate, mock_fetch, manager):
        """Test that cache_week_data checks for transaction reversals."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        manager.set_roster_id("Manager 1", "2023", "1", 1)

        with patch.object(manager, '_ensure_processors_initialized'):
            manager._transaction_processor = MagicMock()
            manager._matchup_processor = MagicMock()

            manager.cache_week_data("2023", "1")

            # Should check for reversals
            assert manager._transaction_processor.check_for_reverse_transactions.called

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.validate_caching_preconditions')
    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_cache_week_data_processes_playoff_data(self, mock_initialize_faab_template, mock_season, mock_validate, mock_fetch, manager):
        """Test that playoff data is processed during playoff weeks."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        mock_season.return_value = "playoffs"

        manager.set_roster_id("Manager 1", "2023", "15", 1)

        with patch.object(manager, '_ensure_processors_initialized'):
            manager._transaction_processor = MagicMock()
            manager._matchup_processor = MagicMock()

            manager.cache_week_data("2023", "15")

            # Should process playoff data
            assert manager._matchup_processor.scrub_playoff_data.called

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.validate_caching_preconditions')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_cache_week_data_clears_state_after(self, mock_initialize_faab_template, mock_validate, mock_fetch, manager):
        """Test that session state is cleared after processing."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        manager.set_roster_id("Manager 1", "2023", "1", 1)

        with patch.object(manager, '_ensure_processors_initialized'):
            manager._transaction_processor = MagicMock()
            manager._matchup_processor = MagicMock()

            manager.cache_week_data("2023", "1")

            # Should clear state
            assert manager._year is None
            assert manager._week is None
            assert manager._weekly_roster_ids == {}


class TestSetPlayoffPlacements:
    """Test set_playoff_placements method."""

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_set_playoff_placements_updates_cache(self, mock_initialize_faab_template, mock_fetch):
        """Test that playoff placements are added to cache."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 2, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]
        placements = {
            "Manager 1": 1,
            "Manager 2": 2
        }

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            set_playoff_placements_updates_cache_manager = manager_metadata_manager.ManagerMetadataManager()
            set_playoff_placements_updates_cache_manager.set_roster_id("Manager 1", "2023", "1", 1)

            set_playoff_placements_updates_cache_manager.set_playoff_placements(placements, "2023")

            assert manager_metadata_manager.MANAGER_CACHE["Manager 1"]["summary"]["overall_data"]["placement"]["2023"] == 1

    def test_set_playoff_placements_skips_unknown_managers(self, manager):
        """Test that unknown managers are skipped."""
        placements = {
            "Unknown Manager": 1
        }

        # Should not raise error
        manager.set_playoff_placements(placements, "2023")


class TestGetManagersList:
    """Test get_managers_list method."""

    def test_get_managers_list_delegates_to_exporter(self, manager):
        """Test that get_managers_list delegates to data exporter."""
        manager._data_exporter = MagicMock()
        manager._data_exporter.get_managers_list.return_value = {"managers": []}

        result = manager.get_managers_list(active_only=True)

        manager._data_exporter.get_managers_list.assert_called_once_with(active_only=True)
        assert result == {"managers": []}


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    def test_get_manager_summary_delegates_to_exporter(self, manager):
        """Test that get_manager_summary delegates to data exporter."""
        manager._data_exporter = MagicMock()
        manager._data_exporter.get_manager_summary.return_value = {"manager_name": "Manager 1"}

        result = manager.get_manager_summary("Manager 1", year="2023")

        manager._data_exporter.get_manager_summary.assert_called_once_with("Manager 1", year="2023")


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    def test_get_head_to_head_delegates_to_exporter(self, manager):
        """Test that get_head_to_head delegates to data exporter."""
        manager._data_exporter = MagicMock()
        manager._data_exporter.get_head_to_head.return_value = {}

        result = manager.get_head_to_head("Manager 1", "Manager 2", year="2023")

        manager._data_exporter.get_head_to_head.assert_called_once_with("Manager 1", "Manager 2", year="2023")


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    def test_get_manager_transactions_delegates_to_exporter(self, manager):
        """Test that get_manager_transactions delegates to data exporter."""
        manager._data_exporter = MagicMock()
        manager._data_exporter.get_manager_transactions.return_value = {}

        result = manager.get_manager_transactions("Manager 1", year="2023")

        manager._data_exporter.get_manager_transactions.assert_called_once_with("Manager 1", year="2023")


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    def test_get_manager_awards_delegates_to_exporter(self, manager):
        """Test that get_manager_awards delegates to data exporter."""
        manager._data_exporter = MagicMock()
        manager._data_exporter.get_manager_awards.return_value = {}

        result = manager.get_manager_awards("Manager 1")

        manager._data_exporter.get_manager_awards.assert_called_once_with("Manager 1")


class TestSave:
    """Test save method."""

    def test_save_writes_all_caches(self):
        """Test that save writes all caches to disk."""

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {"Manager 1": {}}), \
             patch('patriot_center_backend.managers.manager_metadata_manager.CACHE_MANAGER', MagicMock()):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()
            
            mgr.save()

            assert manager_metadata_manager.CACHE_MANAGER.save_all_caches.called


class TestSetDefaultsIfMissing:
    """Test _set_defaults_if_missing method - unit tests calling function directly."""

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_defaults_creates_manager_entry(self, mock_season_state):
        """Test _set_defaults_if_missing creates manager entry if not exists."""
        mock_season_state.return_value = "regular_season"

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()

            mgr._year = "2023"
            mgr._week = "1"
            mgr._use_faab = False
            mgr._playoff_week_start = 15
            mgr._playoff_roster_ids = []
            mgr._weekly_roster_ids[1] = "Manager 1"
            
            # Call directly
            mgr._set_defaults_if_missing(1)

            # Should create manager entry
            assert "Manager 1" in manager_metadata_manager.MANAGER_CACHE
            assert "summary" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]
            assert "years" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_defaults_creates_year_entry(self, mock_season_state):
        """Test _set_defaults_if_missing creates year entry if not exists."""
        mock_season_state.return_value = "regular_season"
        
        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()

            mgr._year = "2023"
            mgr._week = "1"
            mgr._use_faab = False
            mgr._playoff_week_start = 15
            mgr._playoff_roster_ids = []
            mgr._weekly_roster_ids[1] = "Manager 1"
            
            # Call directly
            mgr._set_defaults_if_missing(1)

            # Should create year entry
            assert "2023" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]
            assert "summary" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]["2023"]
            assert "weeks" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]["2023"]

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_defaults_creates_week_entry(self, mock_season_state):
        """Test _set_defaults_if_missing creates week entry with correct template."""
        mock_season_state.return_value = "regular_season"

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()
            
            mgr._year = "2023"
            mgr._week = "1"
            mgr._use_faab = False
            mgr._playoff_week_start = 15
            mgr._playoff_roster_ids = []
            mgr._weekly_roster_ids[1] = "Manager 1"

            # Call directly
            mgr._set_defaults_if_missing(1)

            # Should create week entry with matchup_data
            assert "1" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]
            assert "matchup_data" in manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_defaults_uses_playoff_template_when_not_in_playoffs(self, mock_season_state):
        """Test _set_defaults_if_missing uses playoff template for non-playoff teams."""
        mock_season_state.return_value = "playoffs"

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()
            
            mgr._year = "2023"
            mgr._week = "15"
            mgr._use_faab = False
            mgr._playoff_week_start = 15
            mgr._playoff_roster_ids = [2, 3]
            mgr._weekly_roster_ids[1] = "Manager 1"

            # Call directly
            mgr._set_defaults_if_missing(1)

            # Should use weekly_summary_not_in_playoffs_template (empty matchup_data)
            week_data = manager_metadata_manager.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["15"]
            assert week_data["matchup_data"] == {}

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    def test_set_defaults_skips_existing_entries(self, mock_season_state):
        """Test _set_defaults_if_missing does not overwrite existing data."""
        from patriot_center_backend.managers.templates import initialize_summary_templates

        # Initialize with proper template structure plus custom data
        templates = initialize_summary_templates(use_faab=True)
        manager_cache = {
            "Manager 1": {
                "existing": "data",
                "summary": templates['top_level_summary_template'],
                "years": {}
            }
        }

        mock_season_state.return_value = "regular_season"
        
        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()
            
            mgr._year = "2023"
            mgr._week = "1"
            mgr._use_faab = False
            mgr._playoff_week_start = 15
            mgr._playoff_roster_ids = [2, 3]
            mgr._weekly_roster_ids[1] = "Manager 1"

            # Call directly
            mgr._set_defaults_if_missing(1)

            # Should not overwrite existing key
            assert manager_metadata_manager.MANAGER_CACHE["Manager 1"]["existing"] == "data"

    @patch('patriot_center_backend.managers.manager_metadata_manager.get_season_state')
    @patch('patriot_center_backend.managers.manager_metadata_manager.initialize_faab_template')
    def test_set_defaults_initializes_faab_when_enabled(self, mock_init_faab, mock_season_state, manager):
        """Test _set_defaults_if_missing initializes FAAB template when FAAB is enabled."""
        mock_season_state.return_value = "regular_season"
        mock_init_faab.return_value = None

        manager._year = "2023"
        manager._week = "1"
        manager._use_faab = True
        manager._playoff_week_start = 15
        manager._playoff_roster_ids = []
        manager._weekly_roster_ids[1] = "Manager 1"

        # Call directly
        manager._set_defaults_if_missing(1)

        # Should call initialize_faab_template
        assert mock_init_faab.called
        mock_init_faab.assert_called_once_with("Manager 1", "2023", "1")


class TestCacheIntegrity:
    """Test cache integrity and consistency."""

    @patch('patriot_center_backend.managers.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Manager 1": "manager1_user"})
    @patch('patriot_center_backend.managers.manager_metadata_manager.fetch_sleeper_data')
    def test_cache_references_are_consistent(self, mock_fetch, manager):
        """Test that cache references remain consistent."""
        mock_fetch.side_effect = [
            {"settings": {"waiver_type": 1, "playoff_week_start": 15}},
            {"user_id": "user123"}
        ]

        with patch('patriot_center_backend.managers.manager_metadata_manager.MANAGER_CACHE', {}):
            from patriot_center_backend.managers import manager_metadata_manager
            mgr = manager_metadata_manager.ManagerMetadataManager()

            original_cache = manager_metadata_manager.MANAGER_CACHE

            mgr.set_roster_id("Manager 1", "2023", "1", 1)

            # Cache reference should not change
            assert manager_metadata_manager.MANAGER_CACHE is original_cache


class TestClearWeeklyMetadata:
    """Test _clear_weekly_metadata method."""

    def test_clear_weekly_metadata_resets_year_and_week(self, manager):
        """Test _clear_weekly_metadata resets year and week to None."""
        manager._year = "2023"
        manager._week = "5"

        manager._clear_weekly_metadata()

        assert manager._year is None
        assert manager._week is None

    def test_clear_weekly_metadata_special_case_2024_week_17(self, manager):
        """Test _clear_weekly_metadata clears roster IDs for 2024 week 17."""
        manager._year = "2024"
        manager._week = "17"
        manager._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        manager._clear_weekly_metadata()

        # Should clear roster IDs for this special case
        assert manager._weekly_roster_ids == {}
        assert manager._year is None
        assert manager._week is None

    def test_clear_weekly_metadata_does_not_clear_roster_ids_for_other_weeks(self, manager):
        """Test _clear_weekly_metadata does not clear roster IDs for other weeks."""
        manager._year = "2024"
        manager._week = "5"
        manager._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        manager._clear_weekly_metadata()

        # Should NOT clear roster IDs (not week 17)
        assert manager._weekly_roster_ids == {1: "Manager 1", 2: "Manager 2"}
        assert manager._year is None
        assert manager._week is None

    @patch.object(MatchupProcessor, 'clear_session_state')
    @patch.object(TransactionProcessor, 'clear_session_state')
    def test_clear_weekly_metadata_clears_processor_state(self, mock_trans_clear, mock_matchup_clear, manager):
        """Test _clear_weekly_metadata calls clear_session_state on processors."""
        manager._year = "2023"
        manager._week = "1"

        # Create processor instances
        manager._transaction_processor = TransactionProcessor(False)
        manager._matchup_processor = MatchupProcessor(15)

        manager._clear_weekly_metadata()

        # Should call clear_session_state on both processors
        mock_trans_clear.assert_called_once()
        mock_matchup_clear.assert_called_once()

    def test_clear_weekly_metadata_handles_no_processors(self, manager):
        """Test _clear_weekly_metadata handles None processors gracefully."""
        manager._year = "2023"
        manager._week = "1"
        manager._transaction_processor = None
        manager._matchup_processor = None

        # Should not raise exception
        manager._clear_weekly_metadata()

        assert manager._year is None
        assert manager._week is None
