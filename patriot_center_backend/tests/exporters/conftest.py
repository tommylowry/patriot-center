"""This module contains fixtures for testing the exporters."""

from typing import Any

import pytest


@pytest.fixture
def mock_manager_cache() -> dict[str, Any]:
    """Create a sample cache for testing.

    Returns:
        Sample manager cache
    """
    return {
        "Manager 1": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 10},
                        "losses": {"total": 5},
                        "ties": {"total": 1},
                    }
                },
                "transactions": {
                    "trades": {"total": 5},
                    "adds": {"total": 10},
                    "drops": {"total": 10},
                },
                "overall_data": {
                    "placement": {"2023": 1, "2022": 3},
                    "playoff_appearances": ["2023", "2022"],
                },
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {"wins": {"total": 1, "opponents": {}}}
                        },
                        "transactions": {"trades": {"total": 1}},
                    },
                    "weeks": {},
                },
                "2022": {"summary": {}, "weeks": {}},
            },
        },
        "Manager 2": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 5},
                        "losses": {"total": 10},
                        "ties": {"total": 1},
                    }
                },
                "transactions": {
                    "trades": {"total": 3},
                    "adds": {"total": 8},
                    "drops": {"total": 8},
                },
                "overall_data": {
                    "placement": {"2023": 5},
                    "playoff_appearances": ["2023"],
                },
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {"wins": {"total": 1, "opponents": {}}}
                        },
                        "transactions": {"trades": {"total": 1}},
                    },
                    "weeks": {},
                }
            },
        },
    }


@pytest.fixture
def mock_valid_options_cache() -> dict[str, Any]:
    """Create a sample valid options cache.

    Returns:
        Sample valid options cache
    """
    return {"2025": {"managers": ["Manager 1", "Manager 2"]}}
