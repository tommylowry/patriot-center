"""Unit tests for transaction_reverter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.processors.transactions.transaction_reverter import (  # noqa: E501
    check_for_reverse_transactions,
)


class TestCheckForReverseTransactions:
    """Test check_for_reverse_transactions method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_trans_ids`
        - `revert_trade_transaction`: `mock_revert_trade`
        - `revert_add_drop_transaction`: `mock_revert_add_drop`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_trans_ids,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".transaction_reverter.revert_trade_transaction"
            ) as mock_revert_trade,
            patch(
                "patriot_center_backend.cache.updaters.processors.transactions"
                ".transaction_reverter.revert_add_drop_transaction"
            ) as mock_revert_add_drop,
        ):
            self.mock_get_trans_ids = mock_get_trans_ids
            self.mock_revert_trade = mock_revert_trade
            self.mock_revert_add_drop = mock_revert_add_drop

            self.mock_transaction_ids_cache = {}
            self.transaction_ids = ["trans1", "trans2"]

            self.mock_get_trans_ids.return_value = (
                self.mock_transaction_ids_cache
            )

            yield

    def test_check_for_reverse_transactions_detects_reversal(self):
        """Test that reversed trades are detected and removed."""
        # Set up two transactions that reverse each other
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy", "Jay"],
                    "types": ["trade"],
                    "players_involved": ["Player One", "Player Two"],
                    "trade_details": {
                        "Player One": {
                            "old_manager": "Tommy",
                            "new_manager": "Jay",
                        },
                        "Player Two": {
                            "old_manager": "Jay",
                            "new_manager": "Tommy",
                        },
                    },
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy", "Jay"],
                    "types": ["trade"],
                    "players_involved": ["Player One", "Player Two"],
                    "trade_details": {
                        "Player One": {
                            "old_manager": "Jay",
                            "new_manager": "Tommy",
                        },
                        "Player Two": {
                            "old_manager": "Tommy",
                            "new_manager": "Jay",
                        },
                    },
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should detect reversal and revert trade
        assert self.mock_revert_trade.called
        assert not self.mock_revert_add_drop.called

    def test_check_for_reverse_transactions_no_reversal(self):
        """Test that non-reversed transactions are not removed."""
        # Set up two transactions that do NOT reverse each other
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy", "Jay"],
                    "types": ["trade"],
                    "players_involved": ["Player One"],
                    "trade_details": {
                        "Player One": {
                            "old_manager": "Tommy",
                            "new_manager": "Jay",
                        }
                    },
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy", "Jay"],
                    "types": ["trade"],
                    "players_involved": ["Player Two"],
                    "trade_details": {
                        "Player Two": {
                            "old_manager": "Tommy",
                            "new_manager": "Jay",
                        }
                    },
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should NOT detect reversal
        assert not self.mock_revert_trade.called
        assert not self.mock_revert_add_drop.called

    def test_commissioner_add_then_drop_reversal(self):
        """Test method detects commissioner add followed by drop."""
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": True,
                    "managers_involved": ["Tommy"],
                    "types": ["add"],
                    "players_involved": ["Player One"],
                    "add": "Player One",
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy"],
                    "types": ["drop"],
                    "players_involved": ["Player One"],
                    "drop": "Player One",
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should detect reversal and call revert for both add and drop
        assert self.mock_revert_add_drop.call_count == 2
        # Check that it was called with the correct transaction IDs and types
        trans_id_calls = []
        type_calls = []
        for call in self.mock_revert_add_drop.call_args_list:
            trans_id_calls.append(call[0][0])
            type_calls.append(call[0][1])

        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_commissioner_drop_then_add_reversal(self):
        """Test method detects commissioner drop followed by add."""
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": True,
                    "managers_involved": ["Tommy"],
                    "types": ["drop"],
                    "players_involved": ["Player One"],
                    "drop": "Player One",
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy"],
                    "types": ["add"],
                    "players_involved": ["Player One"],
                    "add": "Player One",
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should detect reversal and call revert for both drop and add
        trans_id_calls = [
            call[0][0] for call in self.mock_revert_add_drop.call_args_list
        ]
        type_calls = [
            call[0][1] for call in self.mock_revert_add_drop.call_args_list
        ]

        assert self.mock_revert_add_drop.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_regular_transaction_then_commissioner_reversal(self):
        """Test method detects regular add followed by commissioner drop."""
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy"],
                    "types": ["add"],
                    "players_involved": ["Player One"],
                    "add": "Player One",
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": True,
                    "managers_involved": ["Tommy"],
                    "types": ["drop"],
                    "players_involved": ["Player One"],
                    "drop": "Player One",
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should detect reversal and call revert for both add and drop
        trans_id_calls = []
        type_calls = []
        for call in self.mock_revert_add_drop.call_args_list:
            trans_id_calls.append(call[0][0])
            type_calls.append(call[0][1])

        assert self.mock_revert_add_drop.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_commissioner_reversal_with_different_players_no_match(self):
        """Test method doesn't detect reversal with different players."""
        self.mock_transaction_ids_cache.update(
            {
                "trans1": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": True,
                    "managers_involved": ["Tommy"],
                    "types": ["add"],
                    "players_involved": ["Player One"],
                    "add": "Player One",
                },
                "trans2": {
                    "year": "2023",
                    "week": "1",
                    "commish_action": False,
                    "managers_involved": ["Tommy"],
                    "types": ["drop"],
                    "players_involved": ["Player Two"],
                    "drop": "Player Two",
                },
            }
        )

        check_for_reverse_transactions(self.transaction_ids)

        # Should NOT detect reversal because players are different
        assert not self.mock_revert_add_drop.called
        assert not self.mock_revert_trade.called
