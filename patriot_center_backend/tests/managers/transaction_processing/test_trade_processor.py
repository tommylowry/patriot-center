"""Unit tests for trade_processor module."""

from typing import Any
from unittest.mock import call, patch

import pytest

from patriot_center_backend.cache.updaters.processors.transactions.trade_processor import (  # noqa: E501
    add_trade_details_to_cache,
    process_trade_transaction,
    revert_trade_transaction,
)


class TestAddTradeDetailsToCache:
    """Test add_trade_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `add_to_transaction_ids`: `mock_add_to_transaction_ids`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.add_to_transaction_ids"
            ) as mock_add_to_transaction_ids,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_add_to_transaction_ids = mock_add_to_transaction_ids

            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_calls_get_manager_cache(self):
        """Test that get_manager_cache is called."""
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {"A.J. Brown": "Jay"},
            [],
            "trade_abc123",
            False,
            True,
        )

        self.mock_get_manager_cache.assert_called_once()

    def test_calls_add_to_transaction_ids_with_correct_args(self):
        """Test that add_to_transaction_ids is called with correct args."""
        weekly_transaction_ids: list[str] = []

        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {"A.J. Brown": "Jay"},
            weekly_transaction_ids,
            "trade_abc123",
            False,
            True,
        )

        self.mock_add_to_transaction_ids.assert_called_once_with(
            "2023",
            "1",
            {
                "type": "trade",
                "manager": "Tommy",
                "trade_partners": ["Jay"],
                "acquired": {"Jayden Daniels": "Jay"},
                "sent": {"A.J. Brown": "Jay"},
                "transaction_id": "trade_abc123",
            },
            weekly_transaction_ids,
            False,
            True,
        )

    def test_skips_duplicate_transaction_id(self):
        """Test that duplicate transaction IDs are not processed twice."""
        # Pre-populate transaction_ids to simulate already processed trade
        wk_lvl = self.mock_manager_cache["Tommy"]["years"]["2023"]["weeks"]["1"]
        wk_lvl["transactions"]["trades"]["transaction_ids"] = ["trade_abc123"]

        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        # add_to_transaction_ids should NOT be called for duplicate
        self.mock_add_to_transaction_ids.assert_not_called()

    def test_increments_total_trades_at_all_levels(self):
        """Test that total trade count is incremented at all levels.

        Fixture starts with total=4, after adding 1 trade should be 5.
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts at 4, incremented by 1 = 5
        assert mgr["summary"][t]["trades"]["total"] == 5
        assert mgr["years"]["2023"]["summary"][t]["trades"]["total"] == 5
        assert mgr["years"]["2023"]["weeks"]["1"][t]["trades"]["total"] == 5

    def test_updates_trade_partners_at_all_levels(self):
        """Test that trade partners are tracked at all levels.

        Fixture starts with trade_partners["Jay"]=2, after adding 1 should be 3.
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts at 2, incremented by 1 = 3
        assert mgr["summary"][t]["trades"]["trade_partners"]["Jay"] == 3
        yr_summary = mgr["years"]["2023"]["summary"][t]["trades"]
        assert yr_summary["trade_partners"]["Jay"] == 3
        wk_summary = mgr["years"]["2023"]["weeks"]["1"][t]["trades"]
        assert wk_summary["trade_partners"]["Jay"] == 3

    def test_tracks_players_acquired_at_all_levels(self):
        """Test that acquired players are tracked with partner info.

        Fixture starts with Jayden Daniels total=1, trade_partners["Jay"]=1.
        After adding 1 more, should be total=2, trade_partners["Jay"]=2.
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        top_acq = mgr["summary"][t]["trades"]["trade_players_acquired"]
        # Fixture starts at 1, incremented by 1 = 2
        assert top_acq["Jayden Daniels"]["total"] == 2
        assert top_acq["Jayden Daniels"]["trade_partners"]["Jay"] == 2

    def test_tracks_players_sent_at_all_levels(self):
        """Test that sent players are tracked with partner info.

        A.J. Brown is not in fixture, so adding creates new entry with total=1.
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {},
            {"A.J. Brown": "Jay"},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        top_sent = mgr["summary"][t]["trades"]["trade_players_sent"]
        # A.J. Brown is new, so total=1
        assert top_sent["A.J. Brown"]["total"] == 1
        assert top_sent["A.J. Brown"]["trade_partners"]["Jay"] == 1

    def test_appends_transaction_id_to_weekly_list(self):
        """Test that transaction ID is appended to weekly transaction_ids."""
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay"],
            {"Jayden Daniels": "Jay"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        wk_lvl = self.mock_manager_cache["Tommy"]["years"]["2023"]["weeks"]["1"]
        assert "trade_abc123" in wk_lvl[t]["trades"]["transaction_ids"]

    def test_handles_multiple_trade_partners(self):
        """Test trade with multiple partners (3-way trade).

        Fixture starts with total=4, trade_partners["Jay"]=2.
        After adding 3-way trade: total=5, Jay=3, Mitch=1 (new).
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            ["Jay", "Mitch"],
            {"Jayden Daniels": "Jay", "Ja'Marr Chase": "Mitch"},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts at 4, incremented by 1 = 5
        assert mgr["summary"][t]["trades"]["total"] == 5
        # Jay: 2 + 1 = 3, Mitch: 0 + 1 = 1
        assert mgr["summary"][t]["trades"]["trade_partners"]["Jay"] == 3
        assert mgr["summary"][t]["trades"]["trade_partners"]["Mitch"] == 1

    def test_no_trade_partners_does_not_increment_total(self):
        """Test that empty trade_partners list does not increment total.

        Fixture starts with total=4. With empty partners, total stays at 4.
        """
        add_trade_details_to_cache(
            "2023",
            "1",
            "Tommy",
            [],
            {},
            {},
            [],
            "trade_abc123",
            False,
            True,
        )

        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts at 4, not incremented = 4
        assert mgr["summary"]["transactions"]["trades"]["total"] == 4


