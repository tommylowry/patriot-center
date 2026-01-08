"""
Unit tests for utilities module.

Tests utility functions with both good and bad scenarios.
"""
from copy import deepcopy
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.utilities import draft_pick_decipher, extract_dict_data


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
        image_urls= {}

        result = extract_dict_data(data, image_urls)

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
        image_urls= {}

        result = extract_dict_data(data, image_urls)

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
        image_urls= {}

        result = extract_dict_data(data, image_urls, cutoff=0)

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
        image_urls= {}

        result = extract_dict_data(data, image_urls, cutoff=3)

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
        image_urls= {}

        result = extract_dict_data(data, image_urls,
                                   key_name="player_name",
                                   value_name="score")

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
        image_urls = {}

        result = extract_dict_data(data, image_urls, cutoff=5)

        assert len(result) == 2


class TestGetImageUrl:
    """Test get_image_url function."""

    def test_draft_pick_string_url(self):
        """Test draft pick returns NFL Draft logo URL."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert "NFL_Draft_logo" in result

    def test_draft_pick_dictionary(self):
        """Test draft pick returns dict when dictionary=True."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url
            
            result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert "NFL_Draft_logo" in result["image_url"]
        assert result["first_name"] == "Manager"
        assert result["last_name"] == "1's 2023 R3"

    def test_faab_string_url(self):
        """Test FAAB returns Mario coin URL."""
        item = "$50 FAAB"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert "Mario-Coin" in result

    def test_faab_dictionary(self):
        """Test FAAB returns dict when dictionary=True."""
        item = "$50 FAAB"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls, dictionary=True)

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
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert result == "http://sleepercdn.com/avatars/avatar123"

    @patch('patriot_center_backend.managers.utilities.get_current_manager_image_url')
    @patch('patriot_center_backend.managers.utilities.NAME_TO_MANAGER_USERNAME', {"Manager 1": "user1"})
    def test_manager_dictionary(self, mock_get_manager_url):
        """Test manager returns dict when dictionary=True."""
        mock_get_manager_url.return_value = "http://sleepercdn.com/avatars/avatar123"

        item = "Manager 1"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "http://sleepercdn.com/avatars/avatar123"
        assert result["name"] == "Manager 1"

    def test_player_numeric_id_url(self):
        """Test player with numeric ID returns player headshot URL."""
        mock_players_cache = {
            "Patrick Mahomes": {"player_id": "4046"}
        }
        mock_player_ids_cache = {
            "4046": {
                "first_name": "Patrick",
                "last_name": "Mahomes"
            }
        }
        
        item = "Patrick Mahomes"
        image_urls = {}
        
        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert result == "https://sleepercdn.com/content/nfl/players/4046.jpg"

    def test_player_numeric_id_dictionary(self):
        """Test player with numeric ID returns dict when dictionary=True."""
        mock_players_cache = {
            "Patrick Mahomes": {"player_id": "4046"}
        }
        mock_player_ids_cache = {
            "4046": {
                "first_name": "Patrick",
                "last_name": "Mahomes"
            }
        }
        
        item = "Patrick Mahomes"
        image_urls = {}
        
        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "https://sleepercdn.com/content/nfl/players/4046.jpg"
        assert result["first_name"] == "Patrick"
        assert result["last_name"] == "Mahomes"

    def test_team_defense_url(self):
        """Test team defense (non-numeric ID) returns team logo URL."""
        mock_players_cache = {
            "Kansas City Chiefs": {"player_id": "KC"}
        }
        mock_player_ids_cache = {
            "KC": {
                "first_name": "Kansas City",
                "last_name": "Chiefs"
            }
        }
        
        item = "Kansas City Chiefs"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert result == "https://sleepercdn.com/images/team_logos/nfl/kc.png"

    def test_team_defense_dictionary(self):
        """Test team defense returns dict when dictionary=True."""
        mock_players_cache = {
            "Kansas City Chiefs": {"player_id": "KC"}
        }
        mock_player_ids_cache = {
            "KC": {
                "first_name": "Kansas City",
                "last_name": "Chiefs"
            }
        }
        
        item = "Kansas City Chiefs"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "https://sleepercdn.com/images/team_logos/nfl/kc.png"
        assert result["first_name"] == "Kansas City"
        assert result["last_name"] == "Chiefs"

    def test_unknown_item(self):
        """Test with unknown item returns empty string."""
        item = "Unknown Item"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_image_url

            result = get_image_url(item, image_urls)

        assert result == ""


