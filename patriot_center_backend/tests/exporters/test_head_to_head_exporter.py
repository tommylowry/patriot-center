"""Unit tests for head_to_head_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.head_to_head_exporter import (
    get_head_to_head,
)

MODULE_PATH = "patriot_center_backend.exporters.head_to_head_exporter"


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `validate_manager_query`: (returns nothing)
        - `get_head_to_head_overall_from_cache`: `mock_get_h2h`
        - `get_trade_history_between_two_managers`:
            `mock_get_trade_history`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.validate_manager_query"
            ) as mock_validate_manager_query,
            patch(
                f"{MODULE_PATH}.get_head_to_head_overall_from_cache"
            ) as mock_get_h2h,
            patch(
                f"{MODULE_PATH}.get_trade_history_between_two_managers"
            ) as mock_get_trade_history,
        ):
            self.mock_validate_manager_query = mock_validate_manager_query

            self.mock_get_h2h = mock_get_h2h
            self.mock_get_h2h.return_value = {}

            self.mock_get_trade_history = mock_get_trade_history
            self.mock_get_trade_history.return_value = []

            yield

    def test_get_h2h_all_time(self):
        """Test getting H2H stats for all-time."""
        self.mock_get_h2h.side_effect = (
            lambda *args, list_all_matchups=False, **kwargs: (
                {"manager_1_wins": 7, "manager_2_wins": 3, "ties": 1}
                if list_all_matchups
                else {"wins": 7, "losses": 3}
            )
        )

        result = get_head_to_head("Tommy", "Benz")

        assert result["manager_1"] == {
            "name": "Tommy",
            "image_url": "https://sleepercdn.com/avatars/abc123",
        }
        assert result["manager_2"] == {
            "name": "Tommy",
            "image_url": "https://sleepercdn.com/avatars/abc123",
        }
        assert result["overall"] == {"wins": 7, "losses": 3}
        assert result["matchup_history"] == {
            "manager_1_wins": 7,
            "manager_2_wins": 3,
            "ties": 1,
        }
        assert result["trades_between"]["total"] == 0
        assert result["trades_between"]["trade_history"] == []

    def test_get_h2h_single_year(self):
        """Test getting H2H stats for specific year."""
        self.mock_get_h2h.return_value = {"wins": 2, "losses": 1}

        get_head_to_head("Tommy", "Benz", year="2023")

        # Verify year was passed to h2h query
        calls = self.mock_get_h2h.call_args_list
        assert len(calls) == 2
        for call in calls:
            assert call[1]["year"] == "2023"

    def test_get_h2h_with_trades(self):
        """Test H2H with trade history between managers."""
        self.mock_get_h2h.return_value = {}
        self.mock_get_trade_history.return_value = [
            {"trade_id": "trade1", "year": "2023", "week": "5"},
            {"trade_id": "trade2", "year": "2023", "week": "10"},
        ]

        result = get_head_to_head("Tommy", "Benz")

        assert result["trades_between"]["total"] == 2
        assert len(result["trades_between"]["trade_history"]) == 2

    def test_get_h2h_validates_both_managers(self):
        """Test that validate_manager_query is called for both managers."""
        get_head_to_head("Tommy", "Benz", year="2023")

        calls = self.mock_validate_manager_query.call_args_list
        assert len(calls) == 2
        assert calls[0].args == ("Tommy", "2023")
        assert calls[1].args == ("Benz", "2023")

    def test_get_h2h_validation_error_propagates(self):
        """Test that ValueError from validation propagates."""
        self.mock_validate_manager_query.side_effect = ValueError(
            "Manager NotAManager not found in cache."
        )

        with pytest.raises(ValueError, match="NotAManager"):
            get_head_to_head("NotAManager", "Benz")

    def test_get_h2h_returns_deepcopy(self):
        """Test that result is a deep copy (immutable)."""
        overall_data = {"wins": 7, "losses": 3}
        self.mock_get_h2h.return_value = overall_data

        result = get_head_to_head("Tommy", "Benz")

        result["overall"]["wins"] = 999
        assert overall_data["wins"] == 7
