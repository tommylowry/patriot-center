"""
Unit tests for utilities module.

Tests utility functions with both good and bad scenarios.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from copy import deepcopy
from patriot_center_backend.managers.utilities import (
    draft_pick_decipher,
    extract_dict_data,
    get_image_url,
    get_current_manager_image_url,
    update_players_cache
)


class TestDraftPickDecipher:
    """Test draft_pick_decipher function."""

    def test_valid_draft_pick(self):
        """Test with valid draft pick dictionary."""
        draft_pick_dict = {
            "season": "2023",
            "round": 3,
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's 2023 Round 3 Draft Pick"

    def test_first_round_pick(self):
        """Test with first round pick."""
        draft_pick_dict = {
            "season": "2024",
            "round": 1,
            "roster_id": 5,
            "previous_owner_id": 5,
            "owner_id": 3
        }
        weekly_roster_ids = {3: "Manager 3", 5: "Manager 5"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 5's 2024 Round 1 Draft Pick"

    def test_unknown_roster_id(self):
        """Test with roster_id not in weekly_roster_ids."""
        draft_pick_dict = {
            "season": "2023",
            "round": 2,
            "roster_id": 999,
            "previous_owner_id": 1,
            "owner_id": 2
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "unknown_manager's 2023 Round 2 Draft Pick"

    def test_missing_season(self):
        """Test with missing season - should use 'unknown_year'."""
        draft_pick_dict = {
            "round": 2,
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's unknown_year Round 2 Draft Pick"

    def test_missing_round(self):
        """Test with missing round - should use 'unknown_round'."""
        draft_pick_dict = {
            "season": "2023",
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's 2023 Round unknown_round Draft Pick"

    def test_missing_roster_id(self):
        """Test with missing roster_id - should use 'unknown_team'."""
        draft_pick_dict = {
            "season": "2023",
            "round": 2,
            "previous_owner_id": 1,
            "owner_id": 2
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "unknown_manager's 2023 Round 2 Draft Pick"


class TestExtractDictData:
    """Test extract_dict_data function."""

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_top_3_simple_dict(self, mock_get_image_url):
        """Test with simple dictionary (no nested totals)."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": 10,
            "Player B": 8,
            "Player C": 6,
            "Player D": 4
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(data, players_cache, player_ids, image_urls_cache, cache)

        assert len(result) == 3
        assert result[0]["name"] == "Player A"
        assert result[0]["count"] == 10
        assert result[1]["name"] == "Player B"
        assert result[1]["count"] == 8
        assert result[2]["name"] == "Player C"
        assert result[2]["count"] == 6

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_top_3_with_nested_totals(self, mock_get_image_url):
        """Test with nested dictionary containing 'total' keys."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": {"total": 10, "other": "data"},
            "Player B": {"total": 8, "other": "data"},
            "Player C": {"total": 6, "other": "data"},
            "Player D": {"total": 4, "other": "data"}
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(data, players_cache, player_ids, image_urls_cache, cache)

        assert len(result) == 3
        assert result[0]["name"] == "Player A"
        assert result[0]["count"] == 10

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_no_cutoff(self, mock_get_image_url):
        """Test with cutoff=0 to include all items."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": 10,
            "Player B": 8,
            "Player C": 6,
            "Player D": 4
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(data, players_cache, player_ids, image_urls_cache, cache, cutoff=0)

        assert len(result) == 4

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_ties_at_cutoff(self, mock_get_image_url):
        """Test tie-breaking logic when items are tied at cutoff position."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": 10,
            "Player B": 8,
            "Player C": 6,
            "Player D": 6,  # Tied with Player C
            "Player E": 6,  # Tied with Player C and D
            "Player F": 4
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(data, players_cache, player_ids, image_urls_cache, cache, cutoff=3)

        # Should include all tied items at position 3
        assert len(result) == 5  # A, B, C, D, E all included

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_custom_key_value_names(self, mock_get_image_url):
        """Test with custom key_name and value_name."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": 10,
            "Player B": 8
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(
            data, players_cache, player_ids, image_urls_cache, cache,
            key_name="player_name", value_name="score"
        )

        assert result[0]["player_name"] == "Player A"
        assert result[0]["score"] == 10
        assert "name" not in result[0]
        assert "count" not in result[0]

    @patch('patriot_center_backend.managers.utilities.get_image_url')
    def test_fewer_than_cutoff_items(self, mock_get_image_url):
        """Test with fewer items than cutoff."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"

        data = {
            "Player A": 10,
            "Player B": 8
        }
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = extract_dict_data(data, players_cache, player_ids, image_urls_cache, cache, cutoff=5)

        assert len(result) == 2


class TestGetImageUrl:
    """Test get_image_url function."""

    def test_draft_pick_string_url(self):
        """Test draft pick returns NFL Draft logo URL."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert "NFL_Draft_logo" in result

    def test_draft_pick_dictionary(self):
        """Test draft pick returns dict when dictionary=True."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        assert isinstance(result, dict)
        assert "NFL_Draft_logo" in result["image_url"]
        assert result["first_name"] == "Manager"
        assert result["last_name"] == "1's 2023 R3"

    def test_faab_string_url(self):
        """Test FAAB returns Mario coin URL."""
        item = "$50 FAAB"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert "Mario-Coin" in result

    def test_faab_dictionary(self):
        """Test FAAB returns dict when dictionary=True."""
        item = "$50 FAAB"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        assert isinstance(result, dict)
        assert "Mario-Coin" in result["image_url"]
        assert result["first_name"] == "$50"
        assert result["last_name"] == "FAAB"

    @patch('patriot_center_backend.managers.utilities.get_current_manager_image_url')
    @patch('patriot_center_backend.managers.utilities.NAME_TO_MANAGER_USERNAME', {"Manager 1": "user1"})
    def test_manager_string_url(self, mock_get_manager_url):
        """Test manager returns Sleeper avatar URL."""
        mock_get_manager_url.return_value = "http://sleepercdn.com/avatars/avatar123"

        item = "Manager 1"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert result == "http://sleepercdn.com/avatars/avatar123"

    @patch('patriot_center_backend.managers.utilities.get_current_manager_image_url')
    @patch('patriot_center_backend.managers.utilities.NAME_TO_MANAGER_USERNAME', {"Manager 1": "user1"})
    def test_manager_dictionary(self, mock_get_manager_url):
        """Test manager returns dict when dictionary=True."""
        mock_get_manager_url.return_value = "http://sleepercdn.com/avatars/avatar123"

        item = "Manager 1"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "http://sleepercdn.com/avatars/avatar123"
        assert result["name"] == "Manager 1"

    def test_player_numeric_id_url(self):
        """Test player with numeric ID returns player headshot URL."""
        item = "Patrick Mahomes"
        players_cache = {
            "Patrick Mahomes": {"player_id": "4046"}
        }
        player_ids = {
            "4046": {
                "first_name": "Patrick",
                "last_name": "Mahomes"
            }
        }
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert result == "https://sleepercdn.com/content/nfl/players/4046.jpg"

    def test_player_numeric_id_dictionary(self):
        """Test player with numeric ID returns dict when dictionary=True."""
        item = "Patrick Mahomes"
        players_cache = {
            "Patrick Mahomes": {"player_id": "4046"}
        }
        player_ids = {
            "4046": {
                "first_name": "Patrick",
                "last_name": "Mahomes"
            }
        }
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "https://sleepercdn.com/content/nfl/players/4046.jpg"
        assert result["first_name"] == "Patrick"
        assert result["last_name"] == "Mahomes"

    def test_team_defense_url(self):
        """Test team defense (non-numeric ID) returns team logo URL."""
        item = "Chiefs Defense"
        players_cache = {
            "Chiefs Defense": {"player_id": "KC"}
        }
        player_ids = {
            "KC": {
                "first_name": "Kansas City",
                "last_name": "Chiefs"
            }
        }
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert result == "https://sleepercdn.com/images/team_logos/nfl/kc.png"

    def test_team_defense_dictionary(self):
        """Test team defense returns dict when dictionary=True."""
        item = "Chiefs Defense"
        players_cache = {
            "Chiefs Defense": {"player_id": "KC"}
        }
        player_ids = {
            "KC": {
                "first_name": "Kansas City",
                "last_name": "Chiefs"
            }
        }
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "https://sleepercdn.com/images/team_logos/nfl/kc.png"
        assert result["first_name"] == "Kansas City"
        assert result["last_name"] == "Chiefs"

    def test_unknown_item(self):
        """Test with unknown item returns empty string."""
        item = "Unknown Item"
        players_cache = {}
        player_ids = {}
        image_urls_cache = {}
        cache = {}

        result = get_image_url(item, players_cache, player_ids, image_urls_cache, cache)

        assert result == ""


class TestGetCurrentManagerImageUrl:
    """Test get_current_manager_image_url function."""

    @patch('patriot_center_backend.managers.utilities.fetch_sleeper_data')
    def test_manager_not_in_cache(self, mock_fetch):
        """Test fetching manager image URL when not in cache."""
        mock_fetch.return_value = {"user_id": "12345", "avatar": "abc123"}

        manager = "Manager 1"
        cache = {
            "Manager 1": {
                "summary": {
                    "user_id": "12345"
                }
            }
        }
        image_urls_cache = {}

        result = get_current_manager_image_url(manager, cache, image_urls_cache)

        assert result == "https://sleepercdn.com/avatars/abc123"
        assert image_urls_cache["Manager 1"] == "https://sleepercdn.com/avatars/abc123"

    def test_manager_already_in_cache(self):
        """Test returning cached manager image URL."""
        manager = "Manager 1"
        cache = {}
        image_urls_cache = {
            "Manager 1": "https://sleepercdn.com/avatars/cached123"
        }

        result = get_current_manager_image_url(manager, cache, image_urls_cache)

        assert result == "https://sleepercdn.com/avatars/cached123"

    @patch('patriot_center_backend.managers.utilities.fetch_sleeper_data')
    def test_invalid_response(self, mock_fetch):
        """Test when API returns invalid response."""
        mock_fetch.return_value = {}

        manager = "Manager 1"
        cache = {
            "Manager 1": {
                "summary": {
                    "user_id": "12345"
                }
            }
        }
        image_urls_cache = {}

        result = get_current_manager_image_url(manager, cache, image_urls_cache)

        assert result == ""

    @patch('patriot_center_backend.managers.utilities.fetch_sleeper_data')
    def test_missing_user_id(self, mock_fetch):
        """Test when manager doesn't have user_id in cache."""
        mock_fetch.return_value = {"user_id": "", "avatar": "abc123"}

        manager = "Manager 1"
        cache = {
            "Manager 1": {
                "summary": {}
            }
        }
        image_urls_cache = {}

        result = get_current_manager_image_url(manager, cache, image_urls_cache)

        # Should still call API with empty user_id
        mock_fetch.assert_called_once_with("user/")


