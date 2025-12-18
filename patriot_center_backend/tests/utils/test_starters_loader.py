"""
Unit tests for utils/starters_loader.py - Starters cache with incremental updates.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


class TestGetMaxWeeks:
    """Test _get_max_weeks helper function."""

    def test_returns_current_week_for_current_season(self):
        """Test returns current_week for current season."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2024, current_season=2024, current_week=10) == 10
        assert _get_max_weeks(season=2025, current_season=2025, current_week=5) == 5

    def test_returns_16_for_2019_and_2020(self):
        """Test returns 16 weeks for 2019 and 2020 seasons (includes playoffs)."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2019, current_season=2024, current_week=10) == 16
        assert _get_max_weeks(season=2020, current_season=2024, current_week=10) == 16

    def test_returns_17_for_other_past_seasons(self):
        """Test returns 17 weeks for completed seasons (not 2019/2020)."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2021, current_season=2024, current_week=10) == 17
        assert _get_max_weeks(season=2023, current_season=2024, current_week=10) == 17


class TestGetRelevantPlayoffRosterIds:
    """Test _get_relevant_playoff_roster_ids playoff logic."""

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_for_regular_season_2020_and_earlier(self, mock_fetch):
        """Test returns empty dict for weeks <= 13 in 2019/2020 seasons."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        result = _get_relevant_playoff_roster_ids(2019, 13, "league_123")
        assert result == {}
        assert not mock_fetch.called

        result = _get_relevant_playoff_roster_ids(2020, 10, "league_123")
        assert result == {}
        assert not mock_fetch.called

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_for_regular_season_2021_and_later(self, mock_fetch):
        """Test returns empty dict for weeks <= 14 in 2021+ seasons."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        result = _get_relevant_playoff_roster_ids(2021, 14, "league_123")
        assert result == {}
        assert not mock_fetch.called

        result = _get_relevant_playoff_roster_ids(2024, 10, "league_123")
        assert result == {}
        assert not mock_fetch.called

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetches_playoff_bracket_for_playoff_weeks(self, mock_fetch):
        """Test fetches playoff bracket data for playoff weeks."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
            {"r": 2, "t1": 1, "t2": 3},
            {"r": 3, "t1": 1, "t2": 3, "p": 1},  # Championship
            {"r": 3, "t1": 4, "t2": 5, "p": 3}   # 3rd place
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        assert mock_fetch.called
        mock_fetch.assert_called_with("league/league_123/winners_bracket")
        assert set(result['round_roster_ids']) == {1, 2, 3, 4}

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_extracts_round_1_rosters_for_week_14_in_2019_2020(self, mock_fetch):
        """Test extracts round 1 playoff rosters for week 14 in 2019/2020."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
            {"r": 2, "t1": 1, "t2": 3},
            {"r": 3, "t1": 1, "t2": 3, "p": 1},
            {"r": 3, "t1": 4, "t2": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2019, 14, "league_123")

        assert set(result['round_roster_ids']) == {1, 2, 3, 4}

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_extracts_round_1_rosters_for_week_15_in_2021_plus(self, mock_fetch):
        """Test extracts round 1 playoff rosters for week 15 in 2021+."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
            {"r": 2, "t1": 1, "t2": 3},
            {"r": 3, "t1": 1, "t2": 3, "p": 1},
            {"r": 3, "t1": 4, "t2": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        assert set(result['round_roster_ids']) == {1, 2, 3, 4}

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_skips_consolation_bracket_matchups(self, mock_fetch):
        """Test skips matchups with p=5 (consolation bracket)."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
            {"r": 1, "t1": 7, "t2": 8, "p": 5},  # Consolation - should skip
            {"r": 2, "t1": 1, "t2": 3},
            {"r": 3, "t1": 1, "t2": 3, "p": 1},
            {"r": 3, "t1": 4, "t2": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        # Should not include rosters 7 and 8 from consolation
        assert 7 not in result['round_roster_ids']
        assert 8 not in result['round_roster_ids']

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_raises_error_for_week_17(self, mock_fetch):
        """Test raises ValueError for week 17 in 2019/2020 (round 4 is unsupported)."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        # Week 17 in 2019 maps to round 4 which explicitly raises error
        mock_fetch.return_value = ([], 200)

        with pytest.raises(ValueError, match="Cannot get playoff roster IDs for week 17"):
            _get_relevant_playoff_roster_ids(2019, 17, "league_123")

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_raises_error_when_no_round_rosters_found(self, mock_fetch):
        """Test raises ValueError when no rosters found for the round."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        # Empty bracket
        mock_fetch.return_value = ([], 200)

        with pytest.raises(ValueError, match="Cannot get playoff roster IDs for the given week"):
            _get_relevant_playoff_roster_ids(2024, 15, "league_123")


class TestGetPlayoffPlacement:
    """Test _get_playoff_placement final placement retrieval."""

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {
        "tommy_sleeper": "Tommy",
        "mike_sleeper": "Mike",
        "davey_sleeper": "Davey"
    })
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_retrieves_first_second_third_place(self, mock_fetch):
        """Test retrieves 1st, 2nd, 3rd place from playoff bracket."""
        from patriot_center_backend.utils.starters_loader import _get_playoff_placement

        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4},
            {"r": 2, "w": 1, "l": 3},
            {"r": 3, "w": 1, "l": 3},  # Championship: 1 wins (1st), 3 loses (2nd)
            {"r": 3, "w": 4, "l": 5}   # 3rd place: 4 wins (3rd)
        ]
        rosters = [
            {"owner_id": "user_tommy", "roster_id": 1},
            {"owner_id": "user_mike", "roster_id": 3},
            {"owner_id": "user_davey", "roster_id": 4}
        ]
        users = [
            {"user_id": "user_tommy", "display_name": "tommy_sleeper"},
            {"user_id": "user_mike", "display_name": "mike_sleeper"},
            {"user_id": "user_davey", "display_name": "davey_sleeper"}
        ]

        def fetch_side_effect(endpoint):
            if "winners_bracket" in endpoint:
                return (playoff_bracket, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "users" in endpoint:
                return (users, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = _get_playoff_placement(2024)

        assert result["Tommy"] == 1  # Championship winner
        assert result["Mike"] == 2   # Championship loser
        assert result["Davey"] == 3  # 3rd place winner

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_bracket_api_failure(self, mock_fetch):
        """Test returns empty dict when playoff bracket API fails."""
        from patriot_center_backend.utils.starters_loader import _get_playoff_placement

        mock_fetch.return_value = ({"error": "Not found"}, 404)

        result = _get_playoff_placement(2024)

        assert result == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_rosters_api_failure(self, mock_fetch):
        """Test returns empty dict when rosters API fails."""
        from patriot_center_backend.utils.starters_loader import _get_playoff_placement

        def fetch_side_effect(endpoint):
            if "winners_bracket" in endpoint:
                return ([{"r": 3, "w": 1, "l": 3}], 200)
            elif "rosters" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = _get_playoff_placement(2024)

        assert result == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_users_api_failure(self, mock_fetch):
        """Test returns empty dict when users API fails."""
        from patriot_center_backend.utils.starters_loader import _get_playoff_placement

        def fetch_side_effect(endpoint):
            if "winners_bracket" in endpoint:
                return ([{"r": 3, "w": 1, "l": 3}], 200)
            elif "rosters" in endpoint:
                return ([{"owner_id": "user_123", "roster_id": 1}], 200)
            elif "users" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = _get_playoff_placement(2024)

        assert result == {}


class TestGetRosterId:
    """Test get_roster_id roster lookup."""

    def test_finds_roster_by_user_id(self):
        """Test finds correct roster_id for given user_id."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = (
            [
                {"owner_id": "user_123", "roster_id": 1},
                {"owner_id": "user_456", "roster_id": 2},
                {"owner_id": "user_789", "roster_id": 3}
            ],
            200
        )

        assert get_roster_id(rosters_response, "user_123") == 1
        assert get_roster_id(rosters_response, "user_456") == 2
        assert get_roster_id(rosters_response, "user_789") == 3

    def test_returns_none_when_user_not_found(self):
        """Test returns None when user_id doesn't match any roster."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = (
            [
                {"owner_id": "user_123", "roster_id": 1},
                {"owner_id": "user_456", "roster_id": 2}
            ],
            200
        )

        assert get_roster_id(rosters_response, "user_999") is None

    def test_returns_none_for_empty_rosters(self):
        """Test returns None when rosters list is empty."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = ([], 200)
        assert get_roster_id(rosters_response, "user_123") is None


class TestUpdatePlayersCache:
    """Test _update_players_cache player metadata caching."""

    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    def test_adds_new_player_to_cache(self, mock_load, mock_save):
        """Test adds new player with metadata when not in cache."""
        from patriot_center_backend.utils.starters_loader import _update_players_cache

        mock_load.return_value = {}

        player_meta = {
            "full_name": "Josh Allen",
            "first_name": "Josh",
            "last_name": "Allen",
            "position": "QB",
            "team": "BUF"
        }
        players_cache = {}

        result = _update_players_cache(player_meta, players_cache)

        # Should add player to cache
        assert "Josh Allen" in result
        assert result["Josh Allen"]["full_name"] == "Josh Allen"
        assert result["Josh Allen"]["first_name"] == "Josh"
        assert result["Josh Allen"]["last_name"] == "Allen"
        assert result["Josh Allen"]["position"] == "QB"
        assert result["Josh Allen"]["team"] == "BUF"
        assert result["Josh Allen"]["slug"] == "Josh_Allen"

        # Should save cache
        assert mock_save.called

    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    def test_creates_url_safe_slug_with_apostrophe(self, mock_load, mock_save):
        """Test converts apostrophes to %27 in slug for URL safety."""
        from patriot_center_backend.utils.starters_loader import _update_players_cache

        mock_load.return_value = {}

        player_meta = {
            "full_name": "D'Andre Swift",
            "first_name": "D'Andre",
            "last_name": "Swift",
            "position": "RB",
            "team": "PHI"
        }
        players_cache = {}

        result = _update_players_cache(player_meta, players_cache)

        # Apostrophe should be URL-encoded
        assert result["D'Andre Swift"]["slug"] == "D%27Andre_Swift"

    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    def test_does_not_add_duplicate_player(self, mock_load, mock_save):
        """Test does not add player if already in cache."""
        from patriot_center_backend.utils.starters_loader import _update_players_cache

        mock_load.return_value = {}

        existing_cache = {
            "Josh Allen": {
                "full_name": "Josh Allen",
                "first_name": "Josh",
                "last_name": "Allen",
                "position": "QB",
                "team": "BUF",
                "slug": "Josh_Allen"
            }
        }

        player_meta = {
            "full_name": "Josh Allen",
            "first_name": "Josh",
            "last_name": "Allen",
            "position": "QB",
            "team": "BUF"
        }

        result = _update_players_cache(player_meta, existing_cache)

        # Should not modify cache
        assert result == existing_cache
        # Should not save cache
        assert not mock_save.called

    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    def test_handles_missing_metadata_fields(self, mock_load, mock_save):
        """Test handles missing metadata fields gracefully with empty strings."""
        from patriot_center_backend.utils.starters_loader import _update_players_cache

        mock_load.return_value = {}

        player_meta = {
            "full_name": "Unknown Player"
            # Missing first_name, last_name, position, team
        }
        players_cache = {}

        result = _update_players_cache(player_meta, players_cache)

        # Should add player with empty strings for missing fields
        assert "Unknown Player" in result
        assert result["Unknown Player"]["full_name"] == "Unknown Player"
        assert result["Unknown Player"]["first_name"] == ""
        assert result["Unknown Player"]["last_name"] == ""
        assert result["Unknown Player"]["position"] == ""
        assert result["Unknown Player"]["team"] == ""


@patch('patriot_center_backend.utils.starters_loader.save_cache')
class TestGetStartersData:
    """Test get_starters_data starter extraction."""

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB"},
        "NE": {"full_name": "New England Patriots", "position": "DEF"}
    })
    def test_extracts_starters_and_points(self, mock_save):
        """Test extracts starter data with points and positions."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547", "4034", "NE"],
                    "players_points": {
                        "7547": 15.6,
                        "4034": 28.3,
                        "NE": 12.0
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Should have all three players
        assert "Amon-Ra St. Brown" in result
        assert "Christian McCaffrey" in result
        assert "New England Patriots" in result

        # Verify points
        assert result["Amon-Ra St. Brown"]["points"] == 15.6
        assert result["Christian McCaffrey"]["points"] == 28.3
        assert result["New England Patriots"]["points"] == 12.0

        # Verify positions
        assert result["Amon-Ra St. Brown"]["position"] == "WR"
        assert result["Christian McCaffrey"]["position"] == "RB"
        assert result["New England Patriots"]["position"] == "DEF"

        # Verify player_ids
        assert result["Amon-Ra St. Brown"]["player_id"] == "7547"
        assert result["Christian McCaffrey"]["player_id"] == "4034"
        assert result["New England Patriots"]["player_id"] == "NE"

        # Verify tracking arrays
        assert "Amon-Ra St. Brown" in players_array
        assert "Christian McCaffrey" in players_array
        assert "New England Patriots" in players_array
        assert "WR" in positions_array
        assert "RB" in positions_array
        assert "DEF" in positions_array

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB"}
    })
    def test_calculates_total_points_correctly(self, mock_save):
        """Test sums all player points into Total_Points."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547", "4034"],
                    "players_points": {
                        "7547": 15.6,
                        "4034": 28.3
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Total: 15.6 + 28.3 = 43.9
        assert result["Total_Points"] == 43.9

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_rounds_total_points_to_2_decimals(self, mock_save):
        """Test rounds Total_Points to 2 decimal places using Decimal."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 15.666666  # Should round to 15.67
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Decimal rounding should give us exactly 2 decimals
        # 15.666666 rounds to 15.67
        assert result["Total_Points"] == 15.67

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {})
    def test_skips_players_not_in_player_ids(self, mock_save):
        """Test skips players without metadata (not in PLAYER_IDS)."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["unknown_player"],
                    "players_points": {
                        "unknown_player": 20.0
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Should only have Total_Points (0.0 since no valid players)
        assert result["Total_Points"] == 0.0
        assert len(result) == 1  # Only Total_Points

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown"}  # Missing position
    })
    def test_skips_players_without_position(self, mock_save):
        """Test skips players missing position field."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 20.0
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Should skip player without position
        assert "Amon-Ra St. Brown" not in result
        assert result["Total_Points"] == 0.0

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"position": "WR"}  # Missing full_name
    })
    def test_skips_players_without_full_name(self, mock_save):
        """Test skips players missing full_name field."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 20.0
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        # Should skip player without full_name
        assert result["Total_Points"] == 0.0

    def test_returns_empty_dict_when_roster_not_found(self, mock_save):
        """Test returns empty dict when roster_id doesn't exist in matchups."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {"roster_id": 1, "starters": [], "players_points": {}},
                {"roster_id": 2, "starters": [], "players_points": {}}
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 999, [], [])
        assert result == {}
        assert players_array == []
        assert positions_array == []

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_handles_zero_points_correctly(self, mock_save):
        """Test handles players with 0 points."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 0.0
                    }
                }
            ],
            200
        )

        result, players_array, positions_array = get_starters_data(matchups_response, 1, [], [])

        assert result["Amon-Ra St. Brown"]["points"] == 0.0
        assert result["Total_Points"] == 0.0


@pytest.mark.usefixtures("use_real_load_or_update_starters")
@patch('patriot_center_backend.utils.starters_loader.save_cache')
class TestFetchStartersForWeek:
    """Test fetch_starters_for_week API integration and data mapping."""

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_user": "Tommy"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetches_from_sleeper_api_successfully(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test fetches users, rosters, and matchups from Sleeper API."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}  # Regular season
        users = [{"user_id": "user_123", "display_name": "sleeper_user"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # Should have data for Tommy (mapped from sleeper_user)
        assert "Tommy" in week_data
        assert "Amon-Ra St. Brown" in week_data["Tommy"]
        assert week_data["Tommy"]["Amon-Ra St. Brown"]["points"] == 15.6

        # Verify tracking arrays
        assert "Tommy" in managers_array
        assert "Amon-Ra St. Brown" in players_array
        assert "WR" in positions_array

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_users_api_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test returns empty dict when users API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        mock_fetch.return_value = ({"error": "Not found"}, 404)

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)
        assert week_data == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_rosters_api_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test returns empty dict when rosters API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "Tommy"}], 200)
            elif "rosters" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)
        assert week_data == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_matchups_api_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test returns empty dict when matchups API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "Tommy"}], 200)
            elif "rosters" in endpoint:
                return ([{"owner_id": "user_123", "roster_id": 1}], 200)
            elif "matchups" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)
        assert week_data == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2019: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_cody": "Cody"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_applies_2019_early_week_cody_to_tommy_correction(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test converts Cody to Tommy for 2019 weeks < 4."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_123", "display_name": "sleeper_cody"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        # Week 3 - should convert Cody to Tommy
        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2019, 3)
        assert "Tommy" in week_data
        assert "Cody" not in week_data

        # Week 4 - should NOT convert (week >= 4)
        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2019, 4)
        assert "Cody" in week_data
        assert "Tommy" not in week_data

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_davey": "Davey"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_applies_2024_davey_roster_id_hardcode(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test hardcodes roster_id=4 for Davey in 2024 when roster lookup fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_davey", "display_name": "sleeper_davey"}]
        # Rosters doesn't have user_davey - triggers hardcode
        rosters = [{"owner_id": "other_user", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 4,  # Hardcoded roster_id for Davey
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # Should have data for Davey with hardcoded roster_id=4
        assert "Davey" in week_data
        assert "Amon-Ra St. Brown" in week_data["Davey"]

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.starters_loader.MANAGER_METADATA')
    def test_uses_unknown_manager_for_unmapped_display_names(self, mock_manager_metadata, mock_fetch, mock_playoff_ids, mock_save):
        """Test uses 'Unknown Manager' for display names not in USERNAME_TO_REAL_NAME."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_123", "display_name": "unmapped_user"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # Should use "Unknown Manager" as fallback
        assert "Unknown Manager" in week_data


