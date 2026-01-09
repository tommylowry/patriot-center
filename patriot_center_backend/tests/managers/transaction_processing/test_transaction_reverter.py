
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.transaction_reverter import (
    check_for_reverse_transactions,
)


class TestCheckForReverseTransactions:
    """Test check_for_reverse_transactions method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache') as mock_get_trans_ids, \
             patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_trade_transaction') as mock_revert_trade, \
             patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_add_drop_transaction') as mock_revert_add_drop:
            
            self.mock_get_trans_ids = mock_get_trans_ids
            self.mock_revert_trade = mock_revert_trade
            self.mock_revert_add_drop = mock_revert_add_drop
            
            self.mock_transaction_ids_cache = {}
            self.transaction_ids = ["trans1", "trans2"]

            self.mock_get_trans_ids.return_value = self.mock_transaction_ids_cache

            yield
    
    def test_check_for_reverse_transactions_detects_reversal(self):
        """Test that reversed trades are detected and removed."""
        # Set up two transactions that reverse each other
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"},
                    "Player Two": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
                }
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 2", "new_manager": "Manager 1"},
                    "Player Two": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            }
        })

        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should detect reversal and revert trade
        assert self.mock_revert_trade.called
        assert not self.mock_revert_add_drop.called

    def test_check_for_reverse_transactions_no_reversal(self):
        """Test that non-reversed transactions are not removed."""
        # Set up two transactions that do NOT reverse each other
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player Two"],
                "trade_details": {
                    "Player Two": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            }
        })

        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should NOT detect reversal
        assert not self.mock_revert_trade.called
        assert not self.mock_revert_add_drop.called
    
    def test_commissioner_add_then_drop_reversal(self):
        """Test check_for_reverse_transactions detects commissioner add followed by drop."""
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            }
        })

        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should detect reversal and call revert for both add and drop
        assert self.mock_revert_add_drop.call_count == 2
        # Check that it was called with the correct transaction IDs and types
        trans_id_calls = [call[0][0] for call in self.mock_revert_add_drop.call_args_list]
        type_calls = [call[0][1] for call in self.mock_revert_add_drop.call_args_list]
        
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_commissioner_drop_then_add_reversal(self):
        """Test check_for_reverse_transactions detects commissioner drop followed by add."""
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            }
        })

        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should detect reversal and call revert for both drop and add
        trans_id_calls = [call[0][0] for call in self.mock_revert_add_drop.call_args_list]
        type_calls = [call[0][1] for call in self.mock_revert_add_drop.call_args_list]
        
        assert self.mock_revert_add_drop.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_regular_transaction_then_commissioner_reversal(self):
        """Test check_for_reverse_transactions detects regular add followed by commissioner drop."""
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            }
        })
            
        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should detect reversal and call revert for both add and drop
        trans_id_calls = [call[0][0] for call in self.mock_revert_add_drop.call_args_list]
        type_calls = [call[0][1] for call in self.mock_revert_add_drop.call_args_list]

        assert self.mock_revert_add_drop.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    def test_commissioner_reversal_with_different_players_no_match(self):
        """Test check_for_reverse_transactions doesn't detect reversal with different players."""
        self.mock_transaction_ids_cache.update({
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player Two"],
                "drop": "Player Two"
            }
        })
            
        check_for_reverse_transactions(transaction_ids=self.transaction_ids)

        # Should NOT detect reversal because players are different
        assert not self.mock_revert_add_drop.called
        assert not self.mock_revert_trade.called