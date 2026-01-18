"""Unit tests for base_processor module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.base_processor import (  # noqa: E501
    TransactionProcessor,
)


@pytest.fixture
def processor():
    """Create TransactionProcessor instance.

    Returns:
        A TransactionProcessor interface.
    """
    return TransactionProcessor()


class TestTransactionProcessorInit:
    """Test TransactionProcessor initialization."""

    def test_init_sets_default_session_state(self):
        """Test that __init__ initializes empty session state."""
        from patriot_center_backend.managers.transaction_processing.base_processor import (  # noqa: E501
            TransactionProcessor,
        )

        processor = TransactionProcessor()

        assert processor._year is None
        assert processor._week is None
        assert processor._use_faab is None
        assert processor._weekly_roster_ids == {}
        assert processor._weekly_transaction_ids == []


class TestSessionState:
    """Test session state management."""

    def test_set_session_state(self, processor: TransactionProcessor):
        """Test setting session state.

        Args:
            processor: A TransactionProcessor interface.
        """
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids=weekly_roster_ids,
            use_faab=True,
        )

        assert processor._year == "2023"
        assert processor._week == "1"
        assert processor._weekly_roster_ids == weekly_roster_ids
        assert processor._use_faab is True

    def test_clear_session_state(self, processor: TransactionProcessor):
        """Test clearing session state.

        Args:
            processor: A TransactionProcessor interface.
        """
        # First set some state
        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1"},
            use_faab=True,
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
    def setup(self, processor: TransactionProcessor):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `_process_transaction`: `mock_process_transaction`

        Args:
            processor: A TransactionProcessor interface.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".base_processor.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".base_processor.TransactionProcessor._process_transaction"
            ) as mock_process_transaction,
        ):
            self.mock_sleeper_data = []
            mock_fetch_sleeper_data.return_value = self.mock_sleeper_data

            self.mock_process_transaction = mock_process_transaction

            processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
            self.processor = processor

            yield

    def test_scrub_transaction_data_processes_transactions(self):
        """Test that function fetches and processes transactions."""
        self.mock_sleeper_data.extend(
            [
                {
                    "transaction_id": "trans1",
                    "type": "free_agent",
                    "adds": {"player1": 1},
                    "drops": None,
                }
            ]
        )

        self.processor.scrub_transaction_data()

        # Should process the transaction
        assert self.mock_process_transaction.called
        assert self.mock_process_transaction.call_count == 1

    def test_scrub_transaction_data_reverses_order(self):
        """Test that transactions are reversed (oldest first)."""
        self.mock_sleeper_data.extend(
            [
                {"transaction_id": "trans1", "type": "free_agent"},
                {"transaction_id": "trans2", "type": "free_agent"},
                {"transaction_id": "trans3", "type": "free_agent"},
            ]
        )

        self.processor.scrub_transaction_data()

        call_list = [
            call[0][0] for call in self.mock_process_transaction.call_args_list
        ]
        # Should be in reversed order (trans3, trans2, trans1)
        # for call in self.mock_process_transaction.call_args_list:

        assert len(call_list) == 3
        assert call_list[0]["transaction_id"] == "trans3"
        assert call_list[1]["transaction_id"] == "trans2"
        assert call_list[2]["transaction_id"] == "trans1"

    def test_scrub_transaction_data_invalid_year(self):
        """Test that invalid year raises ValueError."""
        self.processor.set_session_state("9999", "1", {1: "Manager 1"}, True)

        with pytest.raises(ValueError, match="No league ID found"):
            self.processor.scrub_transaction_data()


class TestProcessTransaction:
    """Test _process_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(self, processor: TransactionProcessor):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `validate_transaction`: `mock_validate_transaction`
        - `process_add_or_drop_transaction`: `mock_proc_add_drop`
        - `process_trade_transaction`: `mock_proc_trade`

        Args:
            processor: A TransactionProcessor interface.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".base_processor.validate_transaction"
            ) as mock_validate_transaction,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".base_processor.process_add_or_drop_transaction"
            ) as mock_proc_add_drop,
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".base_processor.process_trade_transaction"
            ) as mock_proc_trade,
        ):
            self.processor = processor
            self.mock_validate_transaction = mock_validate_transaction
            self.mock_proc_add_drop = mock_proc_add_drop
            self.mock_proc_trade = mock_proc_trade

            self.mock_validate_transaction.return_value = True
            self.processor.set_session_state(
                "2023", "1", {1: "Manager 1"}, True
            )

            yield

    def test_process_transaction_validates(self):
        """Test that transaction is validated before processing."""
        self.mock_validate_value = False

        transaction = {
            "type": "free_agent",
            "adds": {"player1": 1},
            "drops": None,
        }

        self.processor._process_transaction(transaction)

        # Should validate
        assert self.mock_validate_transaction.called

    def test_process_transaction_routes_to_add_or_drop(self):
        """Test that fa/waiver transactions are routed to add_or_drop."""
        transaction = {
            "type": "free_agent",
            "adds": {"player1": 1},
            "drops": None,
        }

        self.processor._process_transaction(transaction)

        assert self.mock_proc_add_drop.called

    def test_add_or_drop_called_with_right_args(self):
        """Test process_add_or_drop_transaction is called correctly."""
        year = "2023"
        week = "1"
        weekly_roster_ids = {1: "Manager 1"}
        weekly_transaction_ids = []
        commish_action = False
        use_faab = True

        transaction = {
            "type": "free_agent",
            "adds": {"player1": 1},
            "drops": None,
        }

        self.processor._process_transaction(transaction)

        self.mock_proc_add_drop.assert_called_with(
            year,
            week,
            transaction,
            weekly_roster_ids,
            weekly_transaction_ids,
            commish_action,
            use_faab,
        )

    def test_process_transaction_routes_to_trade(self):
        """Test that trade transactions are routed to trade processor."""
        self.processor.set_session_state(
            "2023", "1", {1: "Manager 1", 2: "Manager 2"}, True
        )
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2},
        }

        self.processor._process_transaction(transaction)

        assert self.mock_proc_trade.called

    def test_trade_called_with_right_args(self):
        """Test process_trade_transaction is called correctly."""
        year = "2023"
        week = "1"
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        weekly_transaction_ids = []
        commish_action = False
        use_faab = True

        self.processor.set_session_state(
            year, week, weekly_roster_ids, use_faab
        )
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2},
        }

        self.processor._process_transaction(transaction)

        self.mock_proc_trade.assert_called_with(
            year,
            week,
            transaction,
            weekly_roster_ids,
            weekly_transaction_ids,
            commish_action,
            use_faab,
        )

    def test_process_transaction_detects_commissioner_action(self):
        """Test that commissioner actions are detected."""
        transaction = {
            "type": "commissioner",
            "adds": {"player1": 1},
            "drops": None,
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
            "drops": None,  # No drops means add_or_drop type
        }

        self.processor._process_transaction(transaction)

        # Should call add_or_drop processor with commish_action=True
        assert self.mock_proc_add_drop.called
        assert self.mock_proc_add_drop.call_args[0][5]  # commish_action

    def test_commissioner_forced_trade(self):
        """Test commissioner action with multiple players (forced trade)."""
        self.processor.set_session_state(
            "2023", "1", {1: "Manager 1", 2: "Manager 2"}, True
        )

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player1": 2, "player2": 1},
        }

        self.processor._process_transaction(transaction)

        # Should call trade processor with commish_action=True
        assert self.mock_proc_trade.called
        assert self.mock_proc_trade.call_args[0][5]  # commish_action
