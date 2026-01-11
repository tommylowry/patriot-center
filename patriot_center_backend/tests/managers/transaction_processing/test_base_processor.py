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

    @pytest.fixture(autouse=True)
    def setup(self, processor):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.base_processor.fetch_sleeper_data') as mock_fetch_sleeper_data:
            self.mock_sleeper_data = []
            mock_fetch_sleeper_data.return_value = self.mock_sleeper_data

            processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
            self.processor = processor
            
            yield

    def test_scrub_transaction_data_processes_transactions(self):
        """Test that scrub_transaction_data fetches and processes transactions."""
        self.mock_sleeper_data.extend([
            {
                "transaction_id": "trans1",
                "type": "free_agent",
                "adds": {"player1": 1},
                "drops": None
            }
        ])

        with patch.object(self.processor, '_process_transaction') as mock_process:
            self.processor.scrub_transaction_data("2023", "1")

            # Should process the transaction
            assert mock_process.called
            assert mock_process.call_count == 1

    def test_scrub_transaction_data_reverses_order(self):
        """Test that transactions are reversed (oldest first)."""
        self.mock_sleeper_data.extend([
            {"transaction_id": "trans1", "type": "free_agent"},
            {"transaction_id": "trans2", "type": "free_agent"},
            {"transaction_id": "trans3", "type": "free_agent"}
        ])

        call_order = []
        def track_calls(transaction):
            call_order.append(transaction["transaction_id"])

        with patch.object(self.processor, '_process_transaction', side_effect=track_calls):
            self.processor.scrub_transaction_data("2023", "1")

            # Should be in reversed order (trans3, trans2, trans1)
            assert call_order == ["trans3", "trans2", "trans1"]

    def test_scrub_transaction_data_invalid_year(self):
        """Test that invalid year raises ValueError."""
        self.processor.set_session_state("9999", "1", {1: "Manager 1"}, True)

        with pytest.raises(ValueError, match="No league ID found"):
            self.processor.scrub_transaction_data("9999", "1")

class TestProcessTransaction:
    """Test _process_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(self, processor):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.base_processor.validate_transaction') as mock_validate_transaction, \
             patch('patriot_center_backend.managers.transaction_processing.base_processor.process_add_or_drop_transaction') as mock_proc_add_drop, \
             patch('patriot_center_backend.managers.transaction_processing.base_processor.process_trade_transaction') as mock_proc_trade:
            
            self.processor = processor
            self.mock_validate_transaction = mock_validate_transaction
            self.mock_proc_add_drop = mock_proc_add_drop
            self.mock_proc_trade = mock_proc_trade
            
            self.mock_validate_value = True
            
            self.mock_validate_transaction.return_value = self.mock_validate_value
            self.processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

            yield

    def test_process_transaction_validates(self):
        """Test that transaction is validated before processing."""
        self.mock_validate_value = False

        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        self.processor._process_transaction(transaction)

        # Should validate
        assert self.mock_validate_transaction.called

    def test_process_transaction_routes_to_add_or_drop(self):
        """Test that free_agent/waiver transactions are routed to add_or_drop."""
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        self.processor._process_transaction(transaction)

        assert self.mock_proc_add_drop.called
    
    def test_add_or_drop_called_with_right_args(self):
        """Test process_add_or_drop_transaction is called with the correct arguments"""
        year = "2023"
        week = "1"
        weekly_roster_ids = {1: "Manager 1"}
        weekly_transaction_ids = []
        commish_action = False
        use_faab = True

        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        self.processor._process_transaction(transaction)

        self.mock_proc_add_drop.assert_called_with(year, week, transaction,
                                                weekly_roster_ids, weekly_transaction_ids,
                                                commish_action, use_faab)
    
    def test_process_transaction_routes_to_trade(self):
        """Test that trade transactions are routed to trade processor."""
        self.processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2}
        }

        self.processor._process_transaction(transaction)

        assert self.mock_proc_trade.called
    
    def test_trade_called_with_right_args(self):
        """Test process_trade_transaction is called with the correct arguments"""
        year = "2023"
        week = "1"
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        weekly_transaction_ids = []
        commish_action = False
        use_faab = True

        self.processor.set_session_state(year, week, weekly_roster_ids, use_faab)
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2}
        }

        self.processor._process_transaction(transaction)

        self.mock_proc_trade.assert_called_with(year, week, transaction,
                                                weekly_roster_ids, weekly_transaction_ids,
                                                commish_action, use_faab)

    def test_process_transaction_detects_commissioner_action(self):
        """Test that commissioner actions are detected."""
        transaction = {
            "type": "commissioner",
            "adds": {"player1": 1},
            "drops": None
        }

        self.processor._process_transaction(transaction)

        # Should pass commish_action=True
        assert self.mock_proc_add_drop.call_args[0][5] is True
    
    def test_commissioner_add_only(self):
        """Test commissioner action with only adds (no drops)."""
        transaction = {
            "type": "commissioner",
            "transaction_id": "comm1",
            "adds": {"player1": 1},
            "drops": None  # No drops means add_or_drop type
        }

        self.processor._process_transaction(transaction)

        # Should call add_or_drop processor with commish_action=True
        assert self.mock_proc_add_drop.called
        assert self.mock_proc_add_drop.call_args[0][5] == True  # commish_action

    def test_commissioner_forced_trade(self):
        """Test commissioner action with multiple players (forced trade)."""
        self.processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player1": 2, "player2": 1}
        }

        self.processor._process_transaction(transaction)

        # Should call trade processor with commish_action=True
        assert self.mock_proc_trade.called
        assert self.mock_proc_trade.call_args[0][5] == True  # commish_action