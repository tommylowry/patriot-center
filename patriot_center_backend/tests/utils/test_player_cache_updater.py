"""Unit tests for player_cache_updater module."""

from copy import deepcopy
from unittest.mock import call, patch

import pytest

from patriot_center_backend.utils.player_cache_updater import (
    update_players_cache,
    update_players_cache_with_list,
)


class TestUpdatePlayersCache:
    """Test update_players_cache function.

    This class contains unit tests for the update_players_cache function.

    The tests cover the following scenarios:

    - Test updating cache with single player ID.
    - Test updating cache with apostrophe in player name.
    - Test handling player already in cache.
    - Test handling player not in player_ids cache.
    - Test handling player not in player_ids cache with None input.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        This fixture sets up the following mocks:

        - mock_get_player_ids_cache: a mock of CACHE_MANAGER.get_player_ids_cache
        - mock_get_players_cache: a mock of CACHE_MANAGER.get_players_cache

        :return: None
        """
        with patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_player_ids_cache') as mock_get_player_ids_cache, \
             patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_players_cache') as mock_get_players_cache:
            
            self.mock_player_ids_cache = {}
            self.mock_players_cache = {}

            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache
            mock_get_players_cache.return_value = self.mock_players_cache
            
            yield

    def test_update_with_single_player_id(self):
        """Test updating cache with single player ID.

        This test ensures that update_players_cache function correctly updates the cache
        with a single player ID.

        The function should add the player to the cache and set the "slug"
        attribute to the URL slug of the player name.

        :param self: The test class instance.
        :return: None
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
        """Test updating cache with apostrophe in player name.

        This test ensures that update_players_cache function correctly handles
        players with apostrophes in their name.

        :param self: The test class instance.
        :return: None
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
        """Test handling player already in cache.

        This test ensures that update_players_cache function does not modify the cache
        if the player is already present in the cache.

        The function should not modify the cache if the player is already present.

        :param self: The test class instance.
        :return: None
        """
        # Initialize the cache with a sample player
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
        """Test handling player not in player_ids cache.

        This test ensures that update_players_cache function does not add the player to the cache
        if the player is not present in the player_ids cache.

        The function should handle this gracefully and not modify the cache if the player is not present.

        :param self: The test class instance.
        :param capsys: The pytest capsys fixture.
        :return: None
        """
        item = "9999"
        update_players_cache(item)

        # Verify warning was printed for player not in player_ids
        captured = capsys.readouterr()
        assert "player_id 9999 not found" in captured.out

        # Should handle gracefully - player won't be added since no metadata
        assert len(self.mock_players_cache) == 0

    def test_update_with_none_raises_error(self, capsys):
        """Test handling player not in player_ids cache with None input.

        This test ensures that update_players_cache function does not add the player to the cache
        if the player is not present in the player_ids cache and input is None.

        The function should handle this gracefully and not modify the cache if the player is not present.

        :param self: The test class instance.
        :param capsys: The pytest capsys fixture.
        :return: None
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

        This fixture sets up the following mocks:

        - mock_update_players: a mock of update_players_cache function

        :return: None
        """
        with patch('patriot_center_backend.utils.player_cache_updater.update_players_cache') as mock_update_players:
            
            self.mock_update_players = mock_update_players
            
            yield

    def test_update_with_valid_matchup(self):
        """
        Test updating cache with valid list of matchup data.

        This test ensures that update_players_cache_with_list function updates the cache
        with valid list of matchup data.

        The test checks that the function calls update_players_cache with the correct
        player IDs.

        :return: None
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
        Test that update_players_cache_with_list function updates the cache with valid list of matchup data.

        This test ensures that update_players_cache_with_list function updates the cache
        with valid list of matchup data. The function takes a list of dictionaries
        where each dictionary has a "players" key with a value of a list of strings.

        The test checks that the function calls update_players_cache with the correct
        player IDs.

        :return: None
        """
        item = [{"players": [123]}]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with(123)

    def test_update_ignores_non_dict_types(self):
        """
        Test that update_players_cache_with_list ignores non-dictionary types in list.

        This test ensures that update_players_cache_with_list ignores any non-dictionary
        types in the list of matchup data that is passed to it.

        The test checks that the function calls update_players_cache with the correct
        player IDs.

        :return: None
        """
        item = [{"players": ["4046"]}, "invalid type in list"]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with("4046")

    def test_warns_with_invalid_item(self, capsys):
        """
        Test that update_players_cache_with_list raises a warning when passed an invalid item.

        This test ensures that update_players_cache_with_list raises a warning when passed
        an invalid item. The function is expected to raise a warning when the item is
        not a list.

        :return: None
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
        Test updating cache list with invalid type in item.

        This test ensures that update_players_cache_with_list raises a warning when passed
        an item with an invalid type (i.e. not a dictionary).

        The test checks that the function calls update_players_cache with the correct player IDs
        and that the function raises a warning when the item is not a dictionary.

        :return: None
        """
        item = ["invalid type in list"]
        update_players_cache_with_list(item)

        # Verify warning prints
        captured = capsys.readouterr()
        assert "did not have a matchup dict with players" in captured.out, "Warning should be printed when item is not a dictionary"

        # Verify update_players_cache was not called
        self.mock_update_players.assert_not_called, "update_players_cache should not be called when item is not a dictionary"
