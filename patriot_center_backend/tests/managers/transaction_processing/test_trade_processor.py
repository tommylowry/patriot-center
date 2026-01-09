from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.trade_processor import (
    add_trade_details_to_cache,
    process_trade_transaction,
    revert_trade_transaction,
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


@pytest.fixture
def mock_player_ids_cache():
    """Create a sample player ids cache for testing."""
    return {
        "player1": {"full_name": "Player One"},
        "player2": {"full_name": "Player Two"}
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


class TestRevertTradeTransaction:
    """Test revert_trade_transaction method - unit tests calling function directly."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.trade_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.transaction_processing.trade_processor.CACHE_MANAGER.get_transaction_ids_cache') as mock_get_trans_ids:
            
            self.mock_manager_cache = mock_manager_cache
            self.mock_transaction_ids_cache = {}
            self.weekly_transaction_ids = ["trade1", "trade2"]

            mock_get_manager.return_value = self.mock_manager_cache
            mock_get_trans_ids.return_value = self.mock_transaction_ids_cache
            
            yield

    def test_revert_simple_trade_removes_both_transactions(self):
        """Test revert_trade_transaction removes both trades from cache."""

        # Setup cache for both managers - use total=2 since we're removing all trades
        for manager in ["Manager 1", "Manager 2"]:
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 2
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 2
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 2
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }

            # Setup acquired/sent
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["Player One"],
            "trade_details": {
                "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
            }
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["Player One"],
            "trade_details": {
                "Player One": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
            }
        }

        # Call function directly
        revert_trade_transaction(
            transaction_id1="trade1",
            transaction_id2="trade2",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Assert only THIS function's behavior
        assert "trade1" not in self.mock_transaction_ids_cache
        assert "trade2" not in self.mock_transaction_ids_cache
        assert len(self.weekly_transaction_ids) == 0
        assert self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["trades"]["total"] == 0
        assert self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["trades"]["trade_partners"] == {}

    def test_revert_trade_with_faab_removes_faab_data(self):
        """Test revert_trade_transaction removes FAAB data."""

        # Setup basic trade cache - use 4 total so after decrementing 2, there are still 2 left
        # (if total goes to 0, the code continues and skips FAAB decrement logic)
        for manager in ["Manager 1", "Manager 2"]:
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 4
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 4
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 4
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }

            # Setup acquired/sent for FAAB
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

        # Setup FAAB cache - the code decrements both traded_away and acquired_from for each manager
        # Set up both fields for both managers
        for manager, partner in [("Manager 1", "Manager 2"), ("Manager 2", "Manager 1")]:
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["total"] = 100
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["traded_away"]["total"] = 100
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

            self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["traded_away"]["total"] = 100
            self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["$100 FAAB"],
            "trade_details": {
                "$100 FAAB": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
            }
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": ["$100 FAAB"],
            "trade_details": {
                "$100 FAAB": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
            }
        }

        revert_trade_transaction(
            transaction_id1="trade1",
            transaction_id2="trade2",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Assert FAAB was removed
        assert self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"]["traded_away"]["total"] == 0
        assert self.mock_manager_cache["Manager 2"]["summary"]["transactions"]["faab"]["acquired_from"]["total"] == 0
        assert "Manager 2" not in self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"]

    def test_revert_trade_removes_from_weekly_transaction_ids(self):
        """Test revert_trade_transaction removes IDs from weekly list."""

        # Setup with 3 trades total
        for manager in ["Manager 1", "Manager 2"]:
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 3
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2", "trade3"]
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 3
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 3
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }

            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {}
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {}
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {}
            self.mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {}
            self.mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {}
            self.mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {}

        self.mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {}
        }
        self.mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {}
        }
        
        # Adding in a 3rd trade that should still be in there
        self.weekly_transaction_ids.append("trade3")

        revert_trade_transaction(
            transaction_id1="trade1",
            transaction_id2="trade2",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Assert trade3 still exists
        assert "trade3" in self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"]
        assert "trade1" not in self.weekly_transaction_ids
        assert "trade2" not in self.weekly_transaction_ids
        assert "trade3" in self.weekly_transaction_ids


class TestProcessTradeTransaction:
    """Test process_trade_transaction with actual trade processing."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache, mock_player_ids_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.trade_processor.update_players_cache'), \
             patch('patriot_center_backend.managers.transaction_processing.trade_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.transaction_processing.trade_processor.CACHE_MANAGER.get_player_ids_cache') as mock_get_player_ids:
            
            self.mock_manager_cache = mock_manager_cache
            self.mock_player_ids_cache = mock_player_ids_cache

            mock_get_manager.return_value = self.mock_manager_cache
            mock_get_player_ids.return_value = self.mock_player_ids_cache
            
            yield

    def test_process_simple_two_team_trade(self):
        """Test processing a simple 2-team player swap."""
        transaction = {
            "type": "trade",
            "transaction_id": "trade1",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},  # Manager 1 gets player1, Manager 2 gets player2
            "drops": {"player1": 2, "player2": 1},  # Manager 1 sends player2, Manager 2 sends player1
            "draft_picks": None,
            "waiver_budget": []
        }

        process_trade_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1", 2: "Manager 2"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=False
        )

        # Verify Manager 1 acquired player1
        assert self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1
        assert "trade1" in self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"]

        # Verify Manager 2 acquired player2
        assert self.mock_manager_cache["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_draft_picks(self):
        """Test processing trade that includes draft picks."""
        transaction = {
            "type": "trade",
            "transaction_id": "trade2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player1": 2},
            "draft_picks": [
                {
                    "season": "2024",
                    "round": 1,
                    "roster_id": 2,  # Manager 1 acquired this pick
                    "owner_id": 1,
                    "previous_owner_id": 2
                }
            ],
            "waiver_budget": []
        }

        process_trade_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1", 2: "Manager 2"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=False
        )

        # Should process successfully
        assert self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_faab(self):
        """Test processing trade that includes FAAB exchange."""
        transaction = {
            "type": "trade",
            "transaction_id": "trade3",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player1": 2},
            "draft_picks": None,
            "waiver_budget": [
                {
                    "sender": 1,
                    "receiver": 2,
                    "amount": 50
                }
            ]
        }

        process_trade_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1", 2: "Manager 2"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=True
        )

        # Verify FAAB was tracked
        assert self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["total"] == 50
        assert self.mock_manager_cache["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["total"] == 50