
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
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_player_ids_cache') as mock_get_player_ids_cache, \
             patch('patriot_center_backend.utils.player_cache_updater.CACHE_MANAGER.get_players_cache') as mock_get_players_cache:
            
            self.mock_player_ids_cache = {}
            self.mock_players_cache = {}

            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache
            mock_get_players_cache.return_value = self.mock_players_cache
            
            yield

    def test_update_with_single_player_id(self):
        """Test updating cache with single player ID."""
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

        assert "Patrick Mahomes" in self.mock_players_cache
        assert self.mock_players_cache["Patrick Mahomes"]["player_id"] == "4046"
        assert self.mock_players_cache["Patrick Mahomes"]["position"] == "QB"
        assert self.mock_players_cache["Patrick Mahomes"]["slug"] == "patrick%20mahomes"

    def test_update_with_apostrophe_in_name(self):
        """Test URL slug creation with apostrophe in name."""
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

        assert "D'Andre Swift" in self.mock_players_cache
        assert self.mock_players_cache["D'Andre Swift"]["slug"] == "d%27andre%20swift"

    def test_player_already_in_cache(self):
        """Test that player already in cache is not re-added."""
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

        original_cache = deepcopy(self.mock_players_cache)
            
        item = "4046"
        update_players_cache(item)

        # Cache should remain unchanged
        assert self.mock_players_cache == original_cache
    
    def test_player_not_in_player_ids(self, capsys):
        """Test handling player ID not in player_ids dict."""
        item = "9999"
        update_players_cache(item)

        # Verify warning was printed for player not in player_ids
        captured = capsys.readouterr()
        assert "player_id 9999 not found" in captured.out

        # Should handle gracefully - player won't be added since no metadata
        assert len(self.mock_players_cache) == 0

    def test_update_with_none_raises_error(self, capsys):
        """Test that None item raises ValueError."""
        item = None
        update_players_cache(item)

        captured = capsys.readouterr()
        assert "player_id None not found" in captured.out


class TestUpdatePlayersCacheWithList:
    """Test update_players_cache_with_list function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.utils.player_cache_updater.update_players_cache') as mock_update_players:
            
            self.mock_update_players = mock_update_players
            
            yield

    def test_update_with_valid_matchup(self):
        """Test updating cache with valid list of matchup data."""
        item = [
            {"players": ["4046", "5678"]},
            {"players": ["9999"]}
        ]
        update_players_cache_with_list(item)

        calls = self.mock_update_players.call_args_list
        assert call("4046") in calls
        assert call("5678") in calls
        assert call("9999") in calls

    def test_update_with_list_passes_any_type(self):
        """Test updating cache with valid list of matchup data."""
        item = [{"players": [123]}]
        update_players_cache_with_list(item)

        self.mock_update_players.assert_called_once_with(123)

    def test_update_ignores_non_dict_types(self):
        """Test updating cache list with invalid type in item."""
        item = [{"players": ["4046"]}, "invalid type in list"]
        update_players_cache_with_list(item)

        self.mock_update_players.assert_called_once_with("4046")

    def test_warns_with_invalid_item(self, capsys):
        """Test updating cache list with invalid item type."""
        item = "invalid input type"
        update_players_cache_with_list(item)

        # verify warning prints
        captured = capsys.readouterr()
        assert "is not a list" in captured.out

        self.mock_update_players.assert_not_called
    
    def test_warns_when_update_not_called(self, capsys):
        """Test updating cache list with invalid type in item."""
        item = ["invalid type in list"]
        update_players_cache_with_list(item)

        # verify warning prints
        captured = capsys.readouterr()
        assert "did not have a matchup dict with players" in captured.out

        self.mock_update_players.assert_not_called