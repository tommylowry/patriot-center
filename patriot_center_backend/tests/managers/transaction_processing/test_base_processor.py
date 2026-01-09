from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.base_processor import (
    TransactionProcessor,
)


@pytest.fixture
def processor():
    """Create TransactionProcessor instance."""
    return TransactionProcessor(use_faab=True)


class TestTransactionProcessorInit:
    """Test TransactionProcessor initialization."""

    def test_init_stores_caches(self):
        """Test that __init__ stores all cache references."""
        from patriot_center_backend.managers.transaction_processing.base_processor import (
            TransactionProcessor,
        )
        processor = TransactionProcessor(use_faab=True)

        assert processor._use_faab is True

    def test_init_with_faab_disabled(self):
        """Test initialization with FAAB disabled."""
        from patriot_center_backend.managers.transaction_processing.base_processor import (
            TransactionProcessor,
        )
        processor = TransactionProcessor(use_faab=False)

        assert processor._use_faab is False

    def test_init_sets_default_session_state(self):
        """Test that __init__ initializes empty session state."""
        from patriot_center_backend.managers.transaction_processing.base_processor import (
            TransactionProcessor,
        )
        processor = TransactionProcessor(use_faab=True)

        assert processor._year is None
        assert processor._week is None
        assert processor._weekly_roster_ids == {}
        assert processor._weekly_transaction_ids == []

class TestSessionState:
    """Test session state management."""

    def test_set_session_state(self, processor):
        """Test setting session state."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids=weekly_roster_ids,
            use_faab=True
        )

        assert processor._year == "2023"
        assert processor._week == "1"
        assert processor._weekly_roster_ids == weekly_roster_ids
        assert processor._use_faab is True

    def test_set_session_state_without_faab(self, processor):
        """Test setting session state with FAAB disabled."""
        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1"},
            use_faab=False
        )

        assert processor._use_faab is False

    def test_clear_session_state(self, processor):
        """Test clearing session state."""
        # First set some state
        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1"},
            use_faab=True
        )
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        # Then clear it
        processor.clear_session_state()

        assert processor._year is None
        assert processor._week is None
        assert processor._weekly_roster_ids == {}
        assert processor._weekly_transaction_ids == []

class TestScrubTransactionData:
    """Test scrub_transaction_data method."""

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_processes_transactions(self, mock_fetch, processor):
        """Test that scrub_transaction_data fetches and processes transactions."""
        mock_fetch.return_value = [
            {
                "transaction_id": "trans1",
                "type": "free_agent",
                "adds": {"player1": 1},
                "drops": None
            }
        ]

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        with patch.object(processor, '_process_transaction') as mock_process:
            processor.scrub_transaction_data("2023", "1")

            # Should process the transaction
            assert mock_process.called
            assert mock_process.call_count == 1

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_reverses_order(self, mock_fetch, processor):
        """Test that transactions are reversed (oldest first)."""
        mock_fetch.return_value = [
            {"transaction_id": "trans1", "type": "free_agent"},
            {"transaction_id": "trans2", "type": "free_agent"},
            {"transaction_id": "trans3", "type": "free_agent"}
        ]

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        call_order = []
        def track_calls(transaction):
            call_order.append(transaction["transaction_id"])

        with patch.object(processor, '_process_transaction', side_effect=track_calls):
            processor.scrub_transaction_data("2023", "1")

            # Should be in reversed order (trans3, trans2, trans1)
            assert call_order == ["trans3", "trans2", "trans1"]

    def test_scrub_transaction_data_invalid_year(self, processor):
        """Test that invalid year raises ValueError."""
        processor.set_session_state("9999", "1", {1: "Manager 1"}, True)

        with pytest.raises(ValueError, match="No league ID found"):
            processor.scrub_transaction_data("9999", "1")

class TestProcessTransaction:
    """Test _process_transaction method."""

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    def test_process_transaction_validates(self, mock_validate, processor):
        """Test that transaction is validated before processing."""
        mock_validate.return_value = False

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        processor._process_transaction(transaction)

        # Should validate
        assert mock_validate.called

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.base_processor.process_add_or_drop_transaction')
    def test_process_transaction_routes_to_add_or_drop(self, mock_process, mock_validate, processor):
        """Test that free_agent/waiver transactions are routed to add_or_drop."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        processor._process_transaction(transaction)

        assert mock_process.called

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.base_processor.process_trade_transaction')
    def test_process_transaction_routes_to_trade(self, mock_process, mock_validate, processor):
        """Test that trade transactions are routed to trade processor."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2}
        }

        processor._process_transaction(transaction)

        assert mock_process.called

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.base_processor.process_add_or_drop_transaction')
    def test_process_transaction_detects_commissioner_action(self, mock_process, mock_validate, processor):
        """Test that commissioner actions are detected."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {
            "type": "commissioner",
            "adds": {"player1": 1},
            "drops": None
        }

        processor._process_transaction(transaction)

        # Should pass commish_action=True
        assert mock_process.call_args[0][5] is True

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.process_add_or_drop_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    def test_commissioner_add_only(self, mock_validate, mock_add_drop, processor):
        """Test commissioner action with only adds (no drops)."""
        mock_validate.return_value = True
        
        processor._year = "2023"
        processor._week = "1"
        processor._weekly_roster_ids = {1: "Manager 1"}

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm1",
            "adds": {"player1": 1},
            "drops": None  # No drops means add_or_drop type
        }

        processor._process_transaction(transaction)

        # Should call add_or_drop processor with commish_action=True
        assert mock_add_drop.called
        assert mock_add_drop.call_args[0][5] == True  # commish_action

    @patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction')
    @patch('patriot_center_backend.managers.transaction_processing.base_processor.process_trade_transaction')
    def test_commissioner_forced_trade(self, mock_trade, mock_validate, processor):
        """Test commissioner action with multiple players (forced trade)."""
        mock_validate.return_value = True
        
        processor._year = "2023"
        processor._week = "1"
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player1": 2, "player2": 1}
        }

        processor._process_transaction(transaction)

        # Should call trade processor with commish_action=True
        assert mock_trade.called
        assert mock_trade.call_args[0][5] == True  # commish_action