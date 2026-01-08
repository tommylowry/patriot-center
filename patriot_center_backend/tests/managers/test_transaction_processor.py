"""
Unit tests for transaction_processor module.

Tests the TransactionProcessor class which handles all transaction-related operations.
All tests mock API calls and avoid touching real cache files.
"""
import pytest
from unittest.mock import patch, MagicMock
from copy import deepcopy


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

@pytest.fixture
def mock_transaction_ids_cache():
    """Create a blank transaction ids cache for testing."""
    return {}


@pytest.fixture(autouse=True)
def patch_caches(mock_manager_cache, mock_player_ids_cache, mock_transaction_ids_cache):
    with patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache), \
         patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache), \
         patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
        yield


@pytest.fixture
def processor():
    """Create TransactionProcessor instance."""
    from patriot_center_backend.managers.transaction_processor import TransactionProcessor
    return TransactionProcessor(use_faab=True)


class TestTransactionProcessorInit:
    """Test TransactionProcessor initialization."""

    def test_init_stores_caches(self):
        """Test that __init__ stores all cache references."""
        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        
        processor = TransactionProcessor(use_faab=True)

        assert processor._use_faab is True

    def test_init_with_faab_disabled(self):
        """Test initialization with FAAB disabled."""
        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        
        processor = TransactionProcessor(use_faab=False)

        assert processor._use_faab is False

    def test_init_sets_default_session_state(self):
        """Test that __init__ initializes empty session state."""
        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        
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

    @patch('patriot_center_backend.managers.transaction_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_processes_transactions(self, mock_fetch, processor):
        """Test that scrub_transaction_data fetches and processes transactions."""
        mock_fetch.return_value = [
            {
                "transaction_id": "trans1",
                "type": "free_agent",
                "adds": {"player1": 1},
                "drops": None
            }
        ]

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        with patch.object(processor, '_process_transaction') as mock_process:
            processor.scrub_transaction_data("2023", "1")

            # Should process the transaction
            assert mock_process.called
            assert mock_process.call_count == 1

    @patch('patriot_center_backend.managers.transaction_processor.fetch_sleeper_data')
    def test_scrub_transaction_data_reverses_order(self, mock_fetch, processor):
        """Test that transactions are reversed (oldest first)."""
        mock_fetch.return_value = [
            {"transaction_id": "trans1", "type": "free_agent"},
            {"transaction_id": "trans2", "type": "free_agent"},
            {"transaction_id": "trans3", "type": "free_agent"}
        ]

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

    def test_check_for_reverse_transactions_detects_reversal(self):
        """Test that reversed trades are detected and removed."""
        # Set up two transactions that reverse each other
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
        
            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_trade_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should detect reversal and revert
                assert mock_revert.called

    def test_check_for_reverse_transactions_no_reversal(self):
        """Test that non-reversed transactions are not removed."""
        # Set up two transactions that do NOT reverse each other
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
            
            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_trade_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should NOT detect reversal
                assert not mock_revert.called

    def test_commissioner_add_then_drop_reversal(self):
        """Test check_for_reverse_transactions detects commissioner add followed by drop."""
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_add_drop_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should detect reversal and call revert for both add and drop
                assert mock_revert.call_count == 2
                # Check that it was called with the correct transaction IDs and types
                calls = [call[0] for call in mock_revert.call_args_list]
                assert ("trans1", "add") in calls
                assert ("trans2", "drop") in calls

    def test_commissioner_drop_then_add_reversal(self):
        """Test check_for_reverse_transactions detects commissioner drop followed by add."""
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
            
            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_add_drop_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should detect reversal and call revert for both drop and add
                assert mock_revert.call_count == 2
                calls = [call[0] for call in mock_revert.call_args_list]
                assert ("trans1", "drop") in calls
                assert ("trans2", "add") in calls

    def test_regular_transaction_then_commissioner_reversal(self):
        """Test check_for_reverse_transactions detects regular add followed by commissioner drop."""
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
            
            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_add_drop_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should detect reversal and call revert for both add and drop
                assert mock_revert.call_count == 2
                calls = [call[0] for call in mock_revert.call_args_list]
                assert ("trans1", "add") in calls
                assert ("trans2", "drop") in calls

    def test_commissioner_reversal_with_different_players_no_match(self):
        """Test check_for_reverse_transactions doesn't detect reversal with different players."""
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
            
            processor._weekly_transaction_ids = ["trans1", "trans2"]

            with patch.object(processor, '_revert_add_drop_transaction') as mock_revert:
                processor.check_for_reverse_transactions()

                # Should NOT detect reversal because players are different
                assert not mock_revert.called


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
    def test_process_transaction_routes_to_add_or_drop(self, mock_validate):
        """Test that free_agent/waiver transactions are routed to add_or_drop."""
        mock_validate.return_value = True

        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        processor = TransactionProcessor(use_faab=True)

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)
        transaction = {"type": "free_agent", "adds": {"player1": 1}, "drops": None}

        with patch.object(processor, '_process_add_or_drop_transaction') as mock_process:
            processor._process_transaction(transaction)

            assert mock_process.called

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_process_transaction_routes_to_trade(self, mock_validate):
        """Test that trade transactions are routed to trade processor."""
        mock_validate.return_value = True

        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        processor = TransactionProcessor(use_faab=True)

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
    def test_process_transaction_detects_commissioner_action(self, mock_validate):
        """Test that commissioner actions are detected."""
        mock_validate.return_value = True

        from patriot_center_backend.managers.transaction_processor import TransactionProcessor
        processor = TransactionProcessor(use_faab=True)

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
    def test_add_trade_details_updates_cache(self, mock_update):
        """Test that trade details are added to cache at all levels."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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
        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1
        assert "Manager 2" in weekly["trade_partners"]
        assert "Player One" in weekly["trade_players_acquired"]
        assert "Player Two" in weekly["trade_players_sent"]

    @patch('patriot_center_backend.managers.transaction_processor.update_players_cache')
    def test_add_trade_details_prevents_duplicates(self, mock_update):
        """Test that duplicate transaction IDs are not processed twice."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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
        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]
        assert weekly["total"] == 1


