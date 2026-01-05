"""
Unit tests for transaction_processor module.

Tests the TransactionProcessor class which handles all transaction-related operations.
All tests mock API calls and avoid touching real cache files.
"""
import pytest
from unittest.mock import patch, MagicMock
from copy import deepcopy
from patriot_center_backend.managers.transaction_processor import TransactionProcessor


@pytest.fixture
def sample_cache():
    """Create a sample cache for testing."""
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
def processor(sample_cache):
    """Create TransactionProcessor instance."""
    return TransactionProcessor(
        cache=sample_cache,
        transaction_ids_cache={},
        players_cache={},
        player_ids={"player1": {"full_name": "Player One"}, "player2": {"full_name": "Player Two"}},
        use_faab=True
    )


class TestTransactionProcessorInit:
    """Test TransactionProcessor initialization."""

    def test_init_stores_caches(self, sample_cache):
        """Test that __init__ stores all cache references."""
        transaction_ids_cache = {}
        players_cache = {}
        player_ids = {}

        processor = TransactionProcessor(
            cache=sample_cache,
            transaction_ids_cache=transaction_ids_cache,
            players_cache=players_cache,
            player_ids=player_ids,
            use_faab=True
        )

        assert processor._cache is sample_cache
        assert processor._transaction_ids_cache is transaction_ids_cache
        assert processor._players_cache is players_cache
        assert processor._player_ids is player_ids
        assert processor._use_faab is True

    def test_init_with_faab_disabled(self, sample_cache):
        """Test initialization with FAAB disabled."""
        processor = TransactionProcessor(
            cache=sample_cache,
            transaction_ids_cache={},
            players_cache={},
            player_ids={},
            use_faab=False
        )

        assert processor._use_faab is False

    def test_init_sets_default_session_state(self, sample_cache):
        """Test that __init__ initializes empty session state."""
        processor = TransactionProcessor(
            cache=sample_cache,
            transaction_ids_cache={},
            players_cache={},
            player_ids={},
            use_faab=True
        )

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

    @patch('patriot_center_backend.managers.transaction_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_processes_transactions(self, mock_fetch, processor):
        """Test that scrub_transaction_data fetches and processes transactions."""
        mock_fetch.return_value = ([
            {
                "transaction_id": "trans1",
                "type": "free_agent",
                "adds": {"player1": 1},
                "drops": None
            }
        ], 200)

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        with patch.object(processor, '_process_transaction') as mock_process:
            processor.scrub_transaction_data("2023", "1")

            # Should process the transaction
            assert mock_process.called
            assert mock_process.call_count == 1

    @patch('patriot_center_backend.managers.transaction_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_reverses_order(self, mock_fetch, processor):
        """Test that transactions are reversed (oldest first)."""
        mock_fetch.return_value = ([
            {"transaction_id": "trans1", "type": "free_agent"},
            {"transaction_id": "trans2", "type": "free_agent"},
            {"transaction_id": "trans3", "type": "free_agent"}
        ], 200)

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


class TestCheckForReverseTransactions:
    """Test check_for_reverse_transactions method."""

    def test_check_for_reverse_transactions_detects_reversal(self, processor):
        """Test that reversed trades are detected and removed."""
        # Set up two transactions that reverse each other
        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"},
                    "Player Two": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
                }
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 2", "new_manager": "Manager 1"},
                    "Player Two": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        with patch.object(processor, '_revert_trade_transaction') as mock_revert:
            processor.check_for_reverse_transactions()

            # Should detect reversal and revert
            assert mock_revert.called

    def test_check_for_reverse_transactions_no_reversal(self, processor):
        """Test that non-reversed transactions are not removed."""
        # Set up two transactions that do NOT reverse each other
        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player Two"],
                "trade_details": {
                    "Player Two": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        with patch.object(processor, '_revert_trade_transaction') as mock_revert:
            processor.check_for_reverse_transactions()

            # Should NOT detect reversal
            assert not mock_revert.called

    def test_commissioner_add_then_drop_reversal(self, processor):
        """Test commissioner adds player, then player is dropped (reversal)."""
        # Setup session state
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False

        # Setup cache with both transactions
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1

        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        # Call reversal detection - this should actually execute the reversal logic
        processor.check_for_reverse_transactions()

        # Verify both transactions were removed from cache
        assert "trans1" not in processor._transaction_ids_cache
        assert "trans2" not in processor._transaction_ids_cache
        assert len(processor._weekly_transaction_ids) == 0

        # Verify cache was decremented
        assert processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 0
        assert processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 0
        assert "Player One" not in processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]
        assert "Player One" not in processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]

    def test_commissioner_drop_then_add_reversal(self, processor):
        """Test commissioner drops player, then player is added (reversal)."""
        # Setup session state
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False

        # Setup cache with both transactions
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1

        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        # Call reversal detection
        processor.check_for_reverse_transactions()

        # Verify both transactions were removed
        assert "trans1" not in processor._transaction_ids_cache
        assert "trans2" not in processor._transaction_ids_cache
        assert len(processor._weekly_transaction_ids) == 0

        # Verify cache was decremented
        assert processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 0
        assert processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 0

    def test_regular_transaction_then_commissioner_reversal(self, processor):
        """Test regular add/drop followed by commissioner reversal."""
        # Setup session state
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False

        # Setup cache with both transactions
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player One"] = 1

        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player One"],
                "drop": "Player One"
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        # Call reversal detection
        processor.check_for_reverse_transactions()

        # Verify both transactions were removed
        assert "trans1" not in processor._transaction_ids_cache
        assert "trans2" not in processor._transaction_ids_cache
        assert len(processor._weekly_transaction_ids) == 0

        # Verify cache was decremented
        assert processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 0
        assert processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 0

    def test_commissioner_reversal_with_different_players_no_match(self, processor):
        """Test commissioner transactions with different players don't reverse."""
        # Setup session state
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False

        # Setup cache with both transactions (different players)
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player Two"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1

        processor._transaction_ids_cache = {
            "trans1": {
                "year": "2023",
                "week": "1",
                "commish_action": True,
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            },
            "trans2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player Two"],
                "drop": "Player Two"
            }
        }
        processor._weekly_transaction_ids = ["trans1", "trans2"]

        # Call reversal detection
        processor.check_for_reverse_transactions()

        # Verify NO transactions were removed (different players, so no reversal)
        assert "trans1" in processor._transaction_ids_cache
        assert "trans2" in processor._transaction_ids_cache

        # Verify cache was NOT decremented (transactions remain)
        assert processor._cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 1
        assert processor._cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 1