class TestRetroactivelyAssignTeamPlacement:
    """Test retroactively_assign_team_placement_for_player placement assignment."""

    @patch('patriot_center_backend.utils.starters_loader._get_playoff_placement')
    def test_assigns_placements_to_playoff_weeks_2021_plus(self, mock_placement):
        """Test assigns placements to weeks 15-17 for 2021+ seasons."""
        from patriot_center_backend.utils.starters_loader import retroactively_assign_team_placement_for_player_and_manager_metadata

        mock_placement.return_value = {"Tommy": 1, "Mike": 2, "Davey": 3}

        starters_cache = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881"},
                        "Total_Points": 100.0
                    },
                    "Mike": {
                        "Patrick Mahomes": {"points": 22.0, "position": "QB", "player_id": "4046"},
                        "Total_Points": 95.0
                    }
                },
                "16": {
                    "Tommy": {
                        "Josh Allen": {"points": 28.0, "position": "QB", "player_id": "4881"},
                        "Total_Points": 110.0
                    }
                },
                "17": {
                    "Davey": {
                        "Christian McCaffrey": {"points": 20.0, "position": "RB", "player_id": "1234"},
                        "Total_Points": 85.0
                    }
                }
            }
        }

        result = retroactively_assign_team_placement_for_player_and_manager_metadata(2024, starters_cache)

        # Verify Tommy (1st place) has placement assigned
        assert result["2024"]["15"]["Tommy"]["Josh Allen"]["placement"] == 1
        assert result["2024"]["16"]["Tommy"]["Josh Allen"]["placement"] == 1

        # Verify Mike (2nd place) has placement assigned
        assert result["2024"]["15"]["Mike"]["Patrick Mahomes"]["placement"] == 2

        # Verify Davey (3rd place) has placement assigned
        assert result["2024"]["17"]["Davey"]["Christian McCaffrey"]["placement"] == 3

        # Verify Total_Points is still a float, not a dict (doesn't get placement field)
        assert isinstance(result["2024"]["15"]["Tommy"]["Total_Points"], float)

    @patch('patriot_center_backend.utils.starters_loader._get_playoff_placement')
    def test_assigns_placements_to_playoff_weeks_2019_2020(self, mock_placement):
        """Test assigns placements to weeks 14-16 for 2019/2020 seasons."""
        from patriot_center_backend.utils.starters_loader import retroactively_assign_team_placement_for_player_and_manager_metadata

        mock_placement.return_value = {"Tommy": 1}

        starters_cache = {
            "2020": {
                "14": {
                    "Tommy": {
                        "Derrick Henry": {"points": 30.0, "position": "RB", "player_id": "9999"},
                        "Total_Points": 120.0
                    }
                },
                "15": {
                    "Tommy": {
                        "Derrick Henry": {"points": 28.0, "position": "RB", "player_id": "9999"},
                        "Total_Points": 115.0
                    }
                }
            }
        }

        result = retroactively_assign_team_placement_for_player_and_manager_metadata(2020, starters_cache)

        # Verify weeks 14-15 get placements for 2020
        assert result["2020"]["14"]["Tommy"]["Derrick Henry"]["placement"] == 1
        assert result["2020"]["15"]["Tommy"]["Derrick Henry"]["placement"] == 1

    @patch('patriot_center_backend.utils.starters_loader._get_playoff_placement')
    def test_returns_unchanged_cache_when_placement_api_fails(self, mock_placement):
        """Test returns cache unchanged when _get_playoff_placement returns empty dict."""
        from patriot_center_backend.utils.starters_loader import retroactively_assign_team_placement_for_player_and_manager_metadata

        mock_placement.return_value = {}  # API failure

        starters_cache = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881"},
                        "Total_Points": 100.0
                    }
                }
            }
        }

        result = retroactively_assign_team_placement_for_player_and_manager_metadata(2024, starters_cache)

        # Cache should be unchanged
        assert result == starters_cache
        assert "placement" not in result["2024"]["15"]["Tommy"]["Josh Allen"]

    @patch('patriot_center_backend.utils.starters_loader._get_playoff_placement')
    def test_returns_immediately_if_placement_already_assigned(self, mock_placement):
        """Test returns immediately without calling API if placement already exists."""
        from patriot_center_backend.utils.starters_loader import retroactively_assign_team_placement_for_player_and_manager_metadata

        mock_placement.return_value = {"Tommy": 1}

        starters_cache = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881", "placement": 1},
                        "Total_Points": 100.0
                    }
                }
            }
        }

        result = retroactively_assign_team_placement_for_player_and_manager_metadata(2024, starters_cache)

        # Should return immediately without modification
        assert result == starters_cache
        # _get_playoff_placement should still be called
        assert mock_placement.called

    @patch('patriot_center_backend.utils.starters_loader._get_playoff_placement')
    def test_skips_managers_not_in_placement_dict(self, mock_placement):
        """Test skips managers who didn't place in top 3."""
        from patriot_center_backend.utils.starters_loader import retroactively_assign_team_placement_for_player_and_manager_metadata

        mock_placement.return_value = {"Tommy": 1}  # Only Tommy placed

        starters_cache = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881"},
                        "Total_Points": 100.0
                    },
                    "Other Manager": {
                        "Patrick Mahomes": {"points": 22.0, "position": "QB", "player_id": "4046"},
                        "Total_Points": 95.0
                    }
                }
            }
        }

        result = retroactively_assign_team_placement_for_player_and_manager_metadata(2024, starters_cache)

        # Tommy should have placement
        assert result["2024"]["15"]["Tommy"]["Josh Allen"]["placement"] == 1

        # Other Manager should NOT have placement
        assert "placement" not in result["2024"]["15"]["Other Manager"]["Patrick Mahomes"]


