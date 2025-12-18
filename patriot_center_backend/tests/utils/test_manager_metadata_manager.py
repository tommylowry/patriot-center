"""
Unit tests for utils/manager_metadata_manager.py - Manager metadata cache management.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from decimal import Decimal


class TestManagerMetadataManagerInit:
    """Test ManagerMetadataManager initialization."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_initializes_with_empty_cache(self, mock_load_cache, mock_load_player_ids):
        """Test manager initializes with empty cache structure."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        # load_cache is called twice: once for manager cache, once for transaction_id cache
        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        assert manager._cache == {}
        assert manager._transaction_id_cache == {}
        assert manager._use_faab is None
        assert manager._playoff_week_start is None
        assert manager._weekly_roster_ids == {}
        assert manager._year is None
        assert manager._week is None
        assert manager._playoff_roster_ids == {}

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_loads_existing_cache_on_init(self, mock_load_cache, mock_load_player_ids):
        """Test manager loads existing cache from disk on initialization."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        existing_manager_cache = {
            "Tommy": {
                "summary": {"matchup_data": {}},
                "years": {}
            }
        }
        existing_transaction_cache = {"tx123": {"year": "2024"}}
        # First call loads transaction cache, second loads manager cache (order in __init__)
        mock_load_cache.side_effect = [existing_transaction_cache, existing_manager_cache]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        assert manager._cache == existing_manager_cache
        assert manager._transaction_id_cache == existing_transaction_cache

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_loads_player_ids_on_init(self, mock_load_cache, mock_load_player_ids):
        """Test manager loads player IDs on initialization."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        player_ids = {"7547": {"full_name": "Amon-Ra St. Brown"}}
        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = player_ids

        manager = ManagerMetadataManager()

        assert manager._player_ids == player_ids


class TestSetRosterId:
    """Test set_roster_id method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    def test_sets_roster_id_for_new_manager(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test sets roster ID for a new manager not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        # Mock league settings fetch
        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings
            ({"user_id": "user_123"}, 200)  # User data
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)

        assert manager._weekly_roster_ids[1] == "Tommy"
        assert manager._cache["Tommy"]["years"]["2024"]["roster_id"] == 1
        assert manager._cache["Tommy"]["summary"]["user_id"] == "user_123"
        assert manager._use_faab is True
        assert manager._playoff_week_start == 15

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    def test_skips_none_roster_id_for_comanagers(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test skips processing when roster_id is None (co-manager scenario)."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", None)

        # Should not add to cache or weekly roster IDs
        assert "Tommy" not in manager._cache
        assert len(manager._weekly_roster_ids) == 0

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    def test_fetches_league_settings_on_week_1(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test fetches league settings on week 1."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 1, "playoff_week_start": 14}}, 200),
            ({"user_id": "user_123"}, 200)
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)

        assert manager._use_faab is False  # waiver_type 1 means no FAAB
        assert manager._playoff_week_start == 14

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {})
    def test_raises_error_when_manager_username_not_found(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test raises error when manager username mapping is missing."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.return_value = ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200)

        manager = ManagerMetadataManager()

        with pytest.raises(ValueError, match="No username mapping found for manager Unknown"):
            manager.set_roster_id("Unknown", "2024", "1", 1)

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    def test_raises_error_when_user_fetch_fails(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test raises error when user data fetch fails."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),
            ({"error": "not found"}, 404)
        ]

        manager = ManagerMetadataManager()

        with pytest.raises(ValueError, match="Failed to fetch user data for manager Tommy"):
            manager.set_roster_id("Tommy", "2024", "1", 1)


class TestCacheWeekData:
    """Test cache_week_data method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    def test_raises_error_when_no_roster_ids_cached(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test raises error when trying to cache with no roster IDs set."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"

        with pytest.raises(ValueError, match="No roster IDs cached"):
            manager.cache_week_data("2024", "1")

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    def test_raises_error_with_odd_number_of_rosters(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test raises error when odd number of roster IDs cached."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),
            ({"user_id": "user_123"}, 200)
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)

        with pytest.raises(ValueError, match="Odd number of roster IDs cached"):
            manager.cache_week_data("2024", "1")

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_successfully_caches_week_data_with_transactions_and_matchups(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test successfully caches week data with transactions and matchups."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {
            "7547": {"full_name": "Amon-Ra St. Brown"}
        }

        # Mock responses: league settings (x2 because week==1 always fetches), users, transactions, matchups
        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Tommy)
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Mike, week==1 always fetches)
            ({"user_id": "user_456"}, 200),  # Mike user
            ([], 200),  # Transactions (empty list is correct for transactions endpoint)
            ([  # Matchups
                {"roster_id": 1, "matchup_id": 1, "points": 120.5},
                {"roster_id": 2, "matchup_id": 1, "points": 115.3}
            ], 200)
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)
        manager.set_roster_id("Mike", "2024", "1", 2)

        manager.cache_week_data("2024", "1")

        # Verify matchup data was cached
        assert manager._cache["Tommy"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["opponent_manager"] == "Mike"
        assert manager._cache["Tommy"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["points_for"] == 120.5
        assert manager._cache["Tommy"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["result"] == "win"

        assert manager._cache["Mike"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["opponent_manager"] == "Tommy"
        assert manager._cache["Mike"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["points_against"] == 120.5
        assert manager._cache["Mike"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["result"] == "loss"

        # Verify metadata cleared
        assert manager._year is None
        assert manager._week is None


class TestTransactionProcessing:
    """Test transaction processing methods."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_processes_add_transaction(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes add transaction correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {
            "7547": {"full_name": "Amon-Ra St. Brown"}
        }

        add_transaction = {
            "type": "free_agent",
            "status": "complete",
            "transaction_id": "tx123",
            "adds": {"7547": 1},
            "drops": None,
            "settings": {"waiver_bid": 15}
        }

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Tommy)
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Mike, week==1 always fetches)
            ({"user_id": "user_456"}, 200),  # Mike user
            ([add_transaction], 200),  # Transactions
            ([{"roster_id": 1, "matchup_id": 1, "points": 120.5}, {"roster_id": 2, "matchup_id": 1, "points": 115.3}], 200)  # Matchups
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)
        manager.set_roster_id("Mike", "2024", "1", 2)
        manager.cache_week_data("2024", "1")

        # Verify add was processed
        assert manager._cache["Tommy"]["summary"]["transactions"]["adds"]["total"] == 1
        assert manager._cache["Tommy"]["summary"]["transactions"]["adds"]["players"]["Amon-Ra St. Brown"] == 1

        # Verify FAAB was processed
        assert manager._cache["Tommy"]["summary"]["transactions"]["faab"]["total_lost_or_gained"] == -15
        assert manager._cache["Tommy"]["summary"]["transactions"]["faab"]["players"]["Amon-Ra St. Brown"] == 15

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_processes_drop_transaction(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes drop transaction correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {
            "7547": {"full_name": "Amon-Ra St. Brown"}
        }

        drop_transaction = {
            "type": "free_agent",
            "status": "complete",
            "transaction_id": "tx124",
            "adds": None,
            "drops": {"7547": 1}
        }

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Tommy)
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Mike, week==1 always fetches)
            ({"user_id": "user_456"}, 200),  # Mike user
            ([drop_transaction], 200),  # Transactions
            ([{"roster_id": 1, "matchup_id": 1, "points": 120.5}, {"roster_id": 2, "matchup_id": 1, "points": 115.3}], 200)  # Matchups
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)
        manager.set_roster_id("Mike", "2024", "1", 2)
        manager.cache_week_data("2024", "1")

        # Verify drop was processed
        assert manager._cache["Tommy"]["summary"]["transactions"]["drops"]["total"] == 1
        assert manager._cache["Tommy"]["summary"]["transactions"]["drops"]["players"]["Amon-Ra St. Brown"] == 1

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_processes_trade_transaction(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes trade transaction correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {
            "7547": {"full_name": "Amon-Ra St. Brown"},
            "4866": {"full_name": "Travis Kelce"}
        }

        trade_transaction = {
            "type": "trade",
            "status": "complete",
            "transaction_id": "tx125",
            "roster_ids": [1, 2],
            "adds": {"7547": 1, "4866": 2},  # Tommy gets 7547, Mike gets 4866
            "drops": {"7547": 2, "4866": 1},  # Tommy sends 4866, Mike sends 7547
            "draft_picks": []
        }

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Tommy)
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Mike, week==1 always fetches)
            ({"user_id": "user_456"}, 200),  # Mike user
            ([trade_transaction], 200),  # Transactions
            ([{"roster_id": 1, "matchup_id": 1, "points": 120.5}, {"roster_id": 2, "matchup_id": 1, "points": 115.3}], 200)  # Matchups
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)
        manager.set_roster_id("Mike", "2024", "1", 2)
        manager.cache_week_data("2024", "1")

        # Verify trade was processed for Tommy
        assert manager._cache["Tommy"]["summary"]["transactions"]["trades"]["total"] == 1
        assert manager._cache["Tommy"]["summary"]["transactions"]["trades"]["trade_partners"]["Mike"] == 1
        assert "Amon-Ra St. Brown" in manager._cache["Tommy"]["summary"]["transactions"]["trades"]["trade_players_acquired"]
        assert "Travis Kelce" in manager._cache["Tommy"]["summary"]["transactions"]["trades"]["trade_players_sent"]

        # Verify trade was processed for Mike
        assert manager._cache["Mike"]["summary"]["transactions"]["trades"]["total"] == 1
        assert manager._cache["Mike"]["summary"]["transactions"]["trades"]["trade_partners"]["Tommy"] == 1

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_skips_failed_transactions(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test skips transactions with failed status."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._weekly_roster_ids = {1: "Tommy"}

        failed_transaction = {
            "type": "free_agent",
            "status": "failed",
            "transaction_id": "tx126",
            "adds": {"7547": 1}
        }

        # Should not raise error or process
        manager._process_transaction(failed_transaction)

        # Cache should remain empty
        assert "Tommy" not in manager._cache


class TestMatchupProcessing:
    """Test matchup processing methods."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_processes_tie_matchup(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes tie matchup correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Tommy)
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings (Mike, week==1 always fetches)
            ({"user_id": "user_456"}, 200),  # Mike user
            ([], 200),  # Transactions (empty list is correct)
            ([  # Matchups with tie
                {"roster_id": 1, "matchup_id": 1, "points": 120.5},
                {"roster_id": 2, "matchup_id": 1, "points": 120.5}
            ], 200)
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "1", 1)
        manager.set_roster_id("Mike", "2024", "1", 2)
        manager.cache_week_data("2024", "1")

        # Verify tie was recorded
        assert manager._cache["Tommy"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["result"] == "tie"
        assert manager._cache["Mike"]["years"]["2024"]["weeks"]["1"]["matchup_data"]["result"] == "tie"
        assert manager._cache["Tommy"]["summary"]["matchup_data"]["overall"]["ties"]["total"] == 1
        assert manager._cache["Mike"]["summary"]["matchup_data"]["overall"]["ties"]["total"] == 1


class TestPlayoffProcessing:
    """Test playoff data processing."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user"})
    def test_processes_playoff_appearances(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes playoff appearances correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),  # League settings
            ({"user_id": "user_123"}, 200),  # Tommy user
            ({"user_id": "user_456"}, 200),  # Mike user
            ([], 200),  # Transactions
            ([  # Matchups
                {"roster_id": 1, "matchup_id": 1, "points": 120.5},
                {"roster_id": 2, "matchup_id": 1, "points": 115.3}
            ], 200)
        ]

        manager = ManagerMetadataManager()

        # Set playoff roster IDs before setting roster IDs
        playoff_roster_ids = {
            "round_roster_ids": [1, 2],
            "first_place_id": 1,
            "second_place_id": 2,
            "third_place_id": None
        }

        manager.set_roster_id("Tommy", "2024", "15", 1, playoff_roster_ids)  # Week 15 (playoff week)
        manager.set_roster_id("Mike", "2024", "15", 2, playoff_roster_ids)

        manager.cache_week_data("2024", "15")

        # Verify playoff appearance recorded
        assert "2024" in manager._cache["Tommy"]["summary"]["overall_data"]["playoff_appearances"]
        assert "2024" in manager._cache["Mike"]["summary"]["overall_data"]["playoff_appearances"]

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.manager_metadata_manager.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Mike": "mike_user", "Jake": "jake_user", "Owen": "owen_user"})
    def test_processes_playoff_placements(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test processes playoff placements correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.side_effect = [
            ({"settings": {"waiver_type": 2, "playoff_week_start": 15}}, 200),
            ({"user_id": "user_123"}, 200),
            ({"user_id": "user_456"}, 200),
            ({"user_id": "user_789"}, 200),
            ({"user_id": "user_999"}, 200),
            ([], 200),  # Transactions
            ([  # Matchups - need even number of rosters
                {"roster_id": 1, "matchup_id": 1, "points": 130.5},
                {"roster_id": 2, "matchup_id": 1, "points": 115.3},
                {"roster_id": 3, "matchup_id": 2, "points": 110.0},
                {"roster_id": 4, "matchup_id": 2, "points": 105.0}
            ], 200)
        ]

        manager = ManagerMetadataManager()
        manager.set_roster_id("Tommy", "2024", "17", 1)  # Championship week
        manager.set_roster_id("Mike", "2024", "17", 2)
        manager.set_roster_id("Jake", "2024", "17", 3)
        manager.set_roster_id("Owen", "2024", "17", 4)

        # Set playoff results using the new method
        placements = {
            "Tommy": 1,
            "Mike": 2,
            "Jake": 3
        }
        manager.set_playoff_placements(placements, "2024")

        # Verify placements recorded
        assert manager._cache["Tommy"]["summary"]["overall_data"]["placement"]["2024"] == 1
        assert manager._cache["Mike"]["summary"]["overall_data"]["placement"]["2024"] == 2
        assert manager._cache["Jake"]["summary"]["overall_data"]["placement"]["2024"] == 3


class TestSaveAndLoad:
    """Test save and load methods."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.save_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_save_calls_save_cache_with_cache_data(self, mock_load_cache, mock_load_player_ids, mock_save_cache):
        """Test save method calls save_cache with both manager and transaction cache data."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        manager_cache = {"Tommy": {"summary": {}, "years": {}}}
        transaction_cache = {"tx123": {"year": "2024"}}
        # First call loads transaction cache, second loads manager cache (order in __init__)
        mock_load_cache.side_effect = [transaction_cache, manager_cache]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager.save()

        # Should save both caches
        assert mock_save_cache.call_count == 2
        # Verify both caches are saved (manager._cache and manager._transaction_id_cache)
        call_args_list = mock_save_cache.call_args_list
        # First call should be manager cache
        assert call_args_list[0][0][1] == manager_cache
        # Second call should be transaction cache
        assert call_args_list[1][0][1] == transaction_cache


class TestHelperMethods:
    """Test internal helper methods."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    def test_get_season_state_returns_regular_season(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test _get_season_state returns regular_season for weeks before playoffs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        mock_fetch.return_value = ({"settings": {"playoff_week_start": 15}}, 200)

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "10"
        manager._playoff_week_start = 15

        assert manager._get_season_state() == "regular_season"

    @patch('patriot_center_backend.utils.manager_metadata_manager.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    @patch('patriot_center_backend.utils.manager_metadata_manager.LEAGUE_IDS', {2024: "league_123"})
    def test_get_season_state_returns_playoffs(self, mock_load_cache, mock_load_player_ids, mock_fetch):
        """Test _get_season_state returns playoffs for weeks during playoffs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "15"
        manager._playoff_week_start = 15

        assert manager._get_season_state() == "playoffs"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_draft_pick_decipher_formats_correctly(self, mock_load_cache, mock_load_player_ids):
        """Test _draft_pick_decipher formats draft pick strings correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._weekly_roster_ids = {1: "Tommy"}

        draft_pick = {
            "season": "2025",
            "round": 3,
            "roster_id": 1
        }

        result = manager._draft_pick_decipher(draft_pick)

        assert result == "Tommy's 2025 Round 3 Draft Pick"