class TestProcessTransaction:
    """Test _process_transaction method."""

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_process_transaction_validates(self, mock_validate, processor):
        """Test that transaction is validated before processing."""
        mock_validate.return_value = False

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        processor._process_transaction(transaction)

        # Should validate
        assert mock_validate.called

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_process_transaction_routes_to_add_or_drop(self, mock_validate, processor):
        """Test that free_agent/waiver transactions are routed to add_or_drop."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        with patch.object(processor, '_process_add_or_drop_transaction') as mock_process:
            processor._process_transaction(transaction)

            assert mock_process.called

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_process_transaction_routes_to_trade(self, mock_validate, processor):
        """Test that trade transactions are routed to trade processor."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)
        transaction = {
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player2": 1, "player1": 2}
        }

        with patch.object(processor, '_process_trade_transaction') as mock_process:
            processor._process_transaction(transaction)

            assert mock_process.called

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_process_transaction_detects_commissioner_action(self, mock_validate, processor):
        """Test that commissioner actions are detected."""
        mock_validate.return_value = True

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {
            "type": "commissioner",
            "adds": {"player1": 1},
            "drops": None
        }

        with patch.object(processor, '_process_add_or_drop_transaction') as mock_process:
            processor._process_transaction(transaction)

            # Should pass commish_action=True
            assert mock_process.call_args[0][1] is True


