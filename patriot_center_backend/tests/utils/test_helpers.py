"""
Unit tests for utils/helpers.py - Player ID and name lookup utilities.
"""
import pytest
from unittest.mock import patch


class TestGetPlayerId:
    """Test get_player_id function."""

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_player_id_when_name_matches(self, mock_cache):
        """Test returns correct player ID when name is found."""
        from patriot_center_backend.utils.helpers import get_player_id

        mock_cache.items.return_value = [
            ("123", {"full_name": "Josh Allen", "position": "QB"}),
            ("456", {"full_name": "Patrick Mahomes", "position": "QB"}),
            ("789", {"full_name": "Saquon Barkley", "position": "RB"})
        ]

        result = get_player_id("Josh Allen")
        assert result == "123"

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_none_when_name_not_found(self, mock_cache):
        """Test returns None when player name is not found."""
        from patriot_center_backend.utils.helpers import get_player_id

        mock_cache.items.return_value = [
            ("123", {"full_name": "Josh Allen", "position": "QB"}),
            ("456", {"full_name": "Patrick Mahomes", "position": "QB"})
        ]

        result = get_player_id("Unknown Player")
        assert result is None

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_case_sensitive_matching(self, mock_cache):
        """Test that name matching is case-sensitive."""
        from patriot_center_backend.utils.helpers import get_player_id

        mock_cache.items.return_value = [
            ("123", {"full_name": "Josh Allen", "position": "QB"})
        ]

        # Exact match should work
        assert get_player_id("Josh Allen") == "123"

        # Different case should not match
        assert get_player_id("josh allen") is None
        assert get_player_id("JOSH ALLEN") is None

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_exact_name_matching(self, mock_cache):
        """Test that partial names don't match."""
        from patriot_center_backend.utils.helpers import get_player_id

        mock_cache.items.return_value = [
            ("123", {"full_name": "Josh Allen", "position": "QB"})
        ]

        # Partial name should not match
        assert get_player_id("Josh") is None
        assert get_player_id("Allen") is None

        # Only exact match should work
        assert get_player_id("Josh Allen") == "123"

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_first_match_when_duplicates(self, mock_cache):
        """Test returns first player ID when multiple players have same name."""
        from patriot_center_backend.utils.helpers import get_player_id

        # Hypothetical scenario where two players have the same name
        mock_cache.items.return_value = [
            ("123", {"full_name": "Mike Williams", "position": "WR"}),
            ("456", {"full_name": "Mike Williams", "position": "WR"}),
        ]

        result = get_player_id("Mike Williams")
        assert result == "123"  # Returns first match

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_handles_empty_cache(self, mock_cache):
        """Test handles empty player IDs cache."""
        from patriot_center_backend.utils.helpers import get_player_id

        mock_cache.items.return_value = []

        result = get_player_id("Any Player")
        assert result is None


class TestGetPlayerName:
    """Test get_player_name function."""

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_player_name_when_id_exists(self, mock_cache):
        """Test returns correct player name when ID is found."""
        from patriot_center_backend.utils.helpers import get_player_name

        mock_cache.get.return_value = {
            "full_name": "Josh Allen",
            "position": "QB"
        }

        result = get_player_name("123")
        assert result == "Josh Allen"

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_none_when_id_not_found(self, mock_cache):
        """Test returns None when player ID is not found."""
        from patriot_center_backend.utils.helpers import get_player_name

        mock_cache.get.return_value = None

        result = get_player_name("999")
        assert result is None

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_returns_none_when_full_name_missing(self, mock_cache):
        """Test returns None when player info exists but full_name is missing."""
        from patriot_center_backend.utils.helpers import get_player_name

        # Player info exists but no full_name field
        mock_cache.get.return_value = {
            "position": "QB"
        }

        result = get_player_name("123")
        assert result is None

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_handles_numeric_and_string_ids(self, mock_cache):
        """Test handles both numeric and string player IDs."""
        from patriot_center_backend.utils.helpers import get_player_name

        mock_cache.get.return_value = {
            "full_name": "Josh Allen",
            "position": "QB"
        }

        # String ID
        result = get_player_name("123")
        assert result == "Josh Allen"

        # The function should work with whatever is passed
        mock_cache.get.assert_called_with("123")

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_handles_defense_ids(self, mock_cache):
        """Test handles defense IDs (team abbreviations)."""
        from patriot_center_backend.utils.helpers import get_player_name

        mock_cache.get.return_value = {
            "full_name": "New England Patriots",
            "position": "DEF"
        }

        result = get_player_name("NE")
        assert result == "New England Patriots"


class TestHelperFunctionsIntegration:
    """Integration tests for get_player_id and get_player_name working together."""

    @patch('patriot_center_backend.utils.helpers.PLAYER_IDS_CACHE')
    def test_round_trip_id_to_name_to_id(self, mock_cache):
        """Test that converting ID->Name->ID works correctly."""
        from patriot_center_backend.utils.helpers import get_player_id, get_player_name

        # Setup cache
        mock_player_data = {
            "123": {"full_name": "Josh Allen", "position": "QB"},
            "456": {"full_name": "Patrick Mahomes", "position": "QB"}
        }

        # Mock for get_player_name
        mock_cache.get.side_effect = lambda key: mock_player_data.get(key)

        # Mock for get_player_id
        mock_cache.items.return_value = mock_player_data.items()

        # Start with ID, get name, then get ID back
        name = get_player_name("123")
        assert name == "Josh Allen"

        player_id = get_player_id(name)
        assert player_id == "123"
