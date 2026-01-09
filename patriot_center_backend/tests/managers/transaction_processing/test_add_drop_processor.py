from unittest.mock import patch

import pytest

from patriot_center_backend.managers.transaction_processing.add_drop_processor import (
    add_add_or_drop_details_to_cache,
    process_add_or_drop_transaction,
    revert_add_drop_transaction,
)


class TestAddAddOrDropDetailsToCache:
    """Test add_add_or_drop_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_to_transaction_ids'):
            
            self.mock_manager_cache = mock_manager_cache

            mock_get_manager.return_value = self.mock_manager_cache
            
            yield

    def test_add_add_details_updates_cache(self):
        """Test that add details are added to cache at all levels."""
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
        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]
        assert weekly["players"]["Player One"] == 1

    def test_add_drop_details_updates_cache(self):
        """Test that drop details are added to cache at all levels."""
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
        weekly = self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]
        assert weekly["total"] == 1
        assert "Player One" in weekly["players"]

    def test_add_add_or_drop_invalid_type(self):
        """Test that invalid type is handled gracefully."""
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


class TestRevertAddDropTransaction:
    """Test revert_add_drop_transaction method - unit tests calling function directly."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_transaction_ids_cache') as mock_get_ids:
            
            self.mock_manager_cache = mock_manager_cache
            self.mock_transaction_ids_cache = {
                "trans1":
                {
                    "year": "2023",
                    "week": "1",
                    "commish_action": True
                }
            }
            self.weekly_transaction_ids = ["trans1"]
            
            mock_get_ids.return_value = self.mock_transaction_ids_cache
            mock_get_manager.return_value = self.mock_manager_cache
            
            yield
    
    def test_revert_add_removes_from_cache_and_transaction_ids(self):
        """Test revert_add_drop_transaction removes add from cache."""
        # Setup cache as if add was processed
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        
        self.mock_transaction_ids_cache["trans1"].update(
            {
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            }
        )

        # Call function directly
        result = revert_add_drop_transaction(
            transaction_id="trans1",
            transaction_type="add",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Assert only THIS function's behavior
        assert self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] == 0
        assert "Player One" not in self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]
        assert "trans1" not in self.mock_transaction_ids_cache
        assert "trans1" not in self.weekly_transaction_ids
        assert result is True

    def test_revert_drop_removes_from_cache(self):
        """Test revert_add_drop_transaction removes drop from cache."""
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["drops"]["players"]["Player Two"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]["Player Two"] = 1

        self.mock_transaction_ids_cache["trans1"].update(
            {
                "commish_action": False,
                "managers_involved": ["Manager 1"],
                "types": ["drop"],
                "players_involved": ["Player Two"],
                "drop": "Player Two"
            }
        )

        result = revert_add_drop_transaction(
            transaction_id="trans1",
            transaction_type="drop",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        assert self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["total"] == 0
        assert "Player Two" not in self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["drops"]["players"]
        assert "trans1" not in self.mock_transaction_ids_cache
        assert result is True

    def test_revert_add_with_faab_removes_faab_data(self):
        """Test revert_add_drop_transaction removes FAAB data when reverting add."""
        # Setup add and FAAB data
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["transaction_ids"] = ["trans1"]
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"]["players"]["Player One"] = {
            "num_bids_won": 1, "total_faab_spent": 50
        }

        self.mock_transaction_ids_cache["trans1"].update(
            {
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One",
                "faab_spent": 50
            }
        )

        result = revert_add_drop_transaction(
            transaction_id="trans1",
            transaction_type="add",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Assert FAAB data was removed
        assert "Player One" not in self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["faab"]["players"]
        assert "trans1" not in self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["faab"]["transaction_ids"]
        assert result is True

    def test_revert_partial_transaction_keeps_other_type(self):
        """Test reverting only add portion of add+drop transaction keeps drop."""
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["total"] = 1
        self.mock_manager_cache["Manager 1"]["summary"]["transactions"]["adds"]["players"]["Player One"] = 1

        self.mock_transaction_ids_cache["trans1"].update(
            {
                "managers_involved": ["Manager 1"],
                "types": ["add", "drop"],
                "players_involved": ["Player One", "Player Two"],
                "add": "Player One",
                "drop": "Player Two"
            }
        )

        result = revert_add_drop_transaction(
            transaction_id="trans1",
            transaction_type="add",
            weekly_transaction_ids=self.weekly_transaction_ids
        )

        # Transaction should still exist (drop remains)
        assert "trans1" in self.mock_transaction_ids_cache
        assert "add" not in self.mock_transaction_ids_cache["trans1"]
        assert "drop" in self.mock_transaction_ids_cache["trans1"]
        assert "trans1" in self.weekly_transaction_ids
        assert result is False  # Not fully removed
    
    def test_revert_invalid_type_returns_none(self):
        """Test revert_add_drop_transaction returns None for invalid type."""
        self.mock_transaction_ids_cache["trans1"].update(
            {
                "managers_involved": ["Manager 1"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            }
        )

        result = revert_add_drop_transaction(
            transaction_id="trans1",
            transaction_type="invalid_type",
            weekly_transaction_ids=[]
        )
        
        assert result is None

    def test_revert_raises_on_multiple_managers(self):
        """Test revert_add_drop_transaction raises error for multiple managers."""
        self.mock_transaction_ids_cache["trans1"].update(
            {
                "managers_involved": ["Manager 1", "Manager 2"],
                "types": ["add"],
                "players_involved": ["Player One"],
                "add": "Player One"
            }
        )

        with pytest.raises(Exception, match="Weird add with multiple managers"):
            revert_add_drop_transaction("trans1", "add", self.weekly_transaction_ids)


class TestProcessAddOrDropTransaction:
    """Test process_add_or_drop_transaction method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.update_players_cache'), \
             patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_add_or_drop_details_to_cache') as mock_add_details, \
             patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.add_faab_details_to_cache') as mock_add_faab, \
             patch('patriot_center_backend.managers.transaction_processing.add_drop_processor.CACHE_MANAGER.get_player_ids_cache') as mock_get_player_ids:
            
            self.mock_add_details = mock_add_details
            self.mock_add_faab = mock_add_faab

            self.mock_player_ids_cache = {}

            mock_get_player_ids.return_value = self.mock_player_ids_cache
            
            yield

    def test_empty_adds_and_drops_prints_warning(self, capsys):
        """Test process_add_or_drop_transaction handles empty transaction."""
        transaction = {
            "transaction_id": "empty1",
            "adds": {},
            "drops": {}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=True
        )

        # Should print warning and return early
        captured = capsys.readouterr()
        assert "Waiver transaction with no adds or drops" in captured.out

    def test_process_add_with_faab(self):
        """Test process_add_or_drop_transaction processes add with FAAB."""
        self.mock_player_ids_cache["player123"] = {"full_name": "Player A"}

        transaction = {
            "transaction_id": "add1",
            "adds": {"player123": 1},
            "drops": {},
            "settings": {"waiver_bid": 50}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=True
        )

        # Should call both add_details and add_faab_details
        self.mock_add_details.assert_called_once_with("2023", "1", [], "add", "Manager 1", "Player A", "add1", False, True, 50)
        self.mock_add_faab.assert_called_once()

    def test_process_add_without_faab(self):
        """Test process_add_or_drop_transaction processes add without FAAB."""
        self.mock_player_ids_cache["player123"] = {"full_name": "Player A"}

        transaction = {
            "transaction_id": "add2",
            "adds": {"player123": 1},
            "drops": {}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=False
        )

        # Should only call add_details (no FAAB)
        self.mock_add_details.assert_called_once_with("2023", "1", [], "add", "Manager 1", "Player A", "add2", False, False, None)
        assert not self.mock_add_faab.called

    def test_process_drop(self):
        """Test process_add_or_drop_transaction processes drop."""
        self.mock_player_ids_cache["player456"] = {"full_name": "Player B"}

        transaction = {
            "transaction_id": "drop1",
            "adds": {},
            "drops": {"player456": 1}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=True
        )

        # Should call add_details for drop
        self.mock_add_details.assert_called_once_with("2023", "1", [], "drop", "Manager 1", "Player B", "drop1", False, True)
        assert not self.mock_add_faab.called

    def test_process_add_and_drop(self):
        """Test process_add_or_drop_transaction processes both add and drop."""
        self.mock_player_ids_cache["player123"] = {"full_name": "Player A"}
        self.mock_player_ids_cache["player456"] = {"full_name": "Player B"}

        transaction = {
            "transaction_id": "add_drop1",
            "adds": {"player123": 1},
            "drops": {"player456": 1},
            "settings": {"waiver_bid": 30}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=False,
            use_faab=True
        )

        # Should call add_details twice (once for add, once for drop)
        assert self.mock_add_details.call_count == 2
        # Should call add_faab once for the add
        self.mock_add_faab.assert_called_once()

    def test_process_commissioner_action(self):
        """Test process_add_or_drop_transaction handles commissioner action flag."""
        self.mock_player_ids_cache["player123"] = {"full_name": "Player A"}

        transaction = {
            "transaction_id": "commish_add",
            "adds": {"player123": 1},
            "drops": {}
        }
        process_add_or_drop_transaction(
            year="2023",
            week="1",
            transaction=transaction,
            roster_ids={1: "Manager 1"},
            weekly_transaction_ids=[],
            commish_action=True,
            use_faab=True
        )

        # Should pass commish_action=True
        self.mock_add_details.assert_called_once_with("2023", "1", [], "add", "Manager 1", "Player A", "commish_add", True, True, None)