class TestAddTradeDetailsToCache:
    """Test _add_trade_details_to_cache method."""

    @patch('patriot_center_backend.managers.transaction_processor.update_players_cache')
    def test_add_trade_details_updates_cache(self, mock_update, processor):
        """Test that trade details are added to cache at all levels."""
        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        processor._add_trade_details_to_cache(
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={"Player Two": "Manager 2"},
            transaction_id="trans1",
            commish_action=False
        )

        # Check weekly summary
        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1
        assert "Manager 2" in weekly["trade_partners"]
        assert "Player One" in weekly["trade_players_acquired"]
        assert "Player Two" in weekly["trade_players_sent"]

    @patch('patriot_center_backend.managers.transaction_processor.update_players_cache')
    def test_add_trade_details_prevents_duplicates(self, mock_update, processor):
        """Test that duplicate transaction IDs are not processed twice."""
        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        # Add once
        processor._add_trade_details_to_cache(
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={},
            transaction_id="trans1",
            commish_action=False
        )

        # Try to add again
        processor._add_trade_details_to_cache(
            manager="Manager 1",
            trade_partners=["Manager 2"],
            acquired={"Player One": "Manager 2"},
            sent={},
            transaction_id="trans1",
            commish_action=False
        )

        # Should only have 1 trade
        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1


class TestAddAddOrDropDetailsToCache:
    """Test _add_add_or_drop_details_to_cache method."""

    def test_add_add_details_updates_cache(self, processor):
        """Test that add details are added to cache at all levels."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_add_or_drop_details_to_cache(
            free_agent_type="add",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False,
            waiver_bid=None
        )

        # Check weekly summary
        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"] == 1

    def test_add_drop_details_updates_cache(self, processor):
        """Test that drop details are added to cache at all levels."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_add_or_drop_details_to_cache(
            free_agent_type="drop",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False
        )

        # Check weekly summary
        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]

    def test_add_add_or_drop_invalid_type(self, processor):
        """Test that invalid type is handled gracefully."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        # Should return without error
        result = processor._add_add_or_drop_details_to_cache(
            free_agent_type="invalid",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False
        )

        assert result is None


class TestAddFaabDetailsToCache:
    """Test _add_faab_details_to_cache method."""

    def test_add_faab_waiver_details(self, processor):
        """Test that FAAB waiver details are added to cache."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_faab_details_to_cache(
            transaction_type="waiver",
            manager="Manager 1",
            player_name="Player One",
            faab_amount=50,
            transaction_id="trans1",
            trade_partner=None
        )

        # Check weekly summary
        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -50
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"]["num_bids_won"] == 1
        assert weekly["players"]["Player One"]["total_faab_spent"] == 50

    def test_add_faab_trade_details(self, processor):
        """Test that FAAB trade details are added to cache."""
        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        # Manager 1 receives FAAB (positive amount)
        processor._add_faab_details_to_cache(
            transaction_type="trade",
            manager="Manager 1",
            player_name="FAAB",
            faab_amount=100,
            transaction_id="trans1",
            trade_partner="Manager 2"
        )

        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == 100
        assert weekly["acquired_from"]["total"] == 100
        assert "Manager 2" in weekly["acquired_from"]["trade_partners"]

    def test_add_faab_trade_sent(self, processor):
        """Test that FAAB sent in trade is tracked correctly."""
        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        # Manager 1 sends FAAB (negative amount)
        processor._add_faab_details_to_cache(
            transaction_type="trade",
            manager="Manager 1",
            player_name="FAAB",
            faab_amount=-100,
            transaction_id="trans1",
            trade_partner="Manager 2"
        )

        weekly = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -100
        assert weekly["traded_away"]["total"] == 100
        assert "Manager 2" in weekly["traded_away"]["trade_partners"]


