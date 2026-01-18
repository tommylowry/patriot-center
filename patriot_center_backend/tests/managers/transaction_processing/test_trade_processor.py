"""Unit tests for trade_processor module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.trade_processor import (  # noqa: E501
    add_trade_details_to_cache,
    process_trade_transaction,
    revert_trade_transaction,
)


@pytest.fixture
def mock_player_ids_cache():
    """Create a sample player ids cache for testing.

    Returns:
        Sample player ids cache
    """
    return {
        "player1": {"full_name": "Player One"},
        "player2": {"full_name": "Player Two"},
    }


class TestAddTradeDetailsToCache:
    """Test add_trade_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `update_players_cache`: `mock_update_players_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.update_players_cache"
            ) as mock_update_players_cache,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_update_players_cache = mock_update_players_cache

            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_add_trade_details_updates_cache(self):
        """Test that trade details are added to cache at all levels."""
        add_trade_details_to_cache(
            "2023",
            "1",
            "Manager 1",
            ["Manager 2"],
            {"Player One": "Manager 2"},
            {"Player Two": "Manager 2"},
            [],
            "trans1",
            False,
            True,
        )

        # Check weekly summary
        yr_lvl = self.mock_manager_cache["Manager 1"]["years"]["2023"]
        weekly = yr_lvl["weeks"]["1"]["transactions"]["trades"]

        assert weekly["total"] == 1
        assert "Manager 2" in weekly["trade_partners"]
        assert "Player One" in weekly["trade_players_acquired"]
        assert "Player Two" in weekly["trade_players_sent"]

    def test_add_trade_details_prevents_duplicates(self):
        """Test that duplicate transaction IDs are not processed twice."""
        # Add once
        add_trade_details_to_cache(
            "2023",
            "1",
            "Manager 1",
            ["Manager 2"],
            {"Player One": "Manager 2"},
            {},
            [],
            "trans1",
            False,
            True,
        )

        # Try to add again
        add_trade_details_to_cache(
            "2023",
            "1",
            "Manager 1",
            ["Manager 2"],
            {"Player One": "Manager 2"},
            {},
            [],
            "trans1",
            False,
            True,
        )

        # Should only have 1 trade
        yr_lvl = self.mock_manager_cache["Manager 1"]["years"]["2023"]
        weekly = yr_lvl["weeks"]["1"]["transactions"]["trades"]

        assert weekly["total"] == 1


class TestRevertTradeTransaction:
    """Test revert_trade_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_trans_ids`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_trans_ids,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_transaction_ids_cache = {}
            self.weekly_transaction_ids = ["trade1", "trade2"]

            mock_get_manager_cache.return_value = self.mock_manager_cache
            mock_get_trans_ids.return_value = self.mock_transaction_ids_cache

            yield

    def test_revert_simple_trade_removes_both_transactions(self):
        """Test revert_trade_transaction removes both trades from cache."""
        # Setup cache for both managers - use total=2
        # since we're removing all trades
        for manager in ["Manager 1", "Manager 2"]:
            mgr_lvl = self.mock_manager_cache[manager]
            yr_lvl = mgr_lvl["years"]["2023"]
            wk_lvl = yr_lvl["weeks"]["1"]

            trade_partner = (
                "Manager 2" if manager == "Manager 1" else "Manager 1"
            )

            wk_lvl["transactions"]["trades"]["total"] = 2
            wk_lvl["transactions"]["trades"]["transaction_ids"] = [
                "trade1",
                "trade2",
            ]
            wk_lvl["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }
            yr_lvl["summary"]["transactions"]["trades"]["total"] = 2
            yr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }
            mgr_lvl["summary"]["transactions"]["trades"]["total"] = 2
            mgr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }

            acq_key = "trade_players_acquired"

            # Setup acquired/sent
            wk_lvl["transactions"]["trades"][acq_key] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }

            t = "transactions"

            yr_lvl["summary"][t]["trades"][acq_key] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            mgr_lvl["summary"][t]["trades"][acq_key] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }

            wk_lvl[t]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            yr_lvl["summary"][t]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            mgr_lvl["summary"][t]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {trade_partner: 1}}
            }

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["Player One"],
            "trade_details": {
                "Player One": {
                    "old_manager": "Manager 1",
                    "new_manager": "Manager 2",
                }
            },
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["Player One"],
            "trade_details": {
                "Player One": {
                    "old_manager": "Manager 2",
                    "new_manager": "Manager 1",
                }
            },
        }

        # Call function directly
        revert_trade_transaction(
            "trade1",
            "trade2",
            self.weekly_transaction_ids,
        )

        # Assert only THIS function's behavior
        assert "trade1" not in self.mock_transaction_ids_cache
        assert "trade2" not in self.mock_transaction_ids_cache
        assert len(self.weekly_transaction_ids) == 0

        sum_lvl = self.mock_manager_cache["Manager 1"]["summary"]
        assert sum_lvl["transactions"]["trades"]["total"] == 0
        assert sum_lvl["transactions"]["trades"]["trade_partners"] == {}

    def test_revert_trade_with_faab_removes_faab_data(self):
        """Test revert_trade_transaction removes FAAB data."""
        # Setup basic trade cache - use 4 total so
        # after decrementing 2, there are still 2 left
        #   (if total goes to 0, the code continues
        #   and skips FAAB decrement logic)
        for manager in ["Manager 1", "Manager 2"]:
            mgr_lvl = self.mock_manager_cache[manager]
            yr_lvl = mgr_lvl["years"]["2023"]
            wk_lvl = yr_lvl["weeks"]["1"]

            trade_partner = (
                "Manager 2" if manager == "Manager 1" else "Manager 1"
            )

            wk_lvl["transactions"]["trades"]["total"] = 4
            wk_lvl["transactions"]["trades"]["transaction_ids"] = [
                "trade1",
                "trade2",
            ]
            wk_lvl["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }
            yr_lvl["summary"]["transactions"]["trades"]["total"] = 4
            yr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }
            mgr_lvl["summary"]["transactions"]["trades"]["total"] = 4
            mgr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                trade_partner: 2
            }

            # Setup acquired/sent for FAAB
            t = "transactions"

            wk_lvl[t]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            yr_lvl["summary"][t]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            mgr_lvl["summary"][t]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }

            wk_lvl[t]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            yr_lvl["summary"][t]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }
            mgr_lvl["summary"][t]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}}
            }

        # Setup FAAB cache - the code decrements both traded_away and
        # acquired_from for each manager
        # Set up both fields for both managers
        for manager, partner in [
            ("Manager 1", "Manager 2"),
            ("Manager 2", "Manager 1"),
        ]:
            mgr_lvl = self.mock_manager_cache[manager]
            yr_lvl = mgr_lvl["years"]["2023"]
            wk_lvl = yr_lvl["weeks"]["1"]

            s = "summary"
            t = "transactions"

            wk_lvl[t]["faab"]["traded_away"]["total"] = 100
            wk_lvl[t]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            wk_lvl[t]["faab"]["acquired_from"]["total"] = 100
            wk_lvl[t]["faab"]["acquired_from"]["trade_partners"] = {
                partner: 100
            }

            yr_lvl[s][t]["faab"]["traded_away"]["total"] = 100
            yr_lvl[s][t]["faab"]["traded_away"]["trade_partners"] = {
                partner: 100
            }
            yr_lvl[s][t]["faab"]["acquired_from"]["total"] = 100
            yr_lvl[s][t]["faab"]["acquired_from"]["trade_partners"] = {
                partner: 100
            }

            mgr_lvl[s][t]["faab"]["traded_away"]["total"] = 100
            mgr_lvl[s][t]["faab"]["traded_away"]["trade_partners"] = {
                partner: 100
            }
            mgr_lvl[s][t]["faab"]["acquired_from"]["total"] = 100
            mgr_lvl[s][t]["faab"]["acquired_from"]["trade_partners"] = {
                partner: 100
            }

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["$100 FAAB"],
            "trade_details": {
                "$100 FAAB": {
                    "old_manager": "Manager 1",
                    "new_manager": "Manager 2",
                }
            },
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["$100 FAAB"],
            "trade_details": {
                "$100 FAAB": {
                    "old_manager": "Manager 2",
                    "new_manager": "Manager 1",
                }
            },
        }

        revert_trade_transaction(
            "trade1",
            "trade2",
            self.weekly_transaction_ids,
        )

        # Assert FAAB was removed
        m = self.mock_manager_cache
        s = "summary"
        t = "transactions"
        f = "faab"

        assert m["Manager 1"][s][t][f]["traded_away"]["total"] == 0
        assert m["Manager 2"][s][t][f]["acquired_from"]["total"] == 0
        assert (
            "Manager 2"
            not in (m["Manager 1"][s][t][f]["traded_away"]["trade_partners"])
        )

    def test_revert_trade_removes_from_weekly_transaction_ids(self):
        """Test revert_trade_transaction removes IDs from weekly list."""
        # Setup with 3 trades total
        for manager in ["Manager 1", "Manager 2"]:
            mgr_lvl = self.mock_manager_cache[manager]
            yr_lvl = mgr_lvl["years"]["2023"]
            wk_lvl = yr_lvl["weeks"]["1"]

            wk_lvl["transactions"]["trades"]["total"] = 3
            wk_lvl["transactions"]["trades"]["transaction_ids"] = [
                "trade1",
                "trade2",
                "trade3",
            ]
            wk_lvl["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            yr_lvl["summary"]["transactions"]["trades"]["total"] = 3
            yr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            mgr_lvl["summary"]["transactions"]["trades"]["total"] = 3
            mgr_lvl["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }

            s = "summary"
            t = "transactions"

            wk_lvl[t]["trades"]["trade_players_acquired"] = {}
            yr_lvl[s][t]["trades"]["trade_players_acquired"] = {}
            mgr_lvl[s][t]["trades"]["trade_players_acquired"] = {}
            wk_lvl[t]["trades"]["trade_players_sent"] = {}
            yr_lvl[s][t]["trades"]["trade_players_sent"] = {}
            mgr_lvl[s][t]["trades"]["trade_players_sent"] = {}

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {},
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {},
        }

        # Adding in a 3rd trade that should still be in there
        self.weekly_transaction_ids.append("trade3")

        revert_trade_transaction(
            "trade1",
            "trade2",
            self.weekly_transaction_ids,
        )

        # Assert trade3 still exists
        mgr_lvl = self.mock_manager_cache["Manager 1"]
        yr_lvl = mgr_lvl["years"]["2023"]
        wk_lvl = yr_lvl["weeks"]["1"]

        assert "trade3" in wk_lvl["transactions"]["trades"]["transaction_ids"]
        assert "trade1" not in self.weekly_transaction_ids
        assert "trade2" not in self.weekly_transaction_ids
        assert "trade3" in self.weekly_transaction_ids


class TestProcessTradeTransaction:
    """Test process_trade_transaction with actual trade processing."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
        mock_player_ids_cache: dict[str, dict[str, str]],
    ):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids`
        - `update_players_cache`: (returns nothing)

        Args:
            mock_manager_cache: A mock manager cache.
            mock_player_ids_cache: A mock player IDs cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".trade_processor.update_players_cache"
            ),
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_player_ids_cache = mock_player_ids_cache

            mock_get_manager_cache.return_value = self.mock_manager_cache
            mock_get_player_ids.return_value = self.mock_player_ids_cache

            yield

    def test_process_simple_two_team_trade(self):
        """Test processing a simple 2-team player swap."""
        # Manager 1 gets player1, Manager 2 gets player2
        transaction = {
            "type": "trade",
            "transaction_id": "trade1",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player1": 2, "player2": 1},
            "draft_picks": None,
            "waiver_budget": [],
        }

        process_trade_transaction(
            "2023",
            "1",
            transaction,
            {1: "Manager 1", 2: "Manager 2"},
            [],
            False,
            False,
        )

        # Verify Manager 1 acquired player1
        m1 = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]

        assert m1["transactions"]["trades"]["total"] == 1
        assert "trade1" in m1["transactions"]["trades"]["transaction_ids"]

        # Verify Manager 2 acquired player2
        m2 = self.mock_manager_cache["Manager 2"]["years"]["2023"]["weeks"]["1"]
        assert m2["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_draft_picks(self):
        """Test processing trade that includes draft picks."""
        transaction = {
            "type": "trade",
            "transaction_id": "trade2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player1": 2},
            "draft_picks": [
                {
                    "season": "2024",
                    "round": 1,
                    "roster_id": 2,  # Manager 1 acquired this pick
                    "owner_id": 1,
                    "previous_owner_id": 2,
                }
            ],
            "waiver_budget": [],
        }

        process_trade_transaction(
            "2023",
            "1",
            transaction,
            {1: "Manager 1", 2: "Manager 2"},
            [],
            False,
            False,
        )

        # Should process successfully
        m1 = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]
        assert m1["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_faab(self):
        """Test processing trade that includes FAAB exchange."""
        transaction = {
            "type": "trade",
            "transaction_id": "trade3",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player1": 2},
            "draft_picks": None,
            "waiver_budget": [{"sender": 1, "receiver": 2, "amount": 50}],
        }

        process_trade_transaction(
            "2023",
            "1",
            transaction,
            {1: "Manager 1", 2: "Manager 2"},
            [],
            False,
            True,
        )

        # Verify FAAB was tracked
        m1 = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]
        m2 = self.mock_manager_cache["Manager 2"]["years"]["2023"]["weeks"]["1"]

        assert m1["transactions"]["faab"]["traded_away"]["total"] == 50
        assert m2["transactions"]["faab"]["acquired_from"]["total"] == 50