class TestAddAddOrDropDetailsToCache:
    """Test _add_add_or_drop_details_to_cache method."""

    def test_add_add_details_updates_cache(self):
        """Test that add details are added to cache at all levels."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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
        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"] == 1

    def test_add_drop_details_updates_cache(self):
        """Test that drop details are added to cache at all levels."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

        processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

        processor._add_add_or_drop_details_to_cache(
            free_agent_type="drop",
            manager="Manager 1",
            player_name="Player One",
            transaction_id="trans1",
            commish_action=False
        )

        # Check weekly summary
        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]
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

    def test_add_faab_waiver_details(self):
        """Test that FAAB waiver details are added to cache."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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
        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -50
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"]["num_bids_won"] == 1
        assert weekly["players"]["Player One"]["total_faab_spent"] == 50

    def test_add_faab_trade_details(self):
        """Test that FAAB trade details are added to cache."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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

        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == 100
        assert weekly["acquired_from"]["total"] == 100
        assert "Manager 2" in weekly["acquired_from"]["trade_partners"]

    def test_add_faab_trade_sent(self):
        """Test that FAAB sent in trade is tracked correctly."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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

        weekly = transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]
        assert weekly["total_lost_or_gained"] == -100
        assert weekly["traded_away"]["total"] == 100
        assert "Manager 2" in weekly["traded_away"]["trade_partners"]


class TestAddToTransactionIdsCache:
    """Test _add_to_transaction_ids_cache method."""

    def test_add_trade_to_cache(self, processor):
        """Test adding trade to transaction IDs cache."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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

        assert "trans1" in transaction_processor.TRANSACTION_IDS_CACHE
        assert transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["year"] == "2023"
        assert transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["week"] == "1"
        assert "Manager 1" in transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["managers_involved"]
        assert "Manager 2" in transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["managers_involved"]

    def test_add_add_or_drop_to_cache(self, processor):
        """Test adding add/drop to transaction IDs cache."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)

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

        assert "trans1" in transaction_processor.TRANSACTION_IDS_CACHE
        assert transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["add"] == "Player One"
        assert transaction_processor.TRANSACTION_IDS_CACHE["trans1"]["faab_spent"] == 50

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


class TestRevertAddDropTransaction:
    """Test _revert_add_drop_transaction method - unit tests calling function directly."""

    def test_revert_add_removes_from_cache_and_transaction_ids(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_add_drop_transaction removes add from cache."""
        # Setup cache as if add was processed
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        mock_transaction_ids_cache["trans1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": True,
            "managers_involved": ["Manager 1"],
            "types": ["add"],
            "players_involved": ["Player One"],
            "add": "Player One"
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._weekly_transaction_ids = ["trans1"]

            # Call function directly
            result = processor._revert_add_drop_transaction("trans1", "add")

            # Assert only THIS function's behavior
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 0
            assert "Player One" not in transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["adds"]["players"]
            assert "trans1" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert "trans1" not in processor._weekly_transaction_ids
            assert result is True

    def test_revert_drop_removes_from_cache(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_add_drop_transaction removes drop from cache."""
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player Two"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1

        mock_transaction_ids_cache["trans2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1"],
            "types": ["drop"],
            "players_involved": ["Player Two"],
            "drop": "Player Two"
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._weekly_transaction_ids = ["trans2"]

            result = processor._revert_add_drop_transaction("trans2", "drop")

            assert transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 0
            assert "Player Two" not in transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["drops"]["players"]
            assert "trans2" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert result is True

    def test_revert_add_with_faab_removes_faab_data(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_add_drop_transaction removes FAAB data when reverting add."""
        # Setup add and FAAB data
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["transaction_ids"] = ["trans1"]
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }

        mock_transaction_ids_cache["trans1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": True,
            "managers_involved": ["Manager 1"],
            "types": ["add"],
            "players_involved": ["Player One"],
            "add": "Player One",
            "faab_spent": 50
        }
        
        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._use_faab = True

            processor._weekly_transaction_ids = ["trans1"]

            result = processor._revert_add_drop_transaction("trans1", "add")

            # Assert FAAB data was removed
            assert "Player One" not in transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["faab"]["players"]
            assert "trans1" not in transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["transaction_ids"]
            assert result is True

    def test_revert_partial_transaction_keeps_other_type(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test reverting only add portion of add+drop transaction keeps drop."""
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        mock_transaction_ids_cache["trans1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1"],
            "types": ["add", "drop"],
            "players_involved": ["Player One", "Player Two"],
            "add": "Player One",
            "drop": "Player Two"
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)
        
        
            processor._year = "2023"
            processor._week = "1"
            processor._weekly_transaction_ids = ["trans1"]

            result = processor._revert_add_drop_transaction("trans1", "add")

            # Transaction should still exist (drop remains)
            assert "trans1" in transaction_processor.TRANSACTION_IDS_CACHE
            assert "add" not in transaction_processor.TRANSACTION_IDS_CACHE["trans1"]
            assert "drop" in transaction_processor.TRANSACTION_IDS_CACHE["trans1"]
            assert "trans1" in processor._weekly_transaction_ids
            assert result is False  # Not fully removed

    def test_revert_invalid_type_returns_none(self, mock_transaction_ids_cache):
        """Test _revert_add_drop_transaction returns None for invalid type."""
        mock_transaction_ids_cache["trans1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1"],
            "types": ["add"],
            "players_involved": ["Player One"],
            "add": "Player One"
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            result = processor._revert_add_drop_transaction("trans1", "invalid_type")
            assert result is None

    def test_revert_raises_on_multiple_managers(self, mock_transaction_ids_cache):
        """Test _revert_add_drop_transaction raises error for multiple managers."""
        mock_transaction_ids_cache["trans1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["add"],
            "players_involved": ["Player One"],
            "add": "Player One"
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)
            
            processor._year = "2023"
            processor._week = "1"

            with pytest.raises(Exception, match="Weird add with multiple managers"):
                processor._revert_add_drop_transaction("trans1", "add")


class TestRevertTradeTransaction:
    """Test _revert_trade_transaction method - unit tests calling function directly."""

    def test_revert_simple_trade_removes_both_transactions(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_trade_transaction removes both trades from cache."""

        # Setup cache for both managers - use total=2 since we're removing all trades
        for manager in ["Manager 1", "Manager 2"]:
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 2
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 2
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 2
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }

            # Setup acquired/sent
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "Player One": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

        mock_transaction_ids_cache["trade1"] = {
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
        mock_transaction_ids_cache["trade2"] = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"


            processor._weekly_transaction_ids = ["trade1", "trade2"]

            # Call function directly
            processor._revert_trade_transaction("trade1", "trade2")

            # Assert only THIS function's behavior
            assert "trade1" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert "trade2" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert len(processor._weekly_transaction_ids) == 0
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["trades"]["total"] == 0
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["trades"]["trade_partners"] == {}

    def test_revert_trade_with_faab_removes_faab_data(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_trade_transaction removes FAAB data."""

        # Setup basic trade cache - use 4 total so after decrementing 2, there are still 2 left
        # (if total goes to 0, the code continues and skips FAAB decrement logic)
        for manager in ["Manager 1", "Manager 2"]:
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 4
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 4
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 4
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 2
            }

            # Setup acquired/sent for FAAB
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {
                "$100 FAAB": {"total": 1, "trade_partners": {"Manager 2" if manager == "Manager 1" else "Manager 1": 1}}
            }

        # Setup FAAB cache - the code decrements both traded_away and acquired_from for each manager
        # Set up both fields for both managers
        for manager, partner in [("Manager 1", "Manager 2"), ("Manager 2", "Manager 1")]:
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["total"] = 100
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["traded_away"]["total"] = 100
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

            mock_manager_cache[manager]["summary"]["transactions"]["faab"]["traded_away"]["total"] = 100
            mock_manager_cache[manager]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"] = {partner: 100}
            mock_manager_cache[manager]["summary"]["transactions"]["faab"]["acquired_from"]["total"] = 100
            mock_manager_cache[manager]["summary"]["transactions"]["faab"]["acquired_from"]["trade_partners"] = {partner: 100}

        mock_transaction_ids_cache["trade1"] = {
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
        mock_transaction_ids_cache["trade2"] = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._use_faab = True

            processor._weekly_transaction_ids = ["trade1", "trade2"]

            processor._revert_trade_transaction("trade1", "trade2")

            # Assert FAAB was removed
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["faab"]["traded_away"]["total"] == 0
            assert transaction_processor.MANAGER_CACHE["Manager 2"]["summary"]["transactions"]["faab"]["acquired_from"]["total"] == 0
            assert "Manager 2" not in transaction_processor.MANAGER_CACHE["Manager 1"]["summary"]["transactions"]["faab"]["traded_away"]["trade_partners"]

    def test_revert_trade_removes_from_weekly_transaction_ids(self, mock_manager_cache, mock_transaction_ids_cache):
        """Test _revert_trade_transaction removes IDs from weekly list."""

        # Setup with 3 trades total
        for manager in ["Manager 1", "Manager 2"]:
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 3
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2", "trade3"]
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 3
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 3
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_partners"] = {
                "Manager 2" if manager == "Manager 1" else "Manager 1": 3
            }

            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_acquired"] = {}
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {}
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_acquired"] = {}
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["trade_players_sent"] = {}
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["trade_players_sent"] = {}
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["trade_players_sent"] = {}

        mock_transaction_ids_cache["trade1"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {}
        }
        mock_transaction_ids_cache["trade2"] = {
            "year": "2023",
            "week": "1",
            "commish_action": False,
            "managers_involved": ["Manager 1", "Manager 2"],
            "types": ["trade"],
            "players_involved": [],
            "trade_details": {}
        }

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)
        
            processor._year = "2023"
            processor._week = "1"
            
            processor._weekly_transaction_ids = ["trade1", "trade2", "trade3"]

            processor._revert_trade_transaction("trade1", "trade2")

            # Assert trade3 still exists
            assert "trade3" in transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"]
            assert "trade1" not in processor._weekly_transaction_ids
            assert "trade2" not in processor._weekly_transaction_ids
            assert "trade3" in processor._weekly_transaction_ids


class TestCacheModification:
    """Test that processor correctly modifies caches in-place."""

    def test_processor_modifies_cache_in_place(self, mock_manager_cache):
        """Test that processor modifies the cache that was passed in."""
        original_cache = mock_manager_cache

        with patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache), \
             patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor.set_session_state("2023", "1", {1: "Manager 1"}, True)

            processor._add_add_or_drop_details_to_cache(
                free_agent_type="add",
                manager="Manager 1",
                player_name="Player One",
                transaction_id="trans1",
                commish_action=False
            )

            # Verify cache was modified (same object reference)
            assert transaction_processor.MANAGER_CACHE is original_cache
            assert original_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] == 1


class TestProcessTradeTransaction:
    """Test _process_trade_transaction with actual trade processing."""

    def test_process_simple_two_team_trade(self):
        """Test processing a simple 2-team player swap."""
        from patriot_center_backend.managers import transaction_processor
        processor = transaction_processor.TransactionProcessor(use_faab=True)
        
        processor._year = "2023"
        processor._week = "1"
        processor._use_faab = False
        processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

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
        assert transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1
        assert "trade1" in transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"]

        # Verify Manager 2 acquired player2
        assert transaction_processor.MANAGER_CACHE["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_draft_picks(self, mock_player_ids_cache):
        """Test processing trade that includes draft picks."""
        mock_player_ids_cache = {"player1": {"full_name": "Player One"}}

        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)
        
            processor._year = "2023"
            processor._week = "1"
            processor._use_faab = False
            processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

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
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] == 1

    def test_process_trade_with_faab(self, mock_player_ids_cache):
        """Test processing trade that includes FAAB exchange."""
        mock_player_ids_cache = {"player1": {"full_name": "Player One"}}
        
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._use_faab = True
            processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

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
            assert transaction_processor.MANAGER_CACHE["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["traded_away"]["total"] == 50
            assert transaction_processor.MANAGER_CACHE["Manager 2"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["acquired_from"]["total"] == 50


class TestCommissionerTransactionTypes:
    """Test commissioner transaction type detection in _process_transaction."""

    @patch('patriot_center_backend.managers.transaction_processor.validate_transaction')
    def test_commissioner_add_only(self, mock_validate, mock_player_ids_cache):
        """Test commissioner action with only adds (no drops)."""
        mock_validate.return_value = True
        
        mock_player_ids_cache = {"player1": {"full_name": "Player One"}}
        
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._weekly_roster_ids = {1: "Manager 1"}

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
    def test_commissioner_forced_trade(self, mock_validate, mock_player_ids_cache):
        """Test commissioner action with multiple players (forced trade)."""
        mock_validate.return_value = True
        
        mock_player_ids_cache = {
            "player1": {"full_name": "Player One"},
            "player2": {"full_name": "Player Two"}
        }
        
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)
        
            processor._year = "2023"
            processor._week = "1"
            processor._weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

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

    def test_trade_reversal_same_players_opposite_direction(self, mock_transaction_ids_cache, mock_manager_cache):
        """Test detecting and reverting joke trade (same players swapped back)."""

        # Setup: Two trades with same players, opposite directions
        mock_transaction_ids_cache = {
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

        # Setup cache as if trades were processed
        for manager in ["Manager 1", "Manager 2"]:
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["total"] = 2
            mock_manager_cache[manager]["years"]["2023"]["weeks"]["1"]["transactions"]["trades"]["transaction_ids"] = ["trade1", "trade2"]
            mock_manager_cache[manager]["years"]["2023"]["summary"]["transactions"]["trades"]["total"] = 2
            mock_manager_cache[manager]["summary"]["transactions"]["trades"]["total"] = 2

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache), \
             patch('patriot_center_backend.managers.transaction_processor.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)

            processor._year = "2023"
            processor._week = "1"
            processor._use_faab = False
            
            processor._weekly_transaction_ids = ["trade1", "trade2"]

            # Detect and revert
            processor.check_for_reverse_transactions()

            # Both trades should be removed
            assert "trade1" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert "trade2" not in transaction_processor.TRANSACTION_IDS_CACHE
            assert len(processor._weekly_transaction_ids) == 0

    def test_trade_no_reversal_different_players(self, mock_transaction_ids_cache):
        """Test that different trades don't get reversed."""
        mock_transaction_ids_cache = {
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

        with patch('patriot_center_backend.managers.transaction_processor.TRANSACTION_IDS_CACHE', mock_transaction_ids_cache):
            from patriot_center_backend.managers import transaction_processor
            processor = transaction_processor.TransactionProcessor(use_faab=True)
        
            processor._year = "2023"
            processor._week = "1"
            processor._weekly_transaction_ids = ["trade1", "trade2"]

            processor.check_for_reverse_transactions()

            # Trades should NOT be removed (different players)
            assert "trade1" in transaction_processor.TRANSACTION_IDS_CACHE
            assert "trade2" in transaction_processor.TRANSACTION_IDS_CACHE


class TestProcessAddOrDropTransaction:
    """Test _process_add_or_drop_transaction method."""

    def test_empty_adds_and_drops_prints_warning(self, processor, capsys):
        """Test _process_add_or_drop_transaction handles empty transaction."""
        processor._year = "2023"
        processor._week = "1"

        transaction = {
            "transaction_id": "empty1",
            "adds": {},
            "drops": {}
        }

        processor._process_add_or_drop_transaction(transaction, False)

        # Should print warning and return early
        captured = capsys.readouterr()
        assert "Waiver transaction with no adds or drops" in captured.out

    def test_process_add_with_faab(self):
        """Test _process_add_or_drop_transaction processes add with FAAB."""
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', {"player123": {"full_name": "Player A"}}):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            with patch.object(TransactionProcessor, '_add_faab_details_to_cache') as mock_add_faab, \
                 patch.object(TransactionProcessor, '_add_add_or_drop_details_to_cache') as mock_add_details:
                processor._year = "2023"
                processor._week = "1"
                processor._use_faab = True
                processor._weekly_roster_ids = {1: "Manager 1"}

                transaction = {
                    "transaction_id": "add1",
                    "adds": {"player123": 1},
                    "drops": {},
                    "settings": {"waiver_bid": 50}
                }

                processor._process_add_or_drop_transaction(transaction, False)

                # Should call both add_details and add_faab_details
                mock_add_details.assert_called_once_with("add", "Manager 1", "Player A", "add1", False, 50)
                mock_add_faab.assert_called_once()

    def test_process_add_without_faab(self):
        """Test _process_add_or_drop_transaction processes add without FAAB."""
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', {"player123": {"full_name": "Player A"}}):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            with patch.object(TransactionProcessor, '_add_add_or_drop_details_to_cache') as mock_add_details:
                processor._year = "2023"
                processor._week = "1"
                processor._use_faab = False
                processor._weekly_roster_ids = {1: "Manager 1"}

                transaction = {
                    "transaction_id": "add2",
                    "adds": {"player123": 1},
                    "drops": {}
                }

                processor._process_add_or_drop_transaction(transaction, False)

                # Should only call add_details (no FAAB)
                mock_add_details.assert_called_once_with("add", "Manager 1", "Player A", "add2", False, None)

    def test_process_drop(self):
        """Test _process_add_or_drop_transaction processes drop."""
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', {"player456": {"full_name": "Player B"}}):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            with patch.object(TransactionProcessor, '_add_add_or_drop_details_to_cache') as mock_add_details:
                processor._year = "2023"
                processor._week = "1"
                processor._weekly_roster_ids = {1: "Manager 1"}

                transaction = {
                    "transaction_id": "drop1",
                    "adds": {},
                    "drops": {"player456": 1}
                }

                processor._process_add_or_drop_transaction(transaction, False)

                # Should call add_details for drop
                mock_add_details.assert_called_once_with("drop", "Manager 1", "Player B", "drop1", False)

    def test_process_add_and_drop(self):
        """Test _process_add_or_drop_transaction processes both add and drop."""
        mock_player_ids_cache = {
            "player123": {"full_name": "Player A"},
            "player456": {"full_name": "Player B"}
        }

        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            with patch.object(TransactionProcessor, '_add_faab_details_to_cache') as mock_add_faab, \
                 patch.object(TransactionProcessor, '_add_add_or_drop_details_to_cache') as mock_add_details:
                processor._year = "2023"
                processor._week = "1"
                processor._use_faab = True
                processor._weekly_roster_ids = {1: "Manager 1"}

                transaction = {
                    "transaction_id": "add_drop1",
                    "adds": {"player123": 1},
                    "drops": {"player456": 1},
                    "settings": {"waiver_bid": 30}
                }

                processor._process_add_or_drop_transaction(transaction, False)

                # Should call add_details twice (once for add, once for drop)
                assert mock_add_details.call_count == 2
                # Should call add_faab once for the add
                mock_add_faab.assert_called_once()

    def test_process_commissioner_action(self):
        """Test _process_add_or_drop_transaction handles commissioner action flag."""
        with patch('patriot_center_backend.managers.transaction_processor.PLAYER_IDS_CACHE', {"player123": {"full_name": "Player A"}}):
            from patriot_center_backend.managers.transaction_processor import TransactionProcessor
            processor = TransactionProcessor(use_faab=True)

            with patch.object(TransactionProcessor, '_add_add_or_drop_details_to_cache') as mock_add_details:
                processor._year = "2023"
                processor._week = "1"
                processor._weekly_roster_ids = {1: "Manager 1"}

                transaction = {
                    "transaction_id": "commish_add",
                    "adds": {"player123": 1},
                    "drops": {}
                }

                processor._process_add_or_drop_transaction(transaction, True)

                # Should pass commish_action=True
                mock_add_details.assert_called_once_with("add", "Manager 1", "Player A", "commish_add", True, None)
