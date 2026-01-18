"""Unit tests for faab_processor module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.faab_processor import (  # noqa: E501
    add_faab_details_to_cache,
)


class TestAddFaabDetailsToCache:
    """Test add_faab_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".faab_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
        ):
            self.mock_manager_cache = mock_manager_cache

            mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_add_faab_waiver_details(self):
        """Test that FAAB waiver details are added to cache."""
        add_faab_details_to_cache(
            "2023",
            "1",
            "waiver",
            "Tommy",
            "Player One",
            50,
            "trans1",
            trade_partner=None,
        )

        # Check weekly summary
        yr = self.mock_manager_cache["Tommy"]["years"]["2023"]
        weekly = yr["weeks"]["1"]["transactions"]["faab"]

        assert weekly["total_lost_or_gained"] == -50
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"]["num_bids_won"] == 1
        assert weekly["players"]["Player One"]["total_faab_spent"] == 50

    def test_add_faab_trade_details(self):
        """Test that FAAB trade details are added to cache.

        Fixture starts with acquired_from["total"]=50
        and trade_partners["Jay"]=50.
        After adding 100, total should be 150
        and trade_partners["Jay"]=150.
        """
        # Manager 1 receives FAAB (positive amount)
        add_faab_details_to_cache(
            "2023",
            "1",
            "trade",
            "Tommy",
            "FAAB",
            100,
            "trans1",
            trade_partner="Jay",
        )

        yr = self.mock_manager_cache["Tommy"]["years"]["2023"]
        weekly = yr["weeks"]["1"]["transactions"]["faab"]

        # Fixture starts at 0, incremented by 100 = 100
        assert weekly["total_lost_or_gained"] == 100
        # Fixture starts at 50, incremented by 100 = 150
        assert weekly["acquired_from"]["total"] == 150
        assert weekly["acquired_from"]["trade_partners"]["Jay"] == 150

    def test_add_faab_trade_sent(self):
        """Test that FAAB sent in trade is tracked correctly."""
        # Manager 1 sends FAAB (negative amount)
        add_faab_details_to_cache(
            "2023",
            "1",
            "trade",
            "Tommy",
            "FAAB",
            -100,
            "trans1",
            trade_partner="Jay",
        )

        yr = self.mock_manager_cache["Tommy"]["years"]["2023"]
        weekly = yr["weeks"]["1"]["transactions"]["faab"]

        assert weekly["total_lost_or_gained"] == -100
        assert weekly["traded_away"]["total"] == 150
        assert "Jay" in weekly["traded_away"]["trade_partners"]
