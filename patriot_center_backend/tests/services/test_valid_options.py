import pytest
from unittest.mock import patch, MagicMock
import copy

from patriot_center_backend.services.valid_options import (
    fetch_valid_options,
    _parse_args,
    _trim_list,
    _filter_year,
    _filter_week,
    _filter_manager,
    _filter_player
)


class TestParseArgs:
    """Test _parse_args function."""

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1", 2022: "id2", 2023: "id3"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Cody": "cody_user"})
    def test_parses_year_week_manager(self, mock_fetch_players):
        """Test parsing year, week, and manager arguments."""
        mock_fetch_players.return_value = {"Patrick Mahomes": {"position": "QB"}}

        year, week, manager, player = _parse_args(2021, 5, "Tommy")

        assert year == 2021
        assert week == 5
        assert manager == "Tommy"
        assert player is None

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    def test_parses_year_week_player(self, mock_fetch_players):
        """Test parsing year, week, and player arguments."""
        mock_fetch_players.return_value = {"Patrick Mahomes": {"position": "QB"}}

        year, week, manager, player = _parse_args(2021, 5, "Patrick_Mahomes")

        assert year == 2021
        assert week == 5
        assert manager is None
        assert player == "Patrick Mahomes"

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_parses_string_numbers(self, mock_fetch_players):
        """Test parsing string representations of numbers."""
        mock_fetch_players.return_value = {}

        year, week, manager, player = _parse_args("2021", "5", None)

        assert year == 2021
        assert week == 5
        assert manager is None
        assert player is None

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_handles_none_arguments(self, mock_fetch_players):
        """Test handling all None arguments."""
        mock_fetch_players.return_value = {}

        year, week, manager, player = _parse_args(None, None, None)

        assert year is None
        assert week is None
        assert manager is None
        assert player is None

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1", 2022: "id2"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_raises_on_multiple_years(self, mock_fetch_players):
        """Test raises error when multiple years provided."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Multiple year arguments"):
            _parse_args(2021, 2022, None)

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Cody": "cody_user"})
    def test_raises_on_multiple_managers(self, mock_fetch_players):
        """Test raises error when multiple managers provided."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Multiple manager arguments"):
            _parse_args("Tommy", "Cody", None)

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_raises_on_multiple_weeks(self, mock_fetch_players):
        """Test raises error when multiple weeks provided."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Multiple week arguments"):
            _parse_args(5, 6, None)

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_raises_on_invalid_week(self, mock_fetch_players):
        """Test raises error when week is out of range."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Unrecognized integer argument"):
            _parse_args(18, None, None)  # Week 18 is invalid

        with pytest.raises(ValueError, match="Unrecognized integer argument"):
            _parse_args(0, None, None)  # Week 0 is invalid

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_raises_on_unrecognized_string(self, mock_fetch_players):
        """Test raises error on unrecognized string argument."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Unrecognized argument"):
            _parse_args("InvalidManager", None, None)

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_normalizes_player_name_with_underscore(self, mock_fetch_players):
        """Test player name normalization with underscores."""
        mock_fetch_players.return_value = {"Amon-Ra St. Brown": {"position": "WR"}}

        year, week, manager, player = _parse_args("Amon-Ra_St._Brown", None, None)

        assert player == "Amon-Ra St. Brown"

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    def test_normalizes_player_name_with_apostrophe(self, mock_fetch_players):
        """Test player name normalization with URL-encoded apostrophe."""
        mock_fetch_players.return_value = {"D'Andre Swift": {"position": "RB"}}

        year, week, manager, player = _parse_args("D%27Andre_Swift", None, None)

        assert player == "D'Andre Swift"


class TestTrimList:
    """Test _trim_list helper function."""

    def test_trims_list_based_on_keep_list(self):
        """Test trimming items not in keep_list."""
        original = [1, 2, 3, 4, 5]
        keep = [2, 4]

        result = _trim_list(original, keep)

        assert result == [2, 4]
        assert original == [2, 4]  # Original list is modified

    def test_returns_original_when_keep_list_empty(self):
        """Test returns original list when keep_list is empty."""
        original = [1, 2, 3, 4, 5]
        keep = []

        result = _trim_list(original, keep)

        assert result == [1, 2, 3, 4, 5]

    def test_handles_empty_original_list(self):
        """Test handles empty original list."""
        original = []
        keep = [1, 2, 3]

        result = _trim_list(original, keep)

        assert result == []

    def test_preserves_order(self):
        """Test preserves original list order."""
        original = [5, 3, 1, 4, 2]
        keep = [3, 1, 2]

        result = _trim_list(original, keep)

        assert result == [3, 1, 2]


class TestFilterYear:
    """Test _filter_year function."""

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "weeks": [1, 2, 3],
            "positions": ["QB", "RB"],
            "managers": ["Tommy", "Cody"]
        }
    })
    def test_filters_by_year(self):
        """Test filtering options by year."""
        filtered_dict = {
            "years": [2020, 2021, 2022],
            "weeks": list(range(1, 18)),
            "positions": ["QB", "RB", "WR", "TE", "K", "DEF"],
            "managers": ["Tommy", "Cody", "Sach"]
        }

        result = _filter_year(2021, filtered_dict)

        assert result["weeks"] == [1, 2, 3]
        assert result["positions"] == ["QB", "RB"]
        assert result["managers"] == ["Tommy", "Cody"]

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_returns_unchanged_when_year_none(self):
        """Test returns unchanged dict when year is None."""
        filtered_dict = {
            "years": [2021, 2022],
            "weeks": [1, 2, 3],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        original = copy.deepcopy(filtered_dict)

        result = _filter_year(None, filtered_dict)

        assert result == original

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_handles_year_not_in_cache(self):
        """Test handles year not present in cache."""
        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }

        result = _filter_year(2099, filtered_dict)

        # Should return original lists when year not in cache
        assert result["weeks"] == [1, 2]
        assert result["positions"] == ["QB"]
        assert result["managers"] == ["Tommy"]


class TestFilterWeek:
    """Test _filter_week function."""

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "5": {
                "positions": ["QB", "RB"],
                "managers": ["Tommy"]
            }
        }
    })
    def test_filters_by_week(self):
        """Test filtering options by week."""
        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2, 3, 4, 5],
            "positions": ["QB", "RB", "WR"],
            "managers": ["Tommy", "Cody"]
        }

        result = _filter_week(5, 2021, filtered_dict)

        assert result["positions"] == ["QB", "RB"]
        assert result["managers"] == ["Tommy"]

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_returns_unchanged_when_week_none(self):
        """Test returns unchanged dict when week is None."""
        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        original = copy.deepcopy(filtered_dict)

        result = _filter_week(None, 2021, filtered_dict)

        assert result == original


class TestFilterManager:
    """Test _filter_manager function."""

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "managers": ["Tommy", "Cody"],
            "1": {
                "managers": ["Tommy"],
                "Tommy": {
                    "positions": ["QB"]
                }
            },
            "2": {
                "managers": ["Tommy", "Cody"]
            }
        },
        "2022": {
            "managers": ["Cody"],
        }
    })
    def test_filters_years_by_manager(self):
        """Test filters years where manager didn't play."""
        filtered_dict = {
            "years": [2021, 2022],
            "weeks": [1, 2],
            "positions": ["QB", "RB"],
            "managers": ["Tommy", "Cody"]
        }

        result = _filter_manager("Tommy", None, None, filtered_dict)

        assert result["years"] == [2021]
        assert result["weeks"] == [1, 2]  # Both weeks remain when year not specified

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "managers": ["Tommy"],
            "1": {"managers": ["Tommy"]},
            "2": {"managers": ["Tommy"]},
            "3": {"managers": []}
        }
    })
    def test_filters_weeks_by_manager_with_year(self):
        """Test filters weeks where manager didn't play in specific year."""
        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2, 3],
            "positions": ["QB"],
            "managers": ["Tommy", "Cody"]
        }

        result = _filter_manager("Tommy", 2021, None, filtered_dict)

        assert result["weeks"] == [1, 2]

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "5": {
                "managers": ["Tommy"],
                "Tommy": {
                    "positions": ["QB", "RB"]
                }
            }
        }
    })
    def test_filters_positions_by_manager_year_week(self):
        """Test filters positions when year, week, and manager specified."""
        filtered_dict = {
            "years": [2021],
            "weeks": [5],
            "positions": ["QB", "RB", "WR", "TE"],
            "managers": ["Tommy"]
        }

        result = _filter_manager("Tommy", 2021, 5, filtered_dict)

        assert result["positions"] == ["QB", "RB"]

    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_returns_unchanged_when_manager_none(self):
        """Test returns unchanged dict when manager is None."""
        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        original = copy.deepcopy(filtered_dict)

        result = _filter_manager(None, 2021, 1, filtered_dict)

        assert result == original