class TestAddToTransactionIdsCache:
    """Test _add_to_transaction_ids_cache method."""

    def test_add_trade_to_cache(self, processor):
        """Test adding trade to transaction IDs cache."""
        processor.set_session_state("2023", "1", {1: "Manager 1", 2: "Manager 2"}, True)

        processor._add_to_transaction_ids_cache(
            {
                "type": "trade",
                "manager": "Manager 1",
                "trade_partners": ["Manager 2"],
                "acquired": {"Player One": "Manager 2"},
                "sent": {"Player Two": "Manager 2"},
                "transaction_id": "trans1"
            },
            commish_action=False
        )

        assert "trans1" in processor._transaction_ids_cache
        assert processor._transaction_ids_cache["trans1"]["year"] == "2023"
        assert processor._transaction_ids_cache["trans1"]["week"] == "1"
        assert "Manager 1" in processor._transaction_ids_cache["trans1"]["managers_involved"]
        assert "Manager 2" in processor._transaction_ids_cache["trans1"]["managers_involved"]

    def test_add_add_or_drop_to_cache(self, processor):
        """Test adding add/drop to transaction IDs cache."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_to_transaction_ids_cache(
            {
                "type": "add_or_drop",
                "free_agent_type": "add",
                "manager": "Manager 1",
                "player_name": "Player One",
                "transaction_id": "trans1",
                "waiver_bid": 50
            },
            commish_action=False
        )

        assert "trans1" in processor._transaction_ids_cache
        assert processor._transaction_ids_cache["trans1"]["add"] == "Player One"
        assert processor._transaction_ids_cache["trans1"]["faab_spent"] == 50

    def test_add_to_cache_missing_type(self, processor):
        """Test that missing type raises ValueError."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        with pytest.raises(ValueError, match="Transaction type not found"):
            processor._add_to_transaction_ids_cache(
                {"transaction_id": "trans1", "manager": "Manager 1"},
                commish_action=False
            )

    def test_add_to_cache_missing_transaction_id(self, processor):
        """Test that missing transaction_id raises ValueError."""
        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        with pytest.raises(ValueError, match="transaction_id not found"):
            processor._add_to_transaction_ids_cache(
                {"type": "trade", "manager": "Manager 1"},
                commish_action=False
            )


class TestCacheModification:
    """Test that processor correctly modifies caches in-place."""

    def test_processor_modifies_cache_in_place(self, sample_cache):
        """Test that processor modifies the cache that was passed in."""
        original_cache = sample_cache
        processor = TransactionProcessor(
            cache=sample_cache,
            transaction_ids_cache={},
            players_cache={},
            player_ids={},
            use_faab=True
        )

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_add_or_drop_details_to_cache(
            free_agent_type="add",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False
        )

        # Verify cache was modified (same object reference)
        assert processor._cache is original_cache
        assert original_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] == 1


