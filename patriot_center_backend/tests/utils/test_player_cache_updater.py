"""Unit tests for player_cache_updater module."""

from copy import deepcopy
from unittest.mock import call, patch

import pytest

from patriot_center_backend.utils.player_cache_updater import (
    update_players_cache,
    update_players_cache_with_list,
)


class TestUpdatePlayersCache:
    """Test update_players_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        Patches CACHE_MANAGER.get_player_ids_cache and CACHE_MANAGER.get_players_cache
        to return mock objects.
        """
        with patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_player_ids_cache') as mock_get_player_ids_cache, \
             patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_players_cache') as mock_get_players_cache:
            
            self.mock_player_ids_cache = {}
            self.mock_players_cache = {}

            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache
            mock_get_players_cache.return_value = self.mock_players_cache
            
            yield

    def test_update_with_single_player_id(self):
        """
        Test update_players_cache with a single player_id.

        Updates the players cache by adding a new player if the player_id is present in the player_ids cache.
        """
        self.mock_player_ids_cache.update({
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        })
            
        item = "4046"
        update_players_cache(item)

        # Check that the player is in the cache
        assert "Patrick Mahomes" in self.mock_players_cache
        
        # Check that the player_id attribute is set correctly
        assert self.mock_players_cache["Patrick Mahomes"]["player_id"] == "4046"
        
        # Check that the position attribute is set correctly
        assert self.mock_players_cache["Patrick Mahomes"]["position"] == "QB"
        
        # Check that the slug attribute is set correctly
        assert self.mock_players_cache["Patrick Mahomes"]["slug"] == "patrick%20mahomes"
        

    def test_update_with_apostrophe_in_name(self):
        """
        Test update_players_cache with a player_id that has an apostrophe in their name.

        Updates the players cache by adding a new player if the player_id is present in the player_ids cache.

        Checks that the player is in the cache, and that the slug attribute is set correctly.
        """
        self.mock_player_ids_cache.update({
            "5678": {
                "full_name": "D'Andre Swift",
                "first_name": "D'Andre",
                "last_name": "Swift",
                "position": "RB",
                "team": "PHI"
            }
        })
            
        item = "5678"
        update_players_cache(item)

        # Check that the player is in the cache
        assert "D'Andre Swift" in self.mock_players_cache
        
        # Check that the slug attribute is set correctly
        assert self.mock_players_cache["D'Andre Swift"]["slug"] == "d%27andre%20swift"

    def test_player_already_in_cache(self):
        """
        Test that update_players_cache doesn't modify the cache if a player_id is already in the cache.

        Initializes the cache with a sample player, creates a deep copy of the original cache, and then calls update_players_cache with the player_id.

        Asserts that the cache remains unchanged after the call to update_players_cache.
        """
        self.mock_players_cache.update({
            "Patrick Mahomes": {
                "player_id": "4046",
                "position": "QB",
                "slug": "patrick%20mahomes"
            }
        })
        self.mock_player_ids_cache.update({
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        })

        # Create a deep copy of the original cache
        original_cache = deepcopy(self.mock_players_cache)
            
        item = "4046"
        update_players_cache(item)

        # Cache should remain unchanged
        assert self.mock_players_cache == original_cache
    
    def test_player_not_in_player_ids(self, capsys):
        """
        Test that update_players_cache prints a warning when the player_id is not in the player_ids cache.

        Asserts that the cache remains unchanged after the call to update_players_cache.
        """
        item = "9999"
        update_players_cache(item)

        # Verify warning was printed for player not in player_ids
        captured = capsys.readouterr()
        assert "player_id 9999 not found" in captured.out

        # Should handle gracefully - player won't be added since no metadata
        assert len(self.mock_players_cache) == 0

    def test_update_with_none_raises_error(self, capsys):
        """
        Test that update_players_cache prints a warning when given None as the player_id.

        Asserts that the warning "player_id None not found" is printed.
        """
        item = None
        update_players_cache(item)

        # Verify warning was printed for player not in player_ids
        captured = capsys.readouterr()
        assert "player_id None not found" in captured.out


class TestUpdatePlayersCacheWithList:
    """Test update_players_cache_with_list function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        Patches update_players_cache to return a mock object.
        """
        with patch('patriot_center_backend.utils.player_cache_updater.update_players_cache') as mock_update_players:
            
            self.mock_update_players = mock_update_players
            
            yield

    def test_update_with_valid_matchup(self):
        """
        Test that update_players_cache_with_list updates the players cache correctly with valid matchups.

        Asserts that the correct player IDs were passed to update_players_cache.
        """
        item = [
            {"players": ["4046", "5678"]},
            {"players": ["9999"]}
        ]
        update_players_cache_with_list(item)

        # Verify that the correct player IDs were passed to update_players_cache
        calls = self.mock_update_players.call_args_list
        assert call("4046") in calls, "4046 not found in calls"
        assert call("5678") in calls, "5678 not found in calls"
        assert call("9999") in calls, "9999 not found in calls"

    def test_update_with_list_passes_any_type(self):
        """
        Test that update_players_cache_with_list updates the players cache correctly when given a list with any type.

        Asserts that the correct player IDs were passed to update_players_cache.
        """
        item = [{"players": [123]}]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with(123)

    def test_update_ignores_non_dict_types(self):
        """
        Test that update_players_cache_with_list ignores non-dict types in the input list.

        Asserts that the correct player IDs were passed to update_players_cache.
        """
        item = [{"players": ["4046"]}, "invalid type in list"]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with("4046")

    def test_warns_with_invalid_item(self, capsys):
        """
        Test that update_players_cache_with_list warns and does not call update_players_cache when given an invalid item type.

        Asserts that the correct warning is printed when item is not a list and that update_players_cache is not called.
        """
        item = "invalid input type"
        update_players_cache_with_list(item)

        # Verify warning prints
        captured = capsys.readouterr()
        assert "is not a list" in captured.out, "Warning should be printed when item is not a list"

        # Verify update_players_cache was not called
        self.mock_update_players.assert_not_called, "update_players_cache should not be called when item is not a list"
    
    def test_warns_when_update_not_called(self, capsys):
        """
        Test that update_players_cache_with_list warns and does not call update_players_cache when given a list that does not contain a matchup dict with players.

        Asserts that the correct warning is printed when item does not contain a matchup dict with players and that update_players_cache is not called.
        """
        item = ["invalid type in list"]
        update_players_cache_with_list(item)

        # Verify warning prints
        captured = capsys.readouterr()
        assert "did not have a matchup dict with players" in captured.out, "Warning should be printed when item is not a dictionary"

        # Verify update_players_cache was not called
        self.mock_update_players.assert_not_called, "update_players_cache should not be called when item is not a dictionary"