class TestUpdatePlayersCache:
    """Test update_players_cache function."""

    def test_update_with_single_player_id(self):
        """Test updating cache with single player ID."""
        item = "4046"
        players_cache = {}
        player_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        }

        update_players_cache(item, players_cache, player_ids)

        assert "Patrick Mahomes" in players_cache
        assert players_cache["Patrick Mahomes"]["player_id"] == "4046"
        assert players_cache["Patrick Mahomes"]["position"] == "QB"
        assert players_cache["Patrick Mahomes"]["slug"] == "patrick%20mahomes"

    def test_update_with_apostrophe_in_name(self):
        """Test URL slug creation with apostrophe in name."""
        item = "5678"
        players_cache = {}
        player_ids = {
            "5678": {
                "full_name": "D'Andre Swift",
                "first_name": "D'Andre",
                "last_name": "Swift",
                "position": "RB",
                "team": "PHI"
            }
        }

        update_players_cache(item, players_cache, player_ids)

        assert "D'Andre Swift" in players_cache
        assert players_cache["D'Andre Swift"]["slug"] == "d%27andre%20swift"

    def test_player_already_in_cache(self):
        """Test that player already in cache is not re-added."""
        item = "4046"
        players_cache = {
            "Patrick Mahomes": {
                "player_id": "4046",
                "position": "QB",
                "slug": "patrick%20mahomes"
            }
        }
        player_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        }

        original_cache = deepcopy(players_cache)
        update_players_cache(item, players_cache, player_ids)

        # Cache should remain unchanged
        assert players_cache == original_cache

    def test_update_with_matchup_list(self):
        """Test updating cache with list of matchup data."""
        item = [
            {
                "players": ["4046", "5678"]
            },
            {
                "players": ["9999"]
            }
        ]
        players_cache = {}
        player_ids = {
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
        }

        update_players_cache(item, players_cache, player_ids)

        assert len(players_cache) == 3
        assert "Patrick Mahomes" in players_cache
        assert "Travis Kelce" in players_cache
        assert "Test Player" in players_cache
    
    def test_player_not_in_player_ids(self):
        """Test handling player ID not in player_ids dict."""
        item = "9999"
        players_cache = {}
        player_ids = {}

        update_players_cache(item, players_cache, player_ids)

        # Should handle gracefully - player won't be added since no metadata
        assert len(players_cache) == 0

    def test_update_with_none_raises_error(self):
        """Test that None item raises ValueError."""
        item = None
        players_cache = {}
        player_ids = {}

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item, players_cache, player_ids)

    def test_update_with_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        item = ""
        players_cache = {}
        player_ids = {}

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item, players_cache, player_ids)

    def test_update_with_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        item = []
        players_cache = {}
        player_ids = {}

        with pytest.raises(ValueError, match="cannot be None or empty"):
            update_players_cache(item, players_cache, player_ids)

    def test_update_with_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        item = 12345  # Integer instead of string or list
        players_cache = {}
        player_ids = {}

        with pytest.raises(ValueError, match="Either matchups or player_id must be provided"):
            update_players_cache(item, players_cache, player_ids)