from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.add_drop_processor import (
    add_add_or_drop_details_to_cache,
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


class TestAddAddOrDropDetailsToCache:
    """Test add_add_or_drop_details_to_cache method."""

    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_manager_cache')
    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_to_transaction_ids')
    def test_add_add_details_updates_cache(self, mock_add_ids, mock_get_manager_cache, mock_manager_cache):
        """Test that add details are added to cache at all levels."""
        mock_get_manager_cache.return_value = mock_manager_cache

        add_add_or_drop_details_to_cache(
            year = "2023",
            week = "1",
            weekly_transaction_ids=[],
            free_agent_type="add",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False,
            use_faab=True,
            waiver_bid=None
        )

        # Check weekly summary
        weekly = mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"] == 1

    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_manager_cache')
    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_to_transaction_ids')
    def test_add_drop_details_updates_cache(self, mock_add_ids, mock_get_manager_cache, mock_manager_cache):
        """Test that drop details are added to cache at all levels."""
        mock_get_manager_cache.return_value = mock_manager_cache

        add_add_or_drop_details_to_cache(
            year = "2023",
            week = "1",
            weekly_transaction_ids=[],
            free_agent_type="drop",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False,
            use_faab=True,
            waiver_bid=None
        )

        # Check weekly summary
        weekly = mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]

    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_manager_cache')
    @patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_to_transaction_ids')
    def test_add_add_or_drop_invalid_type(self, mock_add_ids, mock_get_manager_cache, mock_manager_cache):
        """Test that invalid type is handled gracefully."""
        mock_get_manager_cache.return_value = mock_manager_cache

        # Should return without error
        result = add_add_or_drop_details_to_cache(
            year = "2023",
            week = "1",
            weekly_transaction_ids=[],
            free_agent_type="invalid",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False,
            use_faab=True
        )

        assert result is None