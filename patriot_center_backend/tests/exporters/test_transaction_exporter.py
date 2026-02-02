"""Unit tests for transaction_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.transaction_exporter import (
    get_manager_transactions,
)

MODULE_PATH = "patriot_center_backend.exporters.transaction_exporter"


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_manager_transaction_history_from_cache`:
            `mock_get_transaction_history`
        - `get_transaction_from_ids_cache`:
            `mock_get_transaction_from_ids`
        - `get_image_url`: `mock_get_image_url`
        - `get_trade_card`: `mock_get_trade_card`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_manager_transaction_history_from_cache"
            ) as mock_get_transaction_history,
            patch(
                f"{MODULE_PATH}.get_transaction_from_ids_cache"
            ) as mock_get_transaction_from_ids,
            patch(
                f"{MODULE_PATH}.get_image_url"
            ) as mock_get_image_url,
            patch(
                f"{MODULE_PATH}.get_trade_card"
            ) as mock_get_trade_card,
        ):
            self.mock_manager_transactions = {
                "Tommy": {
                    "years": {
                        "2023": {
                            "weeks": {},
                        },
                        "2022": {
                            "weeks": {},
                        },
                    },
                },
            }

            self.mock_get_transaction_history = mock_get_transaction_history
            self.mock_get_transaction_history.return_value = (
                self.mock_manager_transactions
            )

            self.mock_get_transaction_from_ids = (
                mock_get_transaction_from_ids
            )
            self.mock_get_transaction_from_ids.return_value = {}

            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.return_value = {
                "name": "Tommy",
                "image_url": "https://sleepercdn.com/avatars/abc123",
            }

            self.mock_get_trade_card = mock_get_trade_card
            self.mock_get_trade_card.return_value = {}

            yield

    def test_get_transactions_all_time(self):
        """Test getting all-time transaction details."""
        result = get_manager_transactions("Tommy")

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result
        assert isinstance(result["transactions"], list)
        assert result["total_count"] == 0

    def test_get_transactions_single_year(self):
        """Test getting transaction details for specific year."""
        self.mock_manager_transactions["Tommy"]["years"] = {
            "2023": {"weeks": {}},
        }

        result = get_manager_transactions("Tommy", year="2023")

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result
        self.mock_get_transaction_history.assert_called_once_with(
            "Tommy", "2023"
        )

    def test_get_transactions_with_trades(self):
        """Test get_manager_transactions processes trade transactions."""
        self.mock_manager_transactions["Tommy"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "trades": {
                        "transaction_ids": ["trade1", "trade2"]
                    }
                }
            }
        }
        self.mock_get_trade_card.return_value = {
            "year": "2023",
            "week": "1",
            "managers_involved": ["Tommy", "Benz"],
        }

        result = get_manager_transactions("Tommy", year="2023")

        assert result["total_count"] == 2
        trades = [
            t for t in result["transactions"] if t["type"] == "trade"
        ]
        assert len(trades) == 2

    def test_get_transactions_with_adds(self):
        """Test get_manager_transactions processes add transactions."""
        self.mock_manager_transactions["Tommy"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {"transaction_ids": ["add1"]}
                }
            }
        }
        self.mock_get_transaction_from_ids.return_value = {
            "types": ["add"],
            "add": "Jayden Daniels",
            "faab_spent": 50,
        }
        self.mock_get_image_url.return_value = {
            "name": "Jayden Daniels",
            "image_url": "https://sleepercdn.com/content/abc123",
        }

        result = get_manager_transactions("Tommy", year="2023")

        adds = [t for t in result["transactions"] if t["type"] == "add"]
        assert len(adds) == 1
        assert adds[0]["faab_spent"] == 50

    def test_get_transactions_with_drops(self):
        """Test get_manager_transactions processes drop transactions."""
        self.mock_manager_transactions["Tommy"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "drops": {"transaction_ids": ["drop1"]}
                }
            }
        }
        self.mock_get_transaction_from_ids.return_value = {
            "types": ["drop"],
            "drop": "Sam Howell",
        }
        self.mock_get_image_url.return_value = {
            "name": "Sam Howell",
            "image_url": "https://sleepercdn.com/content/def456",
        }

        result = get_manager_transactions("Tommy", year="2023")

        drops = [t for t in result["transactions"] if t["type"] == "drop"]
        assert len(drops) == 1
        assert drops[0]["player"]["name"] == "Sam Howell"

    def test_get_transactions_with_add_and_drop(self):
        """Test get_manager_transactions processes add_and_drop."""
        self.mock_manager_transactions["Tommy"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {"transaction_ids": ["add_drop1"]}
                }
            }
        }
        self.mock_get_transaction_from_ids.return_value = {
            "types": ["add", "drop"],
            "add": "Jayden Daniels",
            "drop": "Sam Howell",
            "faab_spent": 30,
        }

        def image_url_side_effect(player, dictionary=False):
            if dictionary:
                return {
                    "name": player,
                    "image_url": f"https://sleepercdn.com/{player}",
                }
            return f"https://sleepercdn.com/{player}"

        self.mock_get_image_url.side_effect = image_url_side_effect

        result = get_manager_transactions("Tommy", year="2023")

        add_drops = [
            t for t in result["transactions"]
            if t["type"] == "add_and_drop"
        ]
        assert len(add_drops) == 1
        assert add_drops[0]["added_player"]["name"] == "Jayden Daniels"
        assert add_drops[0]["dropped_player"]["name"] == "Sam Howell"
        assert add_drops[0]["faab_spent"] == 30

    def test_get_transactions_multiple_weeks(self):
        """Test transactions spanning multiple weeks."""
        self.mock_manager_transactions["Tommy"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "trades": {
                        "transaction_ids": ["trade1"]
                    }
                }
            },
            "2": {
                "transactions": {
                    "trades": {
                        "transaction_ids": ["trade2"]
                    }
                }
            },
        }
        self.mock_get_trade_card.return_value = {
            "year": "2023",
            "week": "1",
            "managers_involved": ["Tommy", "Benz"],
        }

        result = get_manager_transactions("Tommy", year="2023")

        assert result["total_count"] == 2
