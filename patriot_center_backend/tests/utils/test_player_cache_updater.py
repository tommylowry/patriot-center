
from copy import deepcopy
from unittest.mock import patch

import pytest

from patriot_center_backend.utils.player_cache_updater import update_players_cache


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

    def test_update_with_matchup_list(self):
        """Test updating cache with list of matchup data."""
        self.mock_player_ids_cache.update({
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            },
            "5678": {
                "full_name": "Travis Kelce",
                "first_name": "Travis",
                "last_name": "Kelce",
                "position": "TE",
                "team": "KC"
            },
            "9999": {
                "full_name": "Test Player",
                "first_name": "Test",
                "last_name": "Player",
                "position": "WR",
                "team": "TEST"
            }
        })

        item = [
            {"players": ["4046", "5678"]},
            {"players": ["9999"]}
        ]
        update_players_cache(item)

        assert len(self.mock_players_cache) == 3
        assert "Patrick Mahomes" in self.mock_players_cache
        assert "Travis Kelce" in self.mock_players_cache
        assert "Test Player" in self.mock_players_cache
    
    def test_player_not_in_player_ids(self, capsys):
        """Test handling player ID not in player_ids dict."""
        item = "9999"
        update_players_cache(item)

        # Verify warning was printed for player not in player_ids
        captured = capsys.readouterr()
        assert "player_id 9999 not found" in captured.out

        # Should handle gracefully - player won't be added since no metadata
        assert len(self.mock_players_cache) == 0

    def test_update_with_none_raises_error(self):
        """Test that None item raises ValueError."""
        item = None

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item)

    def test_update_with_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        item = ""

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item)

    def test_update_with_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        item = []

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item)

    def test_update_with_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        item = 12345  # Integer instead of string or list

        with pytest.raises(ValueError, match="Either matchups or player_id must be provided"):
            update_players_cache(item)