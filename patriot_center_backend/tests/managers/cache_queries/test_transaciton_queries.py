
from copy import deepcopy
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.cache_queries.transaction_queries import (
    get_trade_history_between_two_managers,
    get_transaction_details_from_cache,
)


@pytest.fixture
def mock_transaction_ids_cache():
    """Create a sample transaction IDs cache."""
    return {
        "trade1": {
            "year": "2023",
            "week": "5",
            "managers_involved": ["Manager 1", "Manager 2"],
            "trade_details": {}
        }
    }


class TestGetTradeHistoryBetweenTwoManagers:
    """Test get_trade_history_between_two_managers function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache, mock_transaction_ids_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.cache_queries.transaction_queries.CACHE_MANAGER.get_transaction_ids_cache') as mock_get_trans_ids, \
             patch('patriot_center_backend.managers.cache_queries.transaction_queries.get_trade_card') as mock_get_trade_card:
            
            self.mock_trade_card_value = {}
            mock_get_trade_card.return_value = self.mock_trade_card_value
            
            mock_get_trans_ids.return_value = mock_transaction_ids_cache
            
            self.mock_manager_cache = mock_manager_cache
            mock_get_manager.return_value = self.mock_manager_cache

            yield

    def test_trade_history(self):
        """Test getting trade history between managers."""
        self.mock_trade_card_value.update({
            "year": "2023",
            "week": "5",
            "managers_involved": ["Manager 1", "Manager 2"]
        })

        # Add transaction_ids to the cache
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"] = {
            "trades": {"transaction_ids": ["trade1"]}
        }

        result = get_trade_history_between_two_managers("Manager 1", "Manager 2", {})

        assert isinstance(result, list)


class TestGetTransactionDetailsFromCache:
    """Test get_transaction_details_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.cache_queries.transaction_queries.extract_dict_data') as mock_extract_dict_data:
            
            mock_extract_dict_data.return_value = []
            
            self.mock_manager_cache = mock_manager_cache
            mock_get_manager.return_value = self.mock_manager_cache

            yield

    def test_all_time_transactions(self):
        """Test getting all-time transaction stats."""
        result = get_transaction_details_from_cache(None, "Manager 1", {})

        assert result["trades"]["total"] == 5
        assert result["adds"]["total"] == 10
        assert result["drops"]["total"] == 10

    def test_single_season_transactions(self):
        """Test getting stats for specific season."""
        result = get_transaction_details_from_cache("2023", "Manager 1", {})

        assert result["trades"]["total"] == 2
        assert result["adds"]["total"] == 5
        assert result["drops"]["total"] == 5

    def test_transactions_with_faab_data(self):
        """Test getting transaction stats when FAAB data exists."""
        
        # Setup cache with FAAB data
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"] = {
            "total_lost_or_gained": -150,
            "players": {
                "Player A": {"num_bids_won": 2, "total_faab_spent": 100},
                "Player B": {"num_bids_won": 1, "total_faab_spent": 50}
            },
            "traded_away": {
                "total": 25,
                "trade_partners": {"Manager 2": 25}
            },
            "acquired_from": {
                "total": 30,
                "trade_partners": {"Manager 2": 30}
            }
        }

        result = get_transaction_details_from_cache(None, "Manager 1", {})

        # Assert FAAB summary was created
        assert "faab" in result
        assert result["faab"]["total_spent"] == 150  # abs(-150)
        assert result["faab"]["faab_traded"]["sent"] == 25
        assert result["faab"]["faab_traded"]["received"] == 30
        assert result["faab"]["faab_traded"]["net"] == 5  # 30 - 25
    
    def test_get_transaction_details_immutable(self):
        """Test that function doesn't modify cache."""
        original = deepcopy(self.mock_manager_cache)

        get_transaction_details_from_cache(None, "Manager 1", {})

        assert self.mock_manager_cache == original