class TestFilterPlayer:
    """Test _filter_player function."""

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "players": ["Patrick Mahomes", "Travis Kelce"],
            "1": {
                "players": ["Patrick Mahomes"],
                "Tommy": {
                    "players": ["Patrick Mahomes"]
                }
            }
        },
        "2022": {
            "players": ["Travis Kelce"]
        }
    })
    def test_filters_years_by_player(self, mock_fetch_players):
        """Test filters years where player didn't play."""
        mock_fetch_players.return_value = {"Patrick Mahomes": {"position": "QB"}}

        filtered_dict = {
            "years": [2021, 2022],
            "weeks": [1],
            "positions": ["QB", "TE"],
            "managers": ["Tommy"]
        }

        result = _filter_player("Patrick Mahomes", None, None, None, filtered_dict)

        assert result["years"] == [2021]
        assert result["positions"] == ["QB"]

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "players": ["Patrick Mahomes"],
            "1": {"players": ["Patrick Mahomes"]},
            "2": {"players": []},
            "3": {"players": ["Patrick Mahomes"]}
        }
    })
    def test_filters_weeks_by_player_with_year(self, mock_fetch_players):
        """Test filters weeks where player didn't play in specific year."""
        mock_fetch_players.return_value = {"Patrick Mahomes": {"position": "QB"}}

        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2, 3],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }

        result = _filter_player("Patrick Mahomes", 2021, None, None, filtered_dict)

        assert result["weeks"] == [1, 3]

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "1": {
                "players": ["Patrick Mahomes"],
                "Tommy": {"players": ["Patrick Mahomes"]},
                "Cody": {"players": []}
            }
        }
    })
    def test_filters_managers_by_player_year_week(self, mock_fetch_players):
        """Test filters managers who didn't have player in specific year/week."""
        mock_fetch_players.return_value = {"Patrick Mahomes": {"position": "QB"}}

        filtered_dict = {
            "years": [2021],
            "weeks": [1],
            "positions": ["QB"],
            "managers": ["Tommy", "Cody"]
        }

        result = _filter_player("Patrick Mahomes", 2021, None, 1, filtered_dict)

        assert result["managers"] == ["Tommy"]

    @patch('patriot_center_backend.services.valid_options.fetch_players')
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_returns_unchanged_when_player_none(self, mock_fetch_players):
        """Test returns unchanged dict when player is None."""
        mock_fetch_players.return_value = {}

        filtered_dict = {
            "years": [2021],
            "weeks": [1, 2],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        original = copy.deepcopy(filtered_dict)

        result = _filter_player(None, 2021, "Tommy", 1, filtered_dict)

        assert result == original


class TestFetchValidOptions:
    """Test main fetch_valid_options function."""

    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1", 2022: "id2"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    def test_returns_all_options_when_no_args(self):
        """Test returns all options when no arguments provided."""
        result = fetch_valid_options(None, None, None)

        assert result["years"] == [2021, 2022]
        assert result["weeks"] == list(range(1, 18))
        assert result["positions"] == ["QB", "RB", "WR", "TE", "K", "DEF"]
        assert result["managers"] == ["Tommy"]

    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {})
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {})
    @patch('patriot_center_backend.services.valid_options.fetch_players')
    def test_raises_when_week_without_year(self, mock_fetch_players):
        """Test raises error when week specified without year."""
        mock_fetch_players.return_value = {}

        with pytest.raises(ValueError, match="Week specified without a year"):
            fetch_valid_options(None, 5, None)

    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user"})
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "weeks": [1, 2, 3],
            "positions": ["QB", "RB"],
            "managers": ["Tommy"],
            "1": {
                "positions": ["QB"],
                "managers": ["Tommy"]
            }
        }
    })
    @patch('patriot_center_backend.services.valid_options.fetch_players')
    def test_filters_by_year_and_week(self, mock_fetch_players):
        """Test filtering with year and week."""
        mock_fetch_players.return_value = {}

        result = fetch_valid_options(2021, 1, None)

        assert result["weeks"] == [1, 2, 3]
        assert result["positions"] == ["QB"]
        assert result["managers"] == ["Tommy"]

    @patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', {2021: "id1", 2022: "id2"})
    @patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', {"Tommy": "tommy_user", "Cody": "cody_user"})
    @patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', {
        "2021": {
            "managers": ["Tommy"],
            "weeks": [1, 2],
            "positions": ["QB"]
        },
        "2022": {
            "managers": ["Tommy", "Cody"],
            "weeks": [1, 2, 3],
            "positions": ["QB", "RB"]
        }
    })
    @patch('patriot_center_backend.services.valid_options.fetch_players')
    def test_filters_by_manager_only(self, mock_fetch_players):
        """Test filtering by manager across all years."""
        mock_fetch_players.return_value = {}

        result = fetch_valid_options("Tommy", None, None)

        assert sorted(result["years"]) == [2021, 2022]
        assert result["weeks"] == list(range(1, 18))  # No year specified, so all weeks
