from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.faab_processor import (
    add_faab_details_to_cache,
)


class TestAddFaabDetailsToCache:
    """Test add_faab_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.faab_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager_cache:
            
            self.mock_manager_cache = mock_manager_cache

            mock_get_manager_cache.return_value = self.mock_manager_cache
            
            yield

    def test_add_faab_waiver_details(self):
        """Test that FAAB waiver details are added to cache."""
        add_faab_details_to_cache(
            year="2023",
            week="1",
            transaction_type="waiver",
            manager="Manager 1",
            player_name="Player One",
            faab_amount=50,
            transaction_id="trans1",
            trade_partner=None
        )

        # Check weekly summary
        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -50
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"]["num_bids_won"] == 1
        assert weekly["players"]["Player One"]["total_faab_spent"] == 50

    def test_add_faab_trade_details(self):
        """Test that FAAB trade details are added to cache."""
        
        # Manager 1 receives FAAB (positive amount)
        add_faab_details_to_cache(
            year="2023",
            week="1",
            transaction_type="trade",
            manager="Manager 1",
            player_name="FAAB",
            faab_amount=100,
            transaction_id="trans1",
            trade_partner="Manager 2"
        )

        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == 100
        assert weekly["acquired_from"]["total"] == 100
        assert "Manager 2" in weekly["acquired_from"]["trade_partners"]

    def test_add_faab_trade_sent(self):
        """Test that FAAB sent in trade is tracked correctly."""

        # Manager 1 sends FAAB (negative amount)
        add_faab_details_to_cache(
            year="2023",
            week="1",
            transaction_type="trade",
            manager="Manager 1",
            player_name="FAAB",
            faab_amount=-100,
            transaction_id="trans1",
            trade_partner="Manager 2"
        )

        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -100
        assert weekly["traded_away"]["total"] == 100
        assert "Manager 2" in weekly["traded_away"]["trade_partners"]
