from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.trade_processor import (
    add_trade_details_to_cache,
)


@pytest.fixture
def mock_manager_cache():
    """Create a sample manager cache for testing."""
    return {
        "Manager 1": {
            "summary": {
                "transactions": {
                    "trades": {
                        "total": 0,
                        "trade_partners": {},
                        "trade_players_acquired": {},
                        "trade_players_sent": {},
                        "transaction_ids": []
                    },
                    "adds": {"total": 0, "players": {}, "transaction_ids": []},
                    "drops": {"total": 0, "players": {}, "transaction_ids": []},
                    "faab": {
                        "total_lost_or_gained": 0,
                        "players": {},
                        "acquired_from": {"total": 0, "trade_partners": {}},
                        "traded_away": {"total": 0, "trade_partners": {}},
                        "transaction_ids": []
                    }
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "transactions": {
                            "trades": {
                                "total": 0,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {},
                                "transaction_ids": []
                            },
                            "adds": {"total": 0, "players": {}, "transaction_ids": []},
                            "drops": {"total": 0, "players": {}, "transaction_ids": []},
                            "faab": {
                                "total_lost_or_gained": 0,
                                "players": {},
                                "acquired_from": {"total": 0, "trade_partners": {}},
                                "traded_away": {"total": 0, "trade_partners": {}},
                                "transaction_ids": []
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "transactions": {
                                "trades": {
                                    "total": 0,
                                    "trade_partners": {},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": []
                                },
                                "adds": {"total": 0, "players": {}, "transaction_ids": []},
                                "drops": {"total": 0, "players": {}, "transaction_ids": []},
                                "faab": {
                                    "total_lost_or_gained": 0,
                                    "players": {},
                                    "acquired_from": {"total": 0, "trade_partners": {}},
                                    "traded_away": {"total": 0, "trade_partners": {}},
                                    "transaction_ids": []
                                }
                            }
                        }
                    }
                }
            }
        },
        "Manager 2": {
            "summary": {
                "transactions": {
                    "trades": {
                        "total": 0,
                        "trade_partners": {},
                        "trade_players_acquired": {},
                        "trade_players_sent": {},
                        "transaction_ids": []
                    },
                    "adds": {"total": 0, "players": {}, "transaction_ids": []},
                    "drops": {"total": 0, "players": {}, "transaction_ids": []},
                    "faab": {
                        "total_lost_or_gained": 0,
                        "players": {},
                        "acquired_from": {"total": 0, "trade_partners": {}},
                        "traded_away": {"total": 0, "trade_partners": {}},
                        "transaction_ids": []
                    }
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "transactions": {
                            "trades": {
                                "total": 0,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {},
                                "transaction_ids": []
                            },
                            "adds": {"total": 0, "players": {}, "transaction_ids": []},
                            "drops": {"total": 0, "players": {}, "transaction_ids": []},
                            "faab": {
                                "total_lost_or_gained": 0,
                                "players": {},
                                "acquired_from": {"total": 0, "trade_partners": {}},
                                "traded_away": {"total": 0, "trade_partners": {}},
                                "transaction_ids": []
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "transactions": {
                                "trades": {
                                    "total": 0,
                                    "trade_partners": {},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": []
                                },
                                "adds": {"total": 0, "players": {}, "transaction_ids": []},
                                "drops": {"total": 0, "players": {}, "transaction_ids": []},
                                "faab": {
                                    "total_lost_or_gained": 0,
                                    "players": {},
                                    "acquired_from": {"total": 0, "trade_partners": {}},
                                    "traded_away": {"total": 0, "trade_partners": {}},
                                    "transaction_ids": []
                                }
                            }
                        }
                    }
                }
            }
        }
    }


class TestAddTradeDetailsToCache:
    """Test add_trade_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.trade_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.transaction_processing.trade_processor.update_players_cache'):
            
            self.mock_manager_cache = mock_manager_cache
            
            mock_get_manager.return_value = self.mock_manager_cache
            
            yield

    def test_add_trade_details_updates_cache(self):
        """Test that trade details are added to cache at all levels."""
        add_trade_details_to_cache(
            year = "2023",
            week = "1",
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={"Player Two": "Manager 2"},
            weekly_transaction_ids=[],
            transaction_id="trans1",
            commish_action=False,
            use_faab=True
        )

        # Check weekly summary
        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1
        assert "Manager 2" in weekly["trade_partners"]
        assert "Player One" in weekly["trade_players_acquired"]
        assert "Player Two" in weekly["trade_players_sent"]

    def test_add_trade_details_prevents_duplicates(self):
        """Test that duplicate transaction IDs are not processed twice."""

        # Add once
        add_trade_details_to_cache(
            year = "2023",
            week = "1",
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={},
            weekly_transaction_ids=[],
            transaction_id="trans1",
            commish_action=False,
            use_faab=True
        )

        # Try to add again
        add_trade_details_to_cache(
            year = "2023",
            week = "1",
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={},
            weekly_transaction_ids=[],
            transaction_id="trans1",
            commish_action=False,
            use_faab=True
        )

        # Should only have 1 trade
        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1