"""Unit tests for transaction_id_processor module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.transaction_id_processor import (  # noqa: E501
    add_to_transaction_ids,
)


class TestAddToTransactionIds:
    """Test add_to_transaction_ids method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_trans_id`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.transaction_processing"
                ".transaction_id_processor"
                ".CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_trans_id,
        ):
            self.mock_ids_cache = {}

            mock_get_trans_id.return_value = self.mock_ids_cache

            yield

    def test_add_trade_to_cache(self):
        """Test adding trade to transaction IDs cache."""
        transaction_info = {
            "type": "trade",
            "manager": "Tommy",
            "trade_partners": ["Jay"],
            "acquired": {"Player One": "Jay"},
            "sent": {"Player Two": "Jay"},
            "transaction_id": "trans1",
        }

        add_to_transaction_ids("2023", "1", transaction_info, [], False, True)

        assert "trans1" in self.mock_ids_cache
        assert self.mock_ids_cache["trans1"]["year"] == "2023"
        assert self.mock_ids_cache["trans1"]["week"] == "1"
        assert "Tommy" in self.mock_ids_cache["trans1"]["managers_involved"]
        assert "Jay" in self.mock_ids_cache["trans1"]["managers_involved"]

    def test_add_add_or_drop_to_cache(self):
        """Test adding add/drop to transaction IDs cache."""
        transaction_info = {
            "type": "add_or_drop",
            "free_agent_type": "add",
            "manager": "Tommy",
            "player_name": "Player One",
            "transaction_id": "trans1",
            "waiver_bid": 50,
        }

        add_to_transaction_ids("2023", "1", transaction_info, [], False, True)

        assert "trans1" in self.mock_ids_cache
        assert self.mock_ids_cache["trans1"]["add"] == "Player One"
        assert self.mock_ids_cache["trans1"]["faab_spent"] == 50

    def test_add_to_cache_missing_type(self):
        """Test that missing type raises ValueError."""
        with pytest.raises(ValueError, match="Transaction type not found"):
            add_to_transaction_ids(
                "2023",
                "1",
                {"transaction_id": "trans1", "manager": "Tommy"},
                [],
                False,
                True,
            )

    def test_add_to_cache_missing_transaction_id(self):
        """Test that missing transaction_id raises ValueError."""
        with pytest.raises(ValueError, match="transaction_id not found"):
            add_to_transaction_ids(
                "2023",
                "1",
                {"type": "trade", "manager": "Tommy"},
                [],
                False,
                True,
            )
