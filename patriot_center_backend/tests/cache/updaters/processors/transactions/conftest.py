"""This module contains fixtures for testing the transaction processing."""

from copy import deepcopy
from typing import Any

import pytest


@pytest.fixture
def mock_transaction_ids_cache() -> dict[str, Any]:
    """Create transaction IDs cache for testing trade reverts.

    Contains two trade transactions between Tommy and Jay with both
    player (Jayden Daniels) and FAAB ($50) details. This single fixture
    supports all revert test scenarios.

    Trade1: Tommy sends Jayden Daniels and $50 FAAB to Jay
    Trade2: Jay sends Jayden Daniels and $50 FAAB back to Tommy

    Returns:
        Transaction IDs cache with trade1 and trade2.
    """
    return {
        "trade1": {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Tommy", "Jay"],
            "types": ["trade"],
            "players_involved": ["Jayden Daniels", "$50 FAAB"],
            "trade_details": {
                "Jayden Daniels": {
                    "old_manager": "Tommy",
                    "new_manager": "Jay",
                },
                "$50 FAAB": {
                    "old_manager": "Tommy",
                    "new_manager": "Jay",
                },
            },
        },
        "trade2": {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Tommy", "Jay"],
            "types": ["trade"],
            "players_involved": ["Jayden Daniels", "$50 FAAB"],
            "trade_details": {
                "Jayden Daniels": {
                    "old_manager": "Jay",
                    "new_manager": "Tommy",
                },
                "$50 FAAB": {
                    "old_manager": "Jay",
                    "new_manager": "Tommy",
                },
            },
        },
    }


def _create_manager_trades_data(trade_partner: str) -> dict[str, Any]:
    """Create trades data structure for a manager.

    Args:
        trade_partner: Name of the trade partner.

    Returns:
        Trades data dict with all fields populated.
    """
    return {
        "total": 4,
        "trade_partners": {trade_partner: 2},
        "trade_players_acquired": {
            "Jayden Daniels": {
                "total": 1,
                "trade_partners": {trade_partner: 1},
            },
            "$50 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}},
        },
        "trade_players_sent": {
            "Jayden Daniels": {
                "total": 1,
                "trade_partners": {trade_partner: 1},
            },
            "$50 FAAB": {"total": 1, "trade_partners": {trade_partner: 1}},
        },
        "transaction_ids": ["trade1", "trade2"],
    }


def _create_manager_faab_data(trade_partner: str) -> dict[str, Any]:
    """Create FAAB data structure for a manager.

    Args:
        trade_partner: Name of the trade partner.

    Returns:
        FAAB data dict with traded/acquired tracking.
    """
    return {
        "total_lost_or_gained": 0,
        "players": {},
        "acquired_from": {"total": 50, "trade_partners": {trade_partner: 50}},
        "traded_away": {"total": 50, "trade_partners": {trade_partner: 50}},
        "transaction_ids": ["trade1", "trade2"],
    }


def _create_manager_structure(trade_partner: str) -> dict[str, Any]:
    """Create full manager cache structure.

    Args:
        trade_partner: Name of the trade partner.

    Returns:
        Complete manager cache structure.
    """
    trades = _create_manager_trades_data(trade_partner)
    faab = _create_manager_faab_data(trade_partner)
    adds = {"total": 0, "players": {}, "transaction_ids": []}
    drops = {"total": 0, "players": {}, "transaction_ids": []}

    return {
        "summary": {
            "transactions": {
                "trades": deepcopy(trades),
                "adds": deepcopy(adds),
                "drops": deepcopy(drops),
                "faab": deepcopy(faab),
            }
        },
        "years": {
            "2023": {
                "summary": {
                    "transactions": {
                        "trades": deepcopy(trades),
                        "adds": deepcopy(adds),
                        "drops": deepcopy(drops),
                        "faab": deepcopy(faab),
                    }
                },
                "weeks": {
                    "1": {
                        "transactions": {
                            "trades": deepcopy(trades),
                            "adds": deepcopy(adds),
                            "drops": deepcopy(drops),
                            "faab": deepcopy(faab),
                        }
                    }
                },
            }
        },
    }


@pytest.fixture
def mock_manager_cache() -> dict[str, Any]:
    """Create manager cache for testing trade operations.

    Contains Tommy and Jay with:
    - 4 total trades
    - 2 trades with each other as partners
    - Jayden Daniels in acquired/sent (1 each)
    - $50 FAAB in acquired/sent (1 each)
    - FAAB tracking: 50 traded_away, 50 acquired_from
    - transaction_ids: ["trade1", "trade2"]

    This single fixture supports all trade processor test scenarios.

    Returns:
        Manager cache with comprehensive trade data.
    """
    return {
        "Tommy": _create_manager_structure("Jay"),
        "Jay": _create_manager_structure("Tommy"),
    }
