
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.base_processor import (
    TransactionProcessor,
)


@pytest.fixture
def processor():
    """Create TransactionProcessor instance."""
    return TransactionProcessor(use_faab=True)


class TestCheckForReverseTransactions:
    """Test check_for_reverse_transactions method."""

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_trade_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_check_for_reverse_transactions_detects_reversal(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test that reversed trades are detected and removed."""
        # Set up two transactions that reverse each other
        mock_transaction_ids_cache.return_value = {
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
        }
        
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should detect reversal and revert
        assert mock_revert.called

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_trade_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_check_for_reverse_transactions_no_reversal(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test that non-reversed transactions are not removed."""
        # Set up two transactions that do NOT reverse each other
        mock_transaction_ids_cache.return_value = {
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
        }
            
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should NOT detect reversal
        assert not mock_revert.called

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_add_drop_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_commissioner_add_then_drop_reversal(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test check_for_reverse_transactions detects commissioner add followed by drop."""
        mock_transaction_ids_cache.return_value = {
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
        }

        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should detect reversal and call revert for both add and drop
        assert mock_revert.call_count == 2
        # Check that it was called with the correct transaction IDs and types
        trans_id_calls = [call[0][0] for call in mock_revert.call_args_list]
        type_calls = [call[0][1] for call in mock_revert.call_args_list]
        
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_add_drop_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_commissioner_drop_then_add_reversal(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test check_for_reverse_transactions detects commissioner drop followed by add."""
        mock_transaction_ids_cache.return_value = {
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
        }

        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should detect reversal and call revert for both drop and add
        trans_id_calls = [call[0][0] for call in mock_revert.call_args_list]
        type_calls = [call[0][1] for call in mock_revert.call_args_list]
        
        assert mock_revert.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_add_drop_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_regular_transaction_then_commissioner_reversal(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test check_for_reverse_transactions detects regular add followed by commissioner drop."""
        mock_transaction_ids_cache.return_value = {
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
        }
            
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should detect reversal and call revert for both add and drop
        trans_id_calls = [call[0][0] for call in mock_revert.call_args_list]
        type_calls = [call[0][1] for call in mock_revert.call_args_list]

        assert mock_revert.call_count == 2
        assert "trans1" in trans_id_calls
        assert "trans2" in trans_id_calls
        assert "add" in type_calls
        assert "drop" in type_calls

    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.revert_add_drop_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.transaction_reverter.CACHE_MANAGER.get_transaction_ids_cache')
    def test_commissioner_reversal_with_different_players_no_match(self, mock_transaction_ids_cache, mock_revert, processor):
        """Test check_for_reverse_transactions doesn't detect reversal with different players."""
        mock_transaction_ids_cache.return_value = {
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
        }
            
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        processor.check_for_reverse_transactions()

        # Should NOT detect reversal because players are different
        assert not mock_revert.called