class TestProcessTradeTransaction:
    """Test _process_trade_transaction with actual trade processing."""

    def test_process_simple_two_team_trade(self, processor):
        """Test processing a simple 2-team player swap."""
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        processor._player_ids = {
            "player1": {"full_name": "Player One"},
            "player2": {"full_name": "Player Two"}
        }

        transaction = {
            "type": "trade",
            "transaction_id": "trade1",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},  # Manager 1 gets player1, Manager 2 gets player2
            "drops": {"player1": 2, "player2": 1},  # Manager 1 sends player2, Manager 2 sends player1
            "draft_picks": None,
            "waiver_budget": []
        }

        processor._process_trade_transaction(transaction, commish_action=False)

        # Verify Manager 1 acquired player1
        assert processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1
        assert "trade1" in processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"]

        # Verify Manager 2 acquired player2
        assert processor._cache["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_draft_picks(self, processor):
        """Test processing trade that includes draft picks."""
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        processor._player_ids = {"player1": {"full_name": "Player One"}}

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

        processor._process_trade_transaction(transaction, commish_action=False)

        # Should process successfully
        assert processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_faab(self, processor):
        """Test processing trade that includes FAAB exchange."""
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = True
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        processor._player_ids = {"player1": {"full_name": "Player One"}}

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

        processor._process_trade_transaction(transaction, commish_action=False)

        # Verify FAAB was tracked
        assert processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["total"] == 50
        assert processor._cache["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["total"] == 50


class TestCommissionerTransactionTypes:
    """Test commissioner transaction type detection in _process_transaction."""

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_commissioner_add_only(self, mock_validate, processor):
        """Test commissioner action with only adds (no drops)."""
        mock_validate.return_value = True
        processor._year = "2023"
        processor._week = "1"
        processor._weekly_roster_ids = {1: "Manager 1"}
        processor._player_ids = {"player1": {"full_name": "Player One"}}

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm1",
            "adds": {"player1": 1},
            "drops": None  # No drops means add_or_drop type
        }

        with patch.object(processor, '_process_add_or_drop_transaction') as mock_add_drop:
            processor._process_transaction(transaction)
            # Should call add_or_drop processor with commish_action=True
            assert mock_add_drop.called
            assert mock_add_drop.call_args[0][1] == True  # commish_action

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_commissioner_forced_trade(self, mock_validate, processor):
        """Test commissioner action with multiple players (forced trade)."""
        mock_validate.return_value = True
        processor._year = "2023"
        processor._week = "1"
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        processor._player_ids = {
            "player1": {"full_name": "Player One"},
            "player2": {"full_name": "Player Two"}
        }

        transaction = {
            "type": "commissioner",
            "transaction_id": "comm2",
            "roster_ids": [1, 2],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player1": 2, "player2": 1}
        }

        with patch.object(processor, '_process_trade_transaction') as mock_trade:
            processor._process_transaction(transaction)
            # Should call trade processor with commish_action=True
            assert mock_trade.called
            assert mock_trade.call_args[0][1] == True  # commish_action


class TestTradeReversalDetection:
    """Test trade reversal detection (joke trades)."""

    def test_trade_reversal_same_players_opposite_direction(self, processor):
        """Test detecting and reverting joke trade (same players swapped back)."""
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False

        # Setup: Two trades with same players, opposite directions
        processor._transaction_ids_cache = {
            "trade1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"},
                    "Player Two": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
                }
            },
            "trade2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One", "Player Two"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 2", "new_manager": "Manager 1"},  # Reversed!
                    "Player Two": {"old_manager": "Manager 1", "new_manager": "Manager 2"}   # Reversed!
                }
            }
        }
        processor._weekly_transaction_ids = ["trade1", "trade2"]

        # Setup cache as if trades were processed
        for manager in ["Manager 1", "Manager 2"]:
            processor._cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 2
            processor._cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            processor._cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 2
            processor._cache[manager]["summary"]["transactions"]["trades"]["total"] = 2

        # Detect and revert
        processor.check_for_reverse_transactions()

        # Both trades should be removed
        assert "trade1" not in processor._transaction_ids_cache
        assert "trade2" not in processor._transaction_ids_cache
        assert len(processor._weekly_transaction_ids) == 0

    def test_trade_no_reversal_different_players(self, processor):
        """Test that different trades don't get reversed."""
        processor._year = "2023"
        processor._week = "1"

        processor._transaction_ids_cache = {
            "trade1": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player One"],
                "trade_details": {
                    "Player One": {"old_manager": "Manager 1", "new_manager": "Manager 2"}
                }
            },
            "trade2": {
                "year": "2023",
                "week": "1",
                "commish_action": False,
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["trade"],
                "players_involved": ["Player Three"],  # Different player!
                "trade_details": {
                    "Player Three": {"old_manager": "Manager 2", "new_manager": "Manager 1"}
                }
            }
        }
        processor._weekly_transaction_ids = ["trade1", "trade2"]

        processor.check_for_reverse_transactions()

        # Trades should NOT be removed (different players)
        assert "trade1" in processor._transaction_ids_cache
        assert "trade2" in processor._transaction_ids_cache