@pytest.mark.usefixtures("use_real_load_or_update_starters")
@patch('patriot_center_backend.utils.starters_loader.MANAGER_METADATA')
class TestLoadOrUpdateStartersCache:
    """Test load_or_update_starters_cache main orchestration."""

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_creates_new_cache_with_baseline_structure(self, mock_fetch, mock_save, mock_load, mock_current, mock_manager_metadata):
        """Test initializes new cache with Last_Updated markers."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 1)
        mock_load.side_effect = lambda filename, **kwargs: {} if 'valid_options' not in filename else {}
        mock_fetch.return_value = (
            {
                "Tommy": {
                    "Total_Points": 100.0,
                    "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881"}
                }
            },
            ["Tommy"],
            ["Josh Allen"],
            ["QB"],
            {"managers": ["Tommy"], "players": ["Josh Allen"], "positions": ["QB"]}
        )

        result = load_or_update_starters_cache()

        # Should have called save (twice: starters_cache and valid_options_cache)
        assert mock_save.called
        # Result should NOT include metadata (popped before return)
        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_resumes_from_last_updated_markers(self, mock_fetch, mock_save, mock_load, mock_current, mock_manager_metadata):
        """Test resumes processing from Last_Updated_Season and Last_Updated_Week."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 5)

        # Cache already has weeks 1-3
        def load_side_effect(filename, **kwargs):
            if 'valid_options' in filename:
                return {"2024": {"managers": ["Tommy"], "players": [], "positions": [], "weeks": ["1", "2", "3"]}}
            return {
                "Last_Updated_Season": "2024",
                "Last_Updated_Week": 3,
                "2024": {
                    "1": {"Tommy": {"Total_Points": 100.0}},
                    "2": {"Tommy": {"Total_Points": 105.0}},
                    "3": {"Tommy": {"Total_Points": 110.0}}
                }
            }

        mock_load.side_effect = load_side_effect
        mock_fetch.return_value = ({"Tommy": {"Total_Points": 115.0}}, ["Tommy"], [], [], {"managers": ["Tommy"], "players": [], "positions": []})

        result = load_or_update_starters_cache()

        # Should only fetch weeks 4 and 5 (not 1-3)
        assert mock_fetch.call_count == 2

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_skips_when_fully_up_to_date(self, mock_save, mock_load, mock_current, mock_manager_metadata):
        """Test skips processing when cache is already current."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 5)

        # Cache is already at 2024 week 5
        def load_side_effect(filename, **kwargs):
            if 'valid_options' in filename:
                return {"2024": {"managers": ["Tommy"], "players": [], "positions": [], "weeks": [str(w) for w in range(1, 6)]}}
            return {
                "Last_Updated_Season": "2024",
                "Last_Updated_Week": 5,
                "2024": {str(w): {"Tommy": {"Total_Points": 100.0}} for w in range(1, 6)}
            }

        mock_load.side_effect = load_side_effect

        result = load_or_update_starters_cache()

        # Should still save but not fetch new data
        assert mock_save.called

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_caps_current_week_at_17(self, mock_fetch, mock_save, mock_load, mock_current, mock_manager_metadata):
        """Test caps current_week at 17 (regular season) even if API returns higher."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        # API returns week 18 (playoffs)
        mock_current.return_value = (2024, 18)
        mock_load.side_effect = lambda filename, **kwargs: {} if 'valid_options' not in filename else {}
        mock_fetch.return_value = ({"Tommy": {"Total_Points": 100.0}}, [], [], [], {})

        result = load_or_update_starters_cache()

        # Should cap at 17, so max 17 calls
        assert mock_fetch.call_count <= 17

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2019: "id1", 2020: "id2"})
    def test_processes_2019_and_2020_with_16_week_cap(self, mock_fetch, mock_save, mock_load, mock_current, mock_manager_metadata):
        """Test processes 2019 and 2020 with 16-week cap (includes playoffs)."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        # Current season is 2021 so 2019 and 2020 are past seasons
        mock_current.return_value = (2021, 10)
        mock_load.side_effect = lambda filename, **kwargs: {} if 'valid_options' not in filename else {}
        mock_fetch.return_value = ({"Tommy": {"Total_Points": 100.0}}, ["Tommy"], [], [], {"managers": ["Tommy"], "players": [], "positions": []})

        result = load_or_update_starters_cache()

        # Should process:
        # - 2019: 16 weeks (includes playoffs)
        # - 2020: 16 weeks (includes playoffs)
        # Total: 32 calls
        assert mock_fetch.call_count == 32


@pytest.mark.usefixtures("use_real_load_or_update_starters")
@patch('patriot_center_backend.utils.starters_loader.save_cache')
class TestRefactoredReturnValues:
    """Comprehensive tests for refactored methods with new multi-value return signatures."""

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"tommy_sleeper": "Tommy"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "4881": {"full_name": "Josh Allen", "position": "QB"},
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetch_starters_for_week_returns_all_five_values_success(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test that fetch_starters_for_week returns all 5 values correctly on success."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_123", "display_name": "tommy_sleeper"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["4881", "7547"],
                "players_points": {"4881": 25.5, "7547": 18.3}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # Verify return value 1: week_data (dict)
        assert isinstance(week_data, dict)
        assert "Tommy" in week_data
        assert "Josh Allen" in week_data["Tommy"]
        assert week_data["Tommy"]["Total_Points"] == 43.8

        # Verify return value 2: managers_array (list)
        assert isinstance(managers_array, list)
        assert "Tommy" in managers_array
        assert len(managers_array) == 1

        # Verify return value 3: players_array (list)
        assert isinstance(players_array, list)
        assert "Josh Allen" in players_array
        assert "Amon-Ra St. Brown" in players_array
        assert len(players_array) == 2

        # Verify return value 4: positions_array (list)
        assert isinstance(positions_array, list)
        assert "QB" in positions_array
        assert "WR" in positions_array
        assert len(positions_array) == 2

        # Verify return value 5: week_valid_data (dict)
        assert isinstance(week_valid_data, dict)
        assert "managers" in week_valid_data
        assert "players" in week_valid_data
        assert "positions" in week_valid_data
        assert "Tommy" in week_valid_data
        assert week_valid_data["Tommy"]["players"] == ["Josh Allen", "Amon-Ra St. Brown"]
        assert week_valid_data["Tommy"]["positions"] == ["QB", "WR"]

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetch_starters_for_week_returns_all_empty_values_on_users_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test that fetch_starters_for_week returns tuple of 5 empty values on users API failure."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        mock_fetch.return_value = ({"error": "Not found"}, 404)

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # All 5 return values should be empty
        assert week_data == {}
        assert managers_array == []
        assert players_array == []
        assert positions_array == []
        assert week_valid_data == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetch_starters_for_week_returns_all_empty_values_on_rosters_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test that fetch_starters_for_week returns tuple of 5 empty values on rosters API failure."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "tommy"}], 200)
            elif "rosters" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # All 5 return values should be empty
        assert week_data == {}
        assert managers_array == []
        assert players_array == []
        assert positions_array == []
        assert week_valid_data == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetch_starters_for_week_returns_all_empty_values_on_matchups_failure(self, mock_fetch, mock_playoff_ids, mock_save):
        """Test that fetch_starters_for_week returns tuple of 5 empty values on matchups API failure."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "tommy"}], 200)
            elif "rosters" in endpoint:
                return ([{"owner_id": "user_123", "roster_id": 1}], 200)
            elif "matchups" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # All 5 return values should be empty
        assert week_data == {}
        assert managers_array == []
        assert players_array == []
        assert positions_array == []
        assert week_valid_data == {}

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "4881": {"full_name": "Josh Allen", "position": "QB"},
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "1234": {"full_name": "Christian McCaffrey", "position": "RB"}
    })
    def test_get_starters_data_returns_all_three_values_success(self, mock_save):
        """Test that get_starters_data returns all 3 values correctly on success."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups = ([
            {
                "roster_id": 5,
                "starters": ["4881", "7547", "1234"],
                "players_points": {"4881": 30.2, "7547": 22.5, "1234": 15.8}
            }
        ], 200)

        manager_data, players_array, positions_array = get_starters_data(
            matchups, 5, [], []
        )

        # Verify return value 1: manager_data (dict)
        assert isinstance(manager_data, dict)
        assert "Josh Allen" in manager_data
        assert "Amon-Ra St. Brown" in manager_data
        assert "Christian McCaffrey" in manager_data
        assert manager_data["Total_Points"] == 68.5
        assert manager_data["Josh Allen"]["points"] == 30.2
        assert manager_data["Josh Allen"]["position"] == "QB"

        # Verify return value 2: players_array (list)
        assert isinstance(players_array, list)
        assert "Josh Allen" in players_array
        assert "Amon-Ra St. Brown" in players_array
        assert "Christian McCaffrey" in players_array
        assert len(players_array) == 3

        # Verify return value 3: positions_array (list)
        assert isinstance(positions_array, list)
        assert "QB" in positions_array
        assert "WR" in positions_array
        assert "RB" in positions_array
        assert len(positions_array) == 3

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {})
    def test_get_starters_data_returns_empty_tuple_when_roster_not_found(self, mock_save):
        """Test that get_starters_data returns tuple of 3 values when roster not found."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups = ([
            {"roster_id": 1, "starters": ["4881"], "players_points": {"4881": 25.0}}
        ], 200)

        # Request roster_id 99 which doesn't exist
        manager_data, players_array, positions_array = get_starters_data(
            matchups, 99, [], []
        )

        # Should return empty dict and preserve input arrays
        assert manager_data == {}
        assert players_array == []
        assert positions_array == []

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "4881": {"full_name": "Josh Allen", "position": "QB"}
    })
    def test_get_starters_data_accumulates_arrays_across_calls(self, mock_save):
        """Test that get_starters_data properly accumulates players and positions arrays."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups = ([
            {"roster_id": 1, "starters": ["4881"], "players_points": {"4881": 25.0}}
        ], 200)

        # First call with empty arrays
        manager_data1, players_array1, positions_array1 = get_starters_data(
            matchups, 1, [], []
        )

        assert "Josh Allen" in players_array1
        assert "QB" in positions_array1

        # Second call reusing the arrays (simulating accumulation)
        manager_data2, players_array2, positions_array2 = get_starters_data(
            matchups, 1, players_array1, positions_array1
        )

        # Arrays should not have duplicates (players are added only if not present)
        assert players_array2.count("Josh Allen") == 1
        assert positions_array2.count("QB") == 1

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {
        "tommy_sleeper": "Tommy",
        "mike_sleeper": "Mike"
    })
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "4881": {"full_name": "Josh Allen", "position": "QB"},
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "1234": {"full_name": "Christian McCaffrey", "position": "RB"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    @patch('patriot_center_backend.utils.starters_loader.MANAGER_METADATA')
    def test_fetch_starters_for_week_aggregates_multiple_managers(self, mock_manager_metadata, mock_fetch, mock_playoff_ids, mock_save):
        """Test that fetch_starters_for_week correctly aggregates data from multiple managers."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [
            {"user_id": "user_123", "display_name": "tommy_sleeper"},
            {"user_id": "user_456", "display_name": "mike_sleeper"}
        ]
        rosters = [
            {"owner_id": "user_123", "roster_id": 1},
            {"owner_id": "user_456", "roster_id": 2}
        ]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["4881"],
                "players_points": {"4881": 25.0}
            },
            {
                "roster_id": 2,
                "starters": ["7547", "1234"],
                "players_points": {"7547": 18.5, "1234": 22.0}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        week_data, managers_array, players_array, positions_array, week_valid_data = fetch_starters_for_week(2024, 1)

        # Verify managers aggregation
        assert len(managers_array) == 2
        assert "Tommy" in managers_array
        assert "Mike" in managers_array

        # Verify players aggregation (no duplicates)
        assert len(players_array) == 3
        assert "Josh Allen" in players_array
        assert "Amon-Ra St. Brown" in players_array
        assert "Christian McCaffrey" in players_array

        # Verify positions aggregation (no duplicates)
        assert len(positions_array) == 3
        assert "QB" in positions_array
        assert "WR" in positions_array
        assert "RB" in positions_array

        # Verify week_valid_data structure
        assert "Tommy" in week_valid_data
        assert "Mike" in week_valid_data
        assert week_valid_data["Tommy"]["players"] == ["Josh Allen"]
        assert week_valid_data["Mike"]["players"] == ["Amon-Ra St. Brown", "Christian McCaffrey"]