class TestGetCurrentManagerImageUrl:
    """Test get_current_manager_image_url function."""

    @patch('patriot_center_backend.managers.utilities.fetch_sleeper_data')
    def test_manager_not_in_cache(self, mock_fetch):
        """Test fetching manager image URL when not in cache."""
        mock_fetch.return_value = {"user_id": "12345", "avatar": "abc123"}

        mock_manager_cache = {
            "Manager 1": {
                "summary": {
                    "user_id": "12345"
                }
            }
        }
        
        manager = "Manager 1"
        image_urls = {}

        with patch('patriot_center_backend.managers.utilities.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.utilities import get_current_manager_image_url
            
            result = get_current_manager_image_url(manager, image_urls)

            assert result == "https://sleepercdn.com/avatars/abc123"
            assert image_urls["Manager 1"] == "https://sleepercdn.com/avatars/abc123"

    def test_manager_already_in_cache(self):
        """Test returning cached manager image URL."""
        manager = "Manager 1"
        image_urls = {
            "Manager 1": "https://sleepercdn.com/avatars/cached123"
        }

        with patch('patriot_center_backend.managers.utilities.MANAGER_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_current_manager_image_url
            
            result = get_current_manager_image_url(manager, image_urls)

        assert result == "https://sleepercdn.com/avatars/cached123"

    def test_missing_user_id(self):
        """Test when manager doesn't have user_id in cache."""
        mock_manager_cache = {
            "Manager 1": {
                "summary": {}
            }
        }

        with patch('patriot_center_backend.managers.utilities.MANAGER_CACHE', {}):
            from patriot_center_backend.managers.utilities import get_current_manager_image_url

            manager = "Manager 1"
            image_urls = {}

            with pytest.raises(ValueError, match="Manager Manager 1 does not have a user_id in MANAGER_CACHE."):
                get_current_manager_image_url(manager, image_urls)


class TestUpdatePlayersCache:
    """Test update_players_cache function."""

    def test_update_with_single_player_id(self):
        """Test updating cache with single player ID."""
        mock_players_cache = {}
        mock_player_ids_cache = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        }

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import utilities
            
            item = "4046"
            utilities.update_players_cache(item)

            assert "Patrick Mahomes" in utilities.PLAYERS_CACHE
            assert utilities.PLAYERS_CACHE["Patrick Mahomes"]["player_id"] == "4046"
            assert utilities.PLAYERS_CACHE["Patrick Mahomes"]["position"] == "QB"
            assert utilities.PLAYERS_CACHE["Patrick Mahomes"]["slug"] == "patrick%20mahomes"

    def test_update_with_apostrophe_in_name(self):
        """Test URL slug creation with apostrophe in name."""
        mock_players_cache = {}
        mock_player_ids_cache = {
            "5678": {
                "full_name": "D'Andre Swift",
                "first_name": "D'Andre",
                "last_name": "Swift",
                "position": "RB",
                "team": "PHI"
            }
        }

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import utilities
            
            item = "5678"
            utilities.update_players_cache(item)

            assert "D'Andre Swift" in utilities.PLAYERS_CACHE
            assert utilities.PLAYERS_CACHE["D'Andre Swift"]["slug"] == "d%27andre%20swift"

    def test_player_already_in_cache(self):
        """Test that player already in cache is not re-added."""
        mock_players_cache = {
            "Patrick Mahomes": {
                "player_id": "4046",
                "position": "QB",
                "slug": "patrick%20mahomes"
            }
        }
        mock_player_ids_cache = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC"
            }
        }

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import utilities

            original_cache = deepcopy(utilities.PLAYERS_CACHE)
            
            item = "4046"
            utilities.update_players_cache(item)

            # Cache should remain unchanged
            assert utilities.PLAYERS_CACHE == original_cache

    def test_update_with_matchup_list(self):
        """Test updating cache with list of matchup data."""
        mock_players_cache = {}
        mock_player_ids_cache = {
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

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import utilities

            item = [
                {
                    "players": ["4046", "5678"]
                },
                {
                    "players": ["9999"]
                }
            ]
            utilities.update_players_cache(item)

            assert len(utilities.PLAYERS_CACHE) == 3
            assert "Patrick Mahomes" in utilities.PLAYERS_CACHE
            assert "Travis Kelce" in utilities.PLAYERS_CACHE
            assert "Test Player" in utilities.PLAYERS_CACHE
    
    def test_player_not_in_player_ids(self):
        """Test handling player ID not in player_ids dict."""
        mock_players_cache = {}
        mock_player_ids_cache = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers import utilities

            item = "9999"
            utilities.update_players_cache(item)

            # Should handle gracefully - player won't be added since no metadata
            assert len(utilities.PLAYERS_CACHE) == 0

    def test_update_with_none_raises_error(self):
        """Test that None item raises ValueError."""
        mock_players_cache = {}
        mock_player_ids_cache = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import update_players_cache

            item = None

            with pytest.raises(ValueError, match="cannot be None or empty"):
                update_players_cache(item)

    def test_update_with_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        mock_players_cache = {}
        mock_player_ids_cache = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import update_players_cache

            item = ""

            with pytest.raises(ValueError, match="cannot be None or empty"):
                update_players_cache(item)

    def test_update_with_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        mock_players_cache = {}
        mock_player_ids_cache = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import update_players_cache

            item = []

            with pytest.raises(ValueError, match="cannot be None or empty"):
                update_players_cache(item)

    def test_update_with_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        mock_players_cache = {}
        mock_player_ids_cache = {}

        with patch('patriot_center_backend.managers.utilities.PLAYERS_CACHE', mock_players_cache), \
             patch('patriot_center_backend.managers.utilities.PLAYER_IDS_CACHE', mock_player_ids_cache):
            from patriot_center_backend.managers.utilities import update_players_cache

            item = 12345  # Integer instead of string or list

            with pytest.raises(ValueError, match="Either matchups or player_id must be provided"):
                update_players_cache(item)