class TestRevertTradeTransaction:
    """Test revert_trade_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
        mock_transaction_ids_cache: dict[str, Any],
    ):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_trans_ids`

        Args:
            mock_manager_cache: Manager cache with comprehensive trade data.
            mock_transaction_ids_cache: Transaction IDs cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_trans_ids,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_transaction_ids_cache = mock_transaction_ids_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_trans_ids = mock_get_trans_ids

            mock_get_manager_cache.return_value = self.mock_manager_cache
            mock_get_trans_ids.return_value = self.mock_transaction_ids_cache

            yield

    def test_calls_get_transaction_ids_cache(self):
        """Test that get_transaction_ids_cache is called."""
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        self.mock_get_trans_ids.assert_called_once()

    def test_calls_get_manager_cache(self):
        """Test that get_manager_cache is called."""
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        self.mock_get_manager_cache.assert_called_once()

    def test_removes_transaction_ids_from_cache(self):
        """Test that both transaction IDs are removed from cache."""
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        assert "trade1" not in self.mock_transaction_ids_cache
        assert "trade2" not in self.mock_transaction_ids_cache

    def test_removes_transaction_ids_from_weekly_list(self):
        """Test that transaction IDs are removed from weekly list."""
        weekly_ids = ["trade1", "trade2", "trade3"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        assert "trade1" not in weekly_ids
        assert "trade2" not in weekly_ids
        assert "trade3" in weekly_ids

    def test_decrements_trade_totals_by_two(self):
        """Test that trade totals are decremented by 2 at all levels.

        Fixture starts with total=4, after revert should be 2.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        t = "transactions"
        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts at 4, decremented by 2 = 2
        assert mgr["summary"][t]["trades"]["total"] == 2
        assert mgr["years"]["2023"]["summary"][t]["trades"]["total"] == 2
        wk = mgr["years"]["2023"]["weeks"]["1"][t]["trades"]
        assert wk["total"] == 2

    def test_removes_faab_transaction_ids_from_weekly(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that FAAB transaction IDs are removed from weekly cache.

        Args:
            caplog: pytest LogCaptureFixture.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        wk_lvl = self.mock_manager_cache["Tommy"]["years"]["2023"]["weeks"]["1"]
        assert "trade1" not in wk_lvl["transactions"]["faab"]["transaction_ids"]
        assert "trade2" not in wk_lvl["transactions"]["faab"]["transaction_ids"]

    def test_decrements_trade_partner_counts(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that trade partner counts are decremented.

        Args:
            caplog: pytest LogCaptureFixture.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        mgr = self.mock_manager_cache["Tommy"]
        # Fixture starts with 2, decremented by 2 = 0, so key is deleted
        assert (
            "Jay"
            not in (mgr["summary"]["transactions"]["trades"]["trade_partners"])
        )

    def test_decrements_player_acquired_counts(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that player acquired counts are decremented.

        Args:
            caplog: pytest LogCaptureFixture.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        mgr = self.mock_manager_cache["Tommy"]
        # Fixture has Jayden Daniels with total=1, decremented to 0 = deleted
        acquired = mgr["summary"]["transactions"]["trades"][
            "trade_players_acquired"
        ]
        assert "Jayden Daniels" not in acquired

    def test_decrements_faab_traded_away(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that FAAB traded_away is decremented for FAAB trades.

        Args:
            caplog: pytest LogCaptureFixture.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        mgr = self.mock_manager_cache["Tommy"]
        faab = mgr["summary"]["transactions"]["faab"]
        # Fixture starts with 50, decremented by 50 = 0
        assert faab["traded_away"]["total"] == 0
        assert "Jay" not in faab["traded_away"]["trade_partners"]

    def test_decrements_faab_acquired_from(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that FAAB acquired_from is decremented for FAAB trades.

        Args:
            caplog: pytest LogCaptureFixture.
        """
        weekly_ids = ["trade1", "trade2"]

        revert_trade_transaction("trade1", "trade2", weekly_ids)

        mgr = self.mock_manager_cache["Tommy"]
        faab = mgr["summary"]["transactions"]["faab"]
        # Fixture starts with 50, decremented by 50 = 0
        assert faab["acquired_from"]["total"] == 0
        assert "Jay" not in faab["acquired_from"]["trade_partners"]


class TestProcessTradeTransaction:
    """Test process_trade_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to mock ALL external function calls:
        - `CACHE_MANAGER.get_player_ids_cache`: Returns player ID mappings
        - `update_players_cache`: Side effect function (no return)
        - `draft_pick_decipher`: Returns draft pick display name
        - `add_trade_details_to_cache`: Side effect function (no return)
        - `add_faab_details_to_cache`: Side effect function (no return)

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.update_players_cache"
            ) as mock_update_players_cache,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.draft_pick_decipher"
            ) as mock_draft_pick_decipher,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.add_trade_details_to_cache"
            ) as mock_add_trade_details,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".trade_processor.add_faab_details_to_cache"
            ) as mock_add_faab_details,
        ):
            self.mock_get_player_ids = mock_get_player_ids
            self.mock_update_players_cache = mock_update_players_cache
            self.mock_draft_pick_decipher = mock_draft_pick_decipher
            self.mock_add_trade_details = mock_add_trade_details
            self.mock_add_faab_details = mock_add_faab_details

            # Default player IDs cache
            self.mock_player_ids_cache = {
                "player1": {"full_name": "Jayden Daniels"},
                "player2": {"full_name": "A.J. Brown"},
            }
            self.mock_get_player_ids.return_value = self.mock_player_ids_cache

            self.simple_trade = {
                "type": "trade",
                "transaction_id": "trade_abc123",
                "roster_ids": [1, 2],
                "adds": {"player1": 1, "player2": 2},
                "drops": {"player1": 2, "player2": 1},
                "draft_picks": None,
                "waiver_budget": [],
            }

            self.trade_w_faab = {
                "type": "trade",
                "transaction_id": "trade_abc123",
                "roster_ids": [1, 2],
                "adds": {"player1": 1},
                "drops": {"player1": 2},
                "draft_picks": None,
                "waiver_budget": [{"sender": 1, "receiver": 2, "amount": 50}],
            }

            self.trade_w_draft_pick = {
                "type": "trade",
                "transaction_id": "trade_abc123",
                "roster_ids": [1, 2],
                "adds": {"player1": 1},
                "drops": {"player1": 2},
                "draft_picks": [
                    {
                        "season": "2024",
                        "round": 1,
                        "roster_id": 2,
                        "owner_id": 1,
                        "previous_owner_id": 2,
                    }
                ],
                "waiver_budget": [],
            }

            yield

    def test_calls_get_player_ids_cache(self):
        """Test that get_player_ids_cache is called."""
        process_trade_transaction(
            "2023",
            "1",
            self.simple_trade,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            False,
        )

        self.mock_get_player_ids.assert_called_once()

    def test_calls_update_players_cache_for_acquired_players(self):
        """Test that update_players_cache is called for each acquired player."""
        process_trade_transaction(
            "2023",
            "1",
            self.simple_trade,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            False,
        )

        # player1 is acquired by Tommy, player2 is acquired by Jerry
        # Each player triggers update for both managers
        calls = self.mock_update_players_cache.call_args_list
        assert call("player1") in calls
        assert call("player2") in calls

    def test_calls_add_trade_details_for_each_manager(self):
        """Test that add_trade_details_to_cache is called for each manager."""
        process_trade_transaction(
            "2023",
            "1",
            self.simple_trade,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        assert self.mock_add_trade_details.call_count == 2

        # Verify call for Tommy
        tommy_call = None
        jay_call = None
        for c in self.mock_add_trade_details.call_args_list:
            if c[0][2] == "Tommy":
                tommy_call = c
            elif c[0][2] == "Jay":
                jay_call = c

        assert tommy_call is not None
        assert tommy_call[0][0] == "2023"  # year
        assert tommy_call[0][1] == "1"  # week
        assert tommy_call[0][2] == "Tommy"  # manager
        assert tommy_call[0][3] == ["Jay"]  # trade_partners
        assert tommy_call[0][4] == {"Jayden Daniels": "Jay"}  # acquired
        assert tommy_call[0][5] == {"A.J. Brown": "Jay"}  # sent

        assert jay_call is not None
        assert jay_call[0][2] == "Jay"
        assert jay_call[0][3] == ["Tommy"]  # trade_partners
        assert jay_call[0][4] == {"A.J. Brown": "Tommy"}  # acquired
        assert jay_call[0][5] == {"Jayden Daniels": "Tommy"}  # sent

    def test_calls_draft_pick_decipher_for_draft_picks(self):
        """Test that draft_pick_decipher is called for draft picks."""
        self.mock_draft_pick_decipher.return_value = "2024 Round 1 (Jerry)"

        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_draft_pick,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            False,
        )

        assert self.mock_draft_pick_decipher.call_count >= 1

    def test_draft_pick_acquired_passed_to_add_trade_details(self):
        """Test that acquired draft picks are passed correctly."""
        self.mock_draft_pick_decipher.return_value = "2024 Round 1 (Jerry)"
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_draft_pick,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            False,
        )

        # Find Tommy's call and verify draft pick is in acquired
        for c in self.mock_add_trade_details.call_args_list:
            if c[0][2] == "Tommy":
                acquired = c[0][4]
                assert "2024 Round 1 (Jerry)" in acquired

    def test_calls_add_faab_details_when_faab_present(self):
        """Test that add_faab_details_to_cache is called for FAAB trades."""
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_faab,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        # Should be called twice (once for sender, once for receiver)
        assert self.mock_add_faab_details.call_count == 2

    def test_add_faab_details_called_with_correct_sender_args(self):
        """Test add_faab_details_to_cache is called correctly for sender."""
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_faab,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        # Find the sender call (negative faab amount)
        sender_call = None
        for c in self.mock_add_faab_details.call_args_list:
            if c[0][5] < 0:  # faab amount is negative for sender
                sender_call = c
                break

        assert sender_call is not None
        assert sender_call[0][0] == "2023"  # year
        assert sender_call[0][1] == "1"  # week
        assert sender_call[0][2] == "trade"  # transaction_type
        assert sender_call[0][3] == "Tommy"  # manager (sender)
        assert sender_call[0][4] == "FAAB"  # player
        assert sender_call[0][5] == -50  # faab (negative)
        assert sender_call[1]["trade_partner"] == "Jay"

    def test_add_faab_details_called_with_correct_receiver_args(self):
        """Test add_faab_details_to_cache is called correctly for receiver."""
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_faab,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        # Find the receiver call (positive faab amount)
        receiver_call = None
        for c in self.mock_add_faab_details.call_args_list:
            if c[0][5] > 0:  # faab amount is positive for receiver
                receiver_call = c
                break

        assert receiver_call is not None
        assert receiver_call[0][3] == "Jay"  # manager (receiver)
        assert receiver_call[0][5] == 50  # faab (positive)
        assert receiver_call[1]["trade_partner"] == "Tommy"

    def test_does_not_call_add_faab_when_use_faab_false(self):
        """Test that add_faab_details is not called when use_faab is False."""
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_faab,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            False,
        )

        self.mock_add_faab_details.assert_not_called()

    def test_does_not_call_add_faab_when_no_waiver_budget(self):
        """Test that add_faab_details is not called when no FAAB in trade."""
        process_trade_transaction(
            "2023",
            "1",
            self.simple_trade,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        self.mock_add_faab_details.assert_not_called()

    def test_skips_unknown_roster_id(self, caplog: pytest.LogCaptureFixture):
        """Test that unknown roster IDs are skipped with warning.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "type": "trade",
            "transaction_id": "trade_abc123",
            "roster_ids": [1, 99],  # 99 is unknown
            "adds": {"player1": 1},
            "drops": {"player1": 99},
            "draft_picks": None,
            "waiver_budget": [],
        }

        process_trade_transaction(
            "2023", "1", transaction, {1: "Tommy"}, [], False, False
        )

        # Should only call add_trade_details once (for Tommy)
        assert self.mock_add_trade_details.call_count == 1

    def test_handles_three_way_trade(self):
        """Test processing a 3-way trade."""
        self.mock_player_ids_cache["player3"] = {"full_name": "Bijan Robinson"}
        transaction = {
            "type": "trade",
            "transaction_id": "trade_abc123",
            "roster_ids": [1, 2, 3],
            "adds": {"player1": 1, "player2": 2, "player3": 3},
            "drops": {"player1": 2, "player2": 3, "player3": 1},
            "draft_picks": None,
            "waiver_budget": [],
        }

        process_trade_transaction(
            "2023",
            "1",
            transaction,
            {1: "Tommy", 2: "Jay", 3: "Mitch"},
            [],
            False,
            False,
        )

        # Should call add_trade_details for each of the 3 managers
        assert self.mock_add_trade_details.call_count == 3

    def test_faab_in_acquired_and_sent_dicts(self):
        """Test that FAAB string is added to acquired/sent dicts."""
        process_trade_transaction(
            "2023",
            "1",
            self.trade_w_faab,
            {1: "Tommy", 2: "Jay"},
            [],
            False,
            True,
        )

        # Tommy (sender) should have FAAB in sent
        for c in self.mock_add_trade_details.call_args_list:
            if c[0][2] == "Tommy":
                sent = c[0][5]
                assert "$50 FAAB" in sent
                assert sent["$50 FAAB"] == "Jay"
            elif c[0][2] == "Jay":
                acquired = c[0][4]
                assert "$50 FAAB" in acquired
                assert acquired["$50 FAAB"] == "Tommy"

    def test_commish_action_passed_through(self):
        """Test that commish_action is passed to add_trade_details_to_cache."""
        process_trade_transaction(
            "2023",
            "1",
            self.simple_trade,
            {1: "Tommy", 2: "Jay"},
            [],
            True,
            False,
        )

        for c in self.mock_add_trade_details.call_args_list:
            assert c[0][8] is True  # commish_action arg
