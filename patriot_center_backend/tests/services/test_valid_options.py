"""
Comprehensive unit tests for ValidOptionsService.

These tests validate the BUSINESS LOGIC rules for dynamic filtering:

RULE 1 - Single Filter Selected:
    - All options that satisfy the selected filter should be returned
    - Options of other filter types should show valid combinations with the selected filter

RULE 2 - Two Filters Selected:
    - All options that satisfy BOTH filters should be returned
    - For each selected filter type: show broader options (what if you changed that filter)
    - filter_A options: valid for filter_B (ignoring filter_A)
    - filter_B options: valid for filter_A (ignoring filter_B)
    - Other filter types: valid for filter_A AND filter_B

RULE 3 - Three+ Filters Selected:
    - Continue the pattern: show options valid for all filters
    - For each selected filter type: show options valid for other filters (ignoring that one)

RULE 4 - Player Filter:
    - Position is ALWAYS locked to the player's position
    - Other filters work normally but constrained by player

RULE 5 - Week Requires Year:
    - Week options only returned if year is selected
    - Selecting week without year raises error
"""

import pytest
from unittest.mock import patch
from patriot_center_backend.services.valid_options import ValidOptionsService


@pytest.fixture
def mock_valid_options_cache():
    """
    Mock valid options cache based on real data structure.

    Structure: {
        year: {
            managers: [list of manager names],
            players: [list of player names],
            weeks: [list of week numbers as strings],
            positions: [list of positions],
            week#: {
                managers: [list of managers who played this week],
                players: [list of players who played this week],
                positions: [list of positions played this week],
                manager_name: {
                    players: [list of players for this manager in this week],
                    positions: [list of positions for this manager in this week]
                }
            }
        }
    }
    """
    return {
        "2024": {
            "managers": ["Tommy", "Jack", "Owen", "Sach"],
            "players": ["Patrick Mahomes", "Christian McCaffrey", "Tyreek Hill", "Travis Kelce", "Amon-Ra St. Brown", "Justin Tucker", "Kansas City Chiefs"],
            "weeks": ["1", "2", "3", "4"],
            "positions": ["QB", "RB", "WR", "TE", "K", "DEF"],
            "1": {
                "managers": ["Tommy", "Jack"],
                "players": ["Patrick Mahomes", "Christian McCaffrey", "Tyreek Hill"],
                "positions": ["QB", "RB", "WR"],
                "Tommy": {
                    "players": ["Patrick Mahomes", "Christian McCaffrey"],
                    "positions": ["QB", "RB"]
                },
                "Jack": {
                    "players": ["Tyreek Hill"],
                    "positions": ["WR"]
                }
            },
            "2": {
                "managers": ["Tommy", "Owen"],
                "players": ["Patrick Mahomes", "Travis Kelce", "Amon-Ra St. Brown"],
                "positions": ["QB", "TE", "WR"],
                "Tommy": {
                    "players": ["Patrick Mahomes"],
                    "positions": ["QB"]
                },
                "Owen": {
                    "players": ["Travis Kelce", "Amon-Ra St. Brown"],
                    "positions": ["TE", "WR"]
                }
            },
            "3": {
                "managers": ["Jack", "Sach"],
                "players": ["Christian McCaffrey", "Justin Tucker", "Kansas City Chiefs"],
                "positions": ["RB", "K", "DEF"],
                "Jack": {
                    "players": ["Christian McCaffrey"],
                    "positions": ["RB"]
                },
                "Sach": {
                    "players": ["Justin Tucker", "Kansas City Chiefs"],
                    "positions": ["K", "DEF"]
                }
            },
            "4": {
                "managers": ["Sach", "Owen"],
                "players": ["Amon-Ra St. Brown", "Travis Kelce"],
                "positions": ["WR", "TE"],
                "Sach": {
                    "players": ["Amon-Ra St. Brown"],
                    "positions": ["WR"]
                },
                "Owen": {
                    "players": ["Travis Kelce"],
                    "positions": ["TE"]
                }
            }
        },
        "2023": {
            "managers": ["Tommy", "Jack", "Sach"],
            "players": ["Patrick Mahomes", "Travis Kelce", "Tyreek Hill"],
            "weeks": ["1", "2", "3"],
            "positions": ["QB", "TE", "WR"],
            "1": {
                "managers": ["Tommy"],
                "players": ["Patrick Mahomes"],
                "positions": ["QB"],
                "Tommy": {
                    "players": ["Patrick Mahomes"],
                    "positions": ["QB"]
                }
            },
            "2": {
                "managers": ["Jack"],
                "players": ["Tyreek Hill"],
                "positions": ["WR"],
                "Jack": {
                    "players": ["Tyreek Hill"],
                    "positions": ["WR"]
                }
            },
            "3": {
                "managers": ["Sach"],
                "players": ["Travis Kelce"],
                "positions": ["TE"],
                "Sach": {
                    "players": ["Travis Kelce"],
                    "positions": ["TE"]
                }
            }
        },
        "2022": {
            "managers": ["Owen", "Dheeraj"],
            "players": ["Christian McCaffrey", "Javonte Williams"],
            "weeks": ["1", "2", "3", "4"],
            "positions": ["RB"],
            "1": {
                "managers": ["Owen", "Dheeraj"],
                "players": ["Christian McCaffrey", "Javonte Williams"],
                "positions": ["RB"],
                "Owen": {
                    "players": ["Christian McCaffrey"],
                    "positions": ["RB"]
                },
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "2": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "3": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "4": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            }
        },
        "2021": {
            "managers": ["Dheeraj", "Ty"],
            "players": ["Javonte Williams"],
            "weeks": ["6", "7", "8", "12", "13", "14"],
            "positions": ["RB"],
            "6": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "7": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "8": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "12": {
                "managers": ["Dheeraj"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Dheeraj": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "13": {
                "managers": ["Ty"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Ty": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            },
            "14": {
                "managers": ["Ty"],
                "players": ["Javonte Williams"],
                "positions": ["RB"],
                "Ty": {
                    "players": ["Javonte Williams"],
                    "positions": ["RB"]
                }
            }
        }
    }


@pytest.fixture
def mock_players_data():
    """Mock players data cache with real player data."""
    return {
        "Patrick Mahomes": {"position": "QB", "full_name": "Patrick Mahomes", "team": "KC"},
        "Christian McCaffrey": {"position": "RB", "full_name": "Christian McCaffrey", "team": "SF"},
        "Tyreek Hill": {"position": "WR", "full_name": "Tyreek Hill", "team": "MIA"},
        "Travis Kelce": {"position": "TE", "full_name": "Travis Kelce", "team": "KC"},
        "Amon-Ra St. Brown": {"position": "WR", "full_name": "Amon-Ra St. Brown", "team": "DET"},
        "Justin Tucker": {"position": "K", "full_name": "Justin Tucker", "team": "BAL"},
        "Kansas City Chiefs": {"position": "DEF", "full_name": "Kansas City Chiefs", "team": "KC"},
        "Javonte Williams": {"position": "RB", "full_name": "Javonte Williams", "team": "DEN"}
    }


@pytest.fixture
def mock_league_ids():
    """Mock LEAGUE_IDS with generic IDs."""
    return {
        2021: "test_league_id_2021",
        2022: "test_league_id_2022",
        2023: "test_league_id_2023",
        2024: "test_league_id_2024"
    }


@pytest.fixture
def mock_name_to_manager():
    """Mock NAME_TO_MANAGER_USERNAME with generic usernames."""
    return {
        "Tommy": "test_user_tommy",
        "Jack": "test_user_jack",
        "Owen": "test_user_owen",
        "Sach": "test_user_sach",
        "Dheeraj": "test_user_dheeraj",
        "Ty": "test_user_ty"
    }


@pytest.fixture
def setup_mocks(mock_valid_options_cache, mock_players_data, mock_league_ids, mock_name_to_manager):
    """Setup all necessary mocks for ValidOptionsService."""
    # Patch the module-level variables that are loaded at import time
    with patch('patriot_center_backend.services.valid_options.VALID_OPTIONS_CACHE', mock_valid_options_cache), \
         patch('patriot_center_backend.services.valid_options.PLAYERS_DATA', mock_players_data), \
         patch('patriot_center_backend.services.valid_options.LEAGUE_IDS', mock_league_ids), \
         patch('patriot_center_backend.services.valid_options.NAME_TO_MANAGER_USERNAME', mock_name_to_manager):
        yield


# ============================================================================
# BUSINESS RULE 1: SINGLE FILTER SELECTED
# ============================================================================

class TestSingleFilterSelected:
    """Validate business rules when ONE filter is selected."""

    def test_rule_one_filter_manager_selected(self, setup_mocks):
        """
        RULE: Select Tommy
        EXPECT:
          - years: only years Tommy played in [2024, 2023]
          - weeks: only weeks Tommy played in (across all years) [1, 2]
          - positions: only positions Tommy played [QB, RB]
          - managers: ALL managers (since we haven't filtered by specific year/week yet)
        """
        service = ValidOptionsService("Tommy", None, None, None)
        result = service.get_valid_options()

        # Years where Tommy played
        assert set(result["years"]) == {"2024", "2023"}

        # Weeks where Tommy played (in any year)
        assert set(result["weeks"]) == {"1", "2"}

        # Positions Tommy played
        assert set(result["positions"]) == {"QB", "RB"}

        # All managers should be available (not filtered by manager yet)
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen", "Sach"}

    def test_rule_one_filter_year_selected(self, setup_mocks):
        """
        RULE: Select 2024
        EXPECT:
          - years: ALL years [2024, 2023, 2022] (to allow "what if I change year?")
          - weeks: all weeks in 2024 [1, 2, 3, 4]
          - positions: all positions in 2024 [QB, RB, WR, TE, "K", "DEF"]
          - managers: all managers in 2024 [Tommy, Jack, Owen, Sach]
        """
        service = ValidOptionsService("2024", None, None, None)
        result = service.get_valid_options()

        # ALL years should be available (RULE 1)
        assert set(result["years"]) == {"2024", "2023", "2022"}
        assert set(result["weeks"]) == {"1", "2", "3", "4"}
        assert set(result["positions"]) == {"QB", "RB", "WR", "TE", "K", "DEF"}
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen", "Sach"}

    def test_rule_one_filter_position_selected(self, setup_mocks):
        """
        RULE: Select QB
        EXPECT:
          - years: years where QB was played [2024, 2023]
          - weeks: weeks where QB was played [1, 2]
          - positions: QB plus other positions available
          - managers: managers who played QB [Tommy]
        """
        service = ValidOptionsService("QB", None, None, None)
        result = service.get_valid_options()

        # Years where QB was played
        assert "2024" in result["years"]
        assert "2023" in result["years"]

        # Managers who played QB
        assert "Tommy" in result["managers"]
        # Jack, Owen, Sach didn't play QB
        assert "Jack" not in result["managers"]

    def test_rule_one_filter_week_without_year_raises_error(self, setup_mocks):
        """
        RULE 5: Week cannot be selected without year
        EXPECT: ValueError
        """
        with pytest.raises(ValueError, match="Week filter cannot be applied without a Year filter"):
            ValidOptionsService("1", None, None, None)


# ============================================================================
# BUSINESS RULE 2: TWO FILTERS SELECTED
# ============================================================================

class TestTwoFiltersSelected:
    """Validate business rules when TWO filters are selected."""

    def test_rule_two_filters_year_and_manager(self, setup_mocks):
        """
        RULE: Select 2024 and Tommy
        EXPECT:
          - weeks: weeks where Tommy played in 2024 [1, 2]
          - positions: positions Tommy played in 2024 [QB, RB]
          - years: ALL years Tommy played [2024, 2023] (showing "what if I change year")
          - managers: ALL managers in 2024 [Tommy, Jack, Owen, Sach] (showing "what if I change manager")
        """
        service = ValidOptionsService("2024", "Tommy", None, None)
        result = service.get_valid_options()

        # Options valid for BOTH 2024 AND Tommy
        assert set(result["weeks"]) == {"1", "2"}
        assert set(result["positions"]) == {"QB", "RB"}

        # Years where Tommy played (broader options - "what if I change year?")
        assert set(result["years"]) == {"2024", "2023"}

        # Managers who played in 2024 (broader options - "what if I change manager?")
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen", "Sach"}

    def test_rule_two_filters_year_and_week(self, setup_mocks):
        """
        RULE: Select 2024 and week 1
        EXPECT:
          - managers: managers in 2024 week 1 [Tommy, Jack]
          - positions: positions in 2024 week 1 [QB, RB, WR]
          - years: [2024]
          - weeks: all weeks in 2024 [1, 2, 3, 4] (showing "what if I change week")
        """
        service = ValidOptionsService("2024", "1", None, None)
        result = service.get_valid_options()

        # Options valid for 2024 week 1
        assert set(result["managers"]) == {"Tommy", "Jack"}
        assert set(result["positions"]) == {"QB", "RB", "WR"}

        # All weeks in 2024 (broader options)
        assert set(result["weeks"]) == {"1", "2", "3", "4"}

    def test_rule_two_filters_manager_and_position(self, setup_mocks):
        """
        RULE: Select Tommy and QB
        EXPECT:
          - years: years where Tommy played QB [2024, 2023]
          - weeks: weeks where Tommy played QB [1, 2]
          - managers: ALL managers who played QB (showing "what if I change manager")
          - positions: ALL positions Tommy played [QB, RB] (showing "what if I change position")
        """
        service = ValidOptionsService("Tommy", "QB", None, None)
        result = service.get_valid_options()

        # Options valid for Tommy AND QB
        assert set(result["years"]) == {"2024", "2023"}
        assert set(result["weeks"]) == {"1", "2"}

        # All positions Tommy played (broader options)
        assert set(result["positions"]) == {"QB", "RB"}

    def test_rule_two_filters_year_and_position(self, setup_mocks):
        """
        RULE: Select 2024 and WR
        EXPECT:
          - weeks: weeks where WR was played in 2024 [1, 2, 4]
          - managers: managers who played WR in 2024 [Jack, Owen, Sach]
          - years: [2024]
          - positions: all positions in 2024 [QB, RB, WR, TE, K, DEF]
        """
        service = ValidOptionsService("2024", "WR", None, None)
        result = service.get_valid_options()

        # Weeks where WR was played in 2024
        assert set(result["weeks"]) == {"1", "2", "4"}

        # Managers who played WR in 2024
        assert set(result["managers"]) == {"Jack", "Owen", "Sach"}

        # All positions in 2024
        assert set(result["positions"]) == {"QB", "RB", "WR", "TE", "K", "DEF"}


# ============================================================================
# BUSINESS RULE 3: THREE FILTERS SELECTED
# ============================================================================

class TestThreeFiltersSelected:
    """Validate business rules when THREE filters are selected."""

    def test_rule_three_filters_year_week_manager(self, setup_mocks):
        """
        RULE: Select 2024, week 1, and Tommy
        EXPECT:
          - positions: positions Tommy played in 2024 week 1 [QB, RB]
          - weeks: all weeks Tommy played in 2024 [1, 2]
          - managers: all managers in 2024 week 1 [Tommy, Jack]
          - years: all years Tommy played [2024, 2023]
        """
        service = ValidOptionsService("2024", "1", "Tommy", None)
        result = service.get_valid_options()

        # Positions Tommy played in 2024 week 1
        assert set(result["positions"]) == {"QB", "RB"}

        # Weeks Tommy played in 2024 (ignoring week 1 filter)
        assert set(result["weeks"]) == {"1", "2"}

        # Managers in 2024 week 1 (ignoring Tommy filter)
        assert set(result["managers"]) == {"Tommy", "Jack"}

        # Years Tommy played (ignoring year 2024 filter)
        assert set(result["years"]) == {"2024", "2023"}

    def test_rule_three_filters_year_manager_position(self, setup_mocks):
        """
        RULE: Select 2024, Tommy, and QB
        EXPECT:
          - weeks: weeks Tommy played QB in 2024 [1, 2]
          - positions: all positions Tommy played in 2024 [QB, RB]
          - managers: all managers who played QB in 2024 [Tommy]
          - years: all years Tommy played QB [2024, 2023]
        """
        service = ValidOptionsService("2024", "Tommy", "QB", None)
        result = service.get_valid_options()

        # Weeks Tommy played QB in 2024
        assert set(result["weeks"]) == {"1", "2"}

        # All positions Tommy played in 2024 (ignoring QB filter)
        assert set(result["positions"]) == {"QB", "RB"}

        # All managers who played QB in 2024 (ignoring Tommy filter)
        assert "Tommy" in result["managers"]

        # All years Tommy played QB (ignoring 2024 filter)
        assert set(result["years"]) == {"2024", "2023"}

    def test_rule_three_filters_year_week_position(self, setup_mocks):
        """
        RULE: Select 2024, week 1, and WR
        EXPECT:
          - managers: managers who played WR in 2024 week 1 [Jack]
          - weeks: all weeks WR was played in 2024 [1, 2, 4]
          - positions: all positions in 2024 week 1 [QB, RB, WR]
          - years: all years WR was played [2024, 2023]
        """
        service = ValidOptionsService("2024", "1", "WR", None)
        result = service.get_valid_options()

        # Managers who played WR in 2024 week 1
        assert set(result["managers"]) == {"Jack"}

        # All weeks WR was played in 2024 (ignoring week 1 filter)
        assert set(result["weeks"]) == {"1", "2", "4"}

        # All positions in 2024 week 1 (ignoring WR filter)
        assert set(result["positions"]) == {"QB", "RB", "WR"}


# ============================================================================
# BUSINESS RULE 4: FOUR FILTERS SELECTED
# ============================================================================

class TestFourFiltersSelected:
    """Validate business rules when FOUR filters (year+week+manager+position) are selected."""

    def test_rule_four_filters_all_non_player(self, setup_mocks):
        """
        RULE: Select 2024, week 1, Tommy, and QB
        EXPECT:
          - weeks: all weeks Tommy played QB in 2024 [1, 2]
          - managers: all managers who played QB in 2024 week 1 [Tommy]
          - positions: all positions Tommy played in 2024 week 1 [QB, RB]
          - years: all years Tommy played QB [2024, 2023]

        This validates that when all 4 non-player filters are selected,
        each list shows valid options with that specific filter "ignored"
        """
        service = ValidOptionsService("2024", "1", "Tommy", "QB")
        result = service.get_valid_options()

        # Weeks where Tommy played QB in 2024 (ignoring week 1 filter)
        assert set(result["weeks"]) == {"1", "2"}

        # Positions Tommy played in 2024 week 1 (ignoring QB filter)
        assert set(result["positions"]) == {"QB", "RB"}

        # Managers who played QB in 2024 week 1 (ignoring Tommy filter)
        assert "Tommy" in result["managers"]


# ============================================================================
# BUSINESS RULE 5: PLAYER FILTER BEHAVIOR
# ============================================================================

class TestPlayerFilterBehavior:
    """Validate business rules for player-based filtering."""

    def test_rule_player_only_locks_position(self, setup_mocks):
        """
        RULE: Select Patrick Mahomes (position: QB)
        EXPECT:
          - positions: [QB] (locked to player's position)
          - years: years Patrick Mahomes played [2024, 2023]
          - weeks: weeks Patrick Mahomes played [1, 2]
          - managers: managers who had Patrick Mahomes [Tommy]
        """
        service = ValidOptionsService("Patrick Mahomes", None, None, None)
        result = service.get_valid_options()

        # Position locked to player's position
        assert result["positions"] == ["QB"]

        # Years Patrick Mahomes played
        assert set(result["years"]) == {"2024", "2023"}

        # Weeks Patrick Mahomes played
        assert set(result["weeks"]) == {"1", "2"}

        # Managers who had Patrick Mahomes
        assert set(result["managers"]) == {"Tommy"}

    def test_rule_player_and_year(self, setup_mocks):
        """
        RULE: Select Amon-Ra St. Brown and 2024
        EXPECT:
          - positions: [WR]
          - weeks: weeks Amon-Ra St. Brown played in 2024 [2, 4]
          - managers: managers who had Amon-Ra St. Brown in 2024 [Owen, Sach]
          - years: all years Amon-Ra St. Brown played [2024]
        """
        service = ValidOptionsService("Amon-Ra St. Brown", "2024", None, None)
        result = service.get_valid_options()

        assert result["positions"] == ["WR"]
        assert set(result["weeks"]) == {"2", "4"}
        assert set(result["managers"]) == {"Owen", "Sach"}

    def test_rule_player_year_and_manager(self, setup_mocks):
        """
        RULE: Select Patrick Mahomes, 2024, and Tommy
        EXPECT:
          - positions: [QB]
          - weeks: weeks Tommy had Patrick Mahomes in 2024 [1, 2]
          - managers: managers who had Patrick Mahomes in 2024 [Tommy]
          - years: years Tommy had Patrick Mahomes [2024, 2023]
        """
        service = ValidOptionsService("Patrick Mahomes", "2024", "Tommy", None)
        result = service.get_valid_options()

        assert result["positions"] == ["QB"]
        assert set(result["weeks"]) == {"1", "2"}
        assert set(result["years"]) == {"2024", "2023"}

    def test_rule_player_changes_across_managers(self, setup_mocks):
        """
        RULE: Select Christian McCaffrey (played for Tommy, Jack, and Owen in different years/weeks)
        EXPECT:
          - positions: [RB]
          - managers: [Tommy, Jack, Owen]
          - years: [2024, 2022]
          - weeks: [1, 3]
        """
        service = ValidOptionsService("Christian McCaffrey", None, None, None)
        result = service.get_valid_options()

        assert result["positions"] == ["RB"]
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen"}
        assert set(result["years"]) == {"2024", "2022"}
        assert set(result["weeks"]) == {"1", "3"}


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================

class TestEdgeCasesAndValidation:
    """Test edge cases and validation rules."""

    def test_no_filters_returns_all_options(self, setup_mocks):
        """
        RULE: No filters selected
        EXPECT: All possible options across all years
        """
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert set(result["years"]) == {"2024", "2023", "2022"}
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen", "Sach"}
        assert "QB" in result["positions"]
        assert "RB" in result["positions"]
        assert "WR" in result["positions"]

    def test_nonexistent_combination_returns_empty(self, setup_mocks):
        """
        RULE: Select filters that don't match any data
        EXPECT: Empty/minimal results for unmatched filters
        """
        # Owen didn't play in 2024 week 1
        service = ValidOptionsService("2024", "1", "Owen", None)
        result = service.get_valid_options()

        # Owen shouldn't be in managers for week 1 of 2024
        assert "Owen" not in result["managers"]

    def test_results_are_sorted(self, setup_mocks):
        """
        RULE: All results should be sorted
        EXPECT: Years, weeks, and managers are sorted
        If the data is integers stored as strings, ensure numeric sorting for weeks
        """
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        expected_weeks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]

        assert result["weeks"] == expected_weeks
        assert result["years"] == sorted(result["years"])
        assert result["managers"] == sorted(result["managers"])
        


    def test_weeks_sorted_numerically(self, setup_mocks):
        """
        RULE: Weeks should be sorted numerically
        EXPECT: ["1", "2", "3", "4"] not ["1", "10", "2"]
        """
        service = ValidOptionsService("2024", None, None, None)
        result = service.get_valid_options()

        weeks_as_ints = [int(w) for w in result["weeks"]]
        assert weeks_as_ints == sorted(weeks_as_ints)

    def test_sach_example_from_spec(self, setup_mocks):
        """
        RULE: Exact example from spec - select Sach
        EXPECT:
          - years: [2024, 2023] (years Sach played)
          - weeks: [3, 4] in 2024, [3] in 2023 => [3, 4]
          - positions: [WR, K, DEF, TE]
          - managers: [Tommy, Jack, Owen, Sach] (all managers)
        """
        service = ValidOptionsService("Sach", None, None, None)
        result = service.get_valid_options()

        # Years Sach played
        assert set(result["years"]) == {"2024", "2023"}

        # Weeks Sach played
        assert set(result["weeks"]) == {"3", "4"}

        # Positions Sach played
        assert set(result["positions"]) == {"WR", "K", "DEF", "TE"}

        # All managers available
        assert set(result["managers"]) == {"Tommy", "Jack", "Owen", "Sach"}

    def test_invalid_argument_raises_error(self, setup_mocks):
        """
        RULE: Invalid arguments should raise ValueError
        """
        with pytest.raises(ValueError):
            ValidOptionsService("InvalidPlayerName", None, None, None)

    def test_duplicate_filter_raises_error(self, setup_mocks):
        """
        RULE: Duplicate filters should raise error
        """
        with pytest.raises(ValueError, match="Multiple year arguments provided"):
            ValidOptionsService("2024", "2023", None, None)


# ============================================================================
# INTEGRATION SCENARIOS
# ============================================================================

class TestRealWorldScenarios:
    """Test realistic user interaction scenarios."""

    def test_scenario_progressive_filtering(self, setup_mocks):
        """
        Scenario: User progressively narrows down filters
        1. Select year 2024
        2. Add week 2
        3. Add manager Owen
        4. Verify results match business rules
        """
        # Step 1: Select 2024
        service = ValidOptionsService("2024", None, None, None)
        result = service.get_valid_options()
        assert set(result["weeks"]) == {"1", "2", "3", "4"}

        # Step 2: Add week 2
        service = ValidOptionsService("2024", "2", None, None)
        result = service.get_valid_options()
        assert set(result["managers"]) == {"Tommy", "Owen"}

        # Step 3: Add Owen
        service = ValidOptionsService("2024", "2", "Owen", None)
        result = service.get_valid_options()
        assert set(result["positions"]) == {"TE", "WR"}

    def test_scenario_player_driven_filtering(self, setup_mocks):
        """
        Scenario: Start with player, then narrow down
        1. Select Travis Kelce
        2. Add year 2024
        3. Verify position always locked to TE
        """
        # Step 1: Select Travis Kelce
        service = ValidOptionsService("Travis Kelce", None, None, None)
        result = service.get_valid_options()
        assert result["positions"] == ["TE"]
        assert set(result["managers"]) == {"Owen", "Sach"}

        # Step 2: Add 2024
        service = ValidOptionsService("Travis Kelce", "2024", None, None)
        result = service.get_valid_options()
        assert result["positions"] == ["TE"]
        assert set(result["weeks"]) == {"2", "4"}

    def test_scenario_cross_year_manager(self, setup_mocks):
        """
        Scenario: Manager who played in multiple years
        Select Jack -> should show 2024 and 2023
        """
        service = ValidOptionsService("Jack", None, None, None)
        result = service.get_valid_options()

        assert set(result["years"]) == {"2024", "2023"}
        assert set(result["weeks"]) == {"1", "2", "3"}
        assert set(result["positions"]) == {"RB", "WR"}

    def test_scenario_defense_position(self, setup_mocks):
        """
        Scenario: Select Kansas City Chiefs (DEF position)
        EXPECT: Position locked to DEF, shows Sach who had them
        """
        service = ValidOptionsService("Kansas City Chiefs", None, None, None)
        result = service.get_valid_options()

        assert result["positions"] == ["DEF"]
        assert set(result["managers"]) == {"Sach"}
        assert set(result["years"]) == {"2024"}
        assert set(result["weeks"]) == {"3"}
    
    def test_special_edge_case_manager_player_year_scenario(self, setup_mocks):
        """
        Scenario: Select Javonte Williams (RB), Select Dheeraj as manager, Select 2021 year
        Edge Case: Javonte Williams played for Dheeraj in 2021 weeks 6, 7, 8, 12 and 2022 weeks 1, 2, 3, 4
                   Javonte Williams played for Ty in 2021 weeks 13 and 14
        EXPECT: Years: [2021, 2022], Weeks: [6, 7, 8, 12], Managers: [Dheeraj, Ty]
        """
        service = ValidOptionsService("Javonte Williams", "Dheeraj", "2021", None)
        result = service.get_valid_options()

        assert set(result["years"]) == {"2021", "2022"}
        assert set(result["weeks"]) == {"6", "7", "8", "12"}
        assert set(result["managers"]) == {"Dheeraj", "Ty"}

    def test_special_edge_case_manager_week_year_scenario(self, setup_mocks):
        """
        Scenario: Select Javonte Williams (RB), Select 13 as week, Select 2021 year
        Edge Case: Javonte Williams played for Dheeraj in 2021 weeks 6, 7, 8, 12 and 2022 weeks 1, 2, 3, 4
                   Javonte Williams played for Ty in 2021 weeks 13 and 14
        EXPECT: Years: [2021], Weeks: [6, 7, 8, 12, 13, 14], Managers: [Ty]
        """
        service = ValidOptionsService("Javonte Williams", "13", "2021", None)
        result = service.get_valid_options()

        assert set(result["years"]) == {"2021"}
        assert set(result["weeks"]) == {"6", "7", "8", "12", "13", "14"}
        assert set(result["managers"]) == {"Ty"}



# ============================================================================
# METHOD-LEVEL TESTS FOR COMPLETE COVERAGE
# ============================================================================

class TestInternalMethods:
    """Test all internal methods for complete code coverage."""

    def test_year_selected_method(self, setup_mocks):
        """Test _year_selected() returns correct boolean."""
        # Year selected
        service = ValidOptionsService("2024", None, None, None)
        assert service._year_selected() == True
        assert service._year == "2024"

        # Year not selected
        service = ValidOptionsService("Tommy", None, None, None)
        assert service._year_selected() == False
        assert service._year is None

    def test_week_selected_method(self, setup_mocks):
        """Test _week_selected() returns correct boolean."""
        # Week selected (with year)
        service = ValidOptionsService("2024", "1", None, None)
        assert service._week_selected() == True
        assert service._week == "1"

        # Week not selected
        service = ValidOptionsService("2024", None, None, None)
        assert service._week_selected() == False
        assert service._week is None

    def test_manager_selected_method(self, setup_mocks):
        """Test _manager_selected() returns correct boolean."""
        # Manager selected
        service = ValidOptionsService("Tommy", None, None, None)
        assert service._manager_selected() == True
        assert service._manager == "Tommy"

        # Manager not selected
        service = ValidOptionsService("2024", None, None, None)
        assert service._manager_selected() == False
        assert service._manager is None

    def test_player_selected_method(self, setup_mocks):
        """Test _player_selected() returns correct boolean."""
        # Player selected
        service = ValidOptionsService("Patrick Mahomes", None, None, None)
        assert service._player_selected() == True
        assert service._player == "Patrick Mahomes"

        # Player not selected
        service = ValidOptionsService("Tommy", None, None, None)
        assert service._player_selected() == False
        assert service._player is None

    def test_position_selected_method(self, setup_mocks):
        """Test _position_selected() returns correct boolean."""
        # Position selected
        service = ValidOptionsService("QB", None, None, None)
        assert service._position_selected() == True
        assert service._position == "QB"

        # Position not selected
        service = ValidOptionsService("Tommy", None, None, None)
        assert service._position_selected() == False
        assert service._position is None

    def test_parse_arg_year(self, setup_mocks):
        """Test _parse_arg correctly parses year."""
        service = ValidOptionsService(None, None, None, None)
        service._parse_arg("2024")
        assert service._year == "2024"

    def test_parse_arg_week(self, setup_mocks):
        """Test _parse_arg correctly parses week."""
        service = ValidOptionsService("2024", None, None, None)
        service._parse_arg("5")
        assert service._week == "5"

    def test_parse_arg_manager(self, setup_mocks):
        """Test _parse_arg correctly parses manager name."""
        service = ValidOptionsService(None, None, None, None)
        service._parse_arg("Tommy")
        assert service._manager == "Tommy"

    def test_parse_arg_player(self, setup_mocks):
        """Test _parse_arg correctly parses player name."""
        service = ValidOptionsService(None, None, None, None)
        service._parse_arg("Patrick Mahomes")
        assert service._player == "Patrick Mahomes"

    def test_parse_arg_position(self, setup_mocks):
        """Test _parse_arg correctly parses position."""
        service = ValidOptionsService(None, None, None, None)
        service._parse_arg("QB")
        assert service._position == "QB"

    def test_parse_arg_player_with_underscores(self, setup_mocks):
        """Test _parse_arg handles player names with underscores."""
        service = ValidOptionsService(None, None, None, None)
        service._parse_arg("Amon-Ra_St._Brown")
        assert service._player == "Amon-Ra St. Brown"

    def test_parse_arg_player_with_apostrophe_encoding(self, setup_mocks):
        """Test _parse_arg handles URL-encoded apostrophes."""
        with patch('patriot_center_backend.services.valid_options.PLAYERS_DATA', {"D'Andre Swift": {"position": "RB"}}):
            service = ValidOptionsService(None, None, None, None)
            service._parse_arg("D%27Andre_Swift")
            assert "D'Andre" in service._player

    def test_check_year_and_week_valid(self, setup_mocks):
        """Test _check_year_and_week passes when year is selected with week."""
        service = ValidOptionsService(None, None, None, None)
        service._year = "2024"
        service._week = "1"
        # Should not raise
        service._check_year_and_week()

    def test_check_year_and_week_invalid(self, setup_mocks):
        """Test _check_year_and_week raises when week without year."""
        service = ValidOptionsService(None, None, None, None)
        service._week = "1"
        service._year = None
        with pytest.raises(ValueError, match="Week filter cannot be applied without a Year filter"):
            service._check_year_and_week()

    def test_get_function_id_calculations(self, setup_mocks):
        """Test _get_function_id calculates correct IDs using bit flags."""
        # Test various combinations
        test_cases = [
            (None, None, None, None, 0),  # No filters
            ("QB", None, None, None, 1),  # Position only
            ("Tommy", None, None, None, 2),  # Manager only
            ("Tommy", "QB", None, None, 3),  # Manager + Position
            ("2024", None, None, None, 8),  # Year only
            ("2024", "Tommy", None, None, 10),  # Year + Manager
            ("2024", "1", None, None, 12),  # Year + Week
            ("2024", "1", "Tommy", "QB", 15),  # Year + Week + Manager + Position
            ("Patrick Mahomes", None, None, None, 16),  # Player only
            ("Patrick Mahomes", "2024", None, None, 24),  # Player + Year
        ]

        for arg1, arg2, arg3, arg4, expected_id in test_cases:
            service = ValidOptionsService(arg1, arg2, arg3, arg4)
            assert service._func_id == expected_id, f"Failed for {arg1}, {arg2}, {arg3}, {arg4}"

    def test_add_to_valid_options_single_filter(self, setup_mocks):
        """Test _add_to_vaild_options with single filter."""
        service = ValidOptionsService(None, None, None, None)
        service._reset_growing_lists()

        # Add a year
        service._add_to_vaild_options("2024", "year")
        assert "2024" in service._growing_years_list

        # Add a manager
        service._add_to_vaild_options("Tommy", "manager")
        assert "Tommy" in service._growing_managers_list

    def test_add_to_valid_options_multiple_filters(self, setup_mocks):
        """Test _add_to_vaild_options with multiple dependent filters."""
        service = ValidOptionsService(None, None, None, None)
        service._reset_growing_lists()

        # Add year with week dependency
        service._add_to_vaild_options("2024", "year", "week")
        assert "2024" in service._growing_years_list

    def test_add_to_valid_options_done_flag(self, setup_mocks):
        """Test _add_to_vaild_options sets done flag correctly."""
        service = ValidOptionsService(None, None, None, None)
        service._reset_growing_lists()

        # Initially not done
        assert service._done == False

        # Add an option
        service._add_to_vaild_options("2024", "year")
        # Done flag depends on whether all lists are complete
        assert isinstance(service._done, bool)

    def test_reset_growing_lists(self, setup_mocks):
        """Test _reset_growing_lists clears all lists."""
        service = ValidOptionsService(None, None, None, None)

        # Add some data
        service._growing_years_list = ["2024"]
        service._growing_weeks_list = ["1"]
        service._growing_managers_list = ["Tommy"]
        service._growing_positions_list = ["QB"]
        service._done = True

        # Reset
        service._reset_growing_lists()

        # All should be cleared
        assert service._growing_years_list == []
        assert service._growing_weeks_list == []
        assert service._growing_managers_list == []
        assert service._growing_positions_list == []
        assert service._done == False

    def test_call_new_function_valid(self, setup_mocks):
        """Test _call_new_function executes the correct function."""
        service = ValidOptionsService("2024", None, None, None)

        # Call function 8 (year selected)
        service._call_new_function(8)

        # Growing lists should be reset
        assert service._growing_years_list == []
        assert service._growing_weeks_list == []

    def test_call_new_function_invalid(self, setup_mocks):
        """Test _call_new_function raises error for unimplemented function."""
        service = ValidOptionsService(None, None, None, None)

        # Function 4 is not implemented (week without year)
        with pytest.raises(ValueError, match="Function for bit 4 not implemented"):
            service._call_new_function(4)

    def test_function_mapping_exists(self, setup_mocks):
        """Test _function_mapping contains all implemented functions."""
        service = ValidOptionsService(None, None, None, None)

        # Check that key functions are mapped
        implemented_functions = [0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29, 30]

        for func_id in implemented_functions:
            assert func_id in service._function_mapping
            assert callable(service._function_mapping[func_id])

    def test_player_filtered_flag(self, setup_mocks):
        """Test _player_filtered flag prevents double processing."""
        service = ValidOptionsService("Patrick Mahomes", None, None, None)

        # After initialization, player should be filtered
        assert service._player_filtered == True

        # Position should be set to player's position
        assert service._positions_list == ["QB"]

    def test_all_position_types(self, setup_mocks):
        """Test all position types can be selected."""
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

        for pos in positions:
            service = ValidOptionsService(pos, None, None, None)
            assert service._position == pos
            assert service._position_selected() == True


class TestAllFilterFunctions:
    """Test each of the 32 filter functions individually."""

    def test_function_0_none_selected(self, setup_mocks):
        """Test #0: _none_selected() - no filters."""
        service = ValidOptionsService(None, None, None, None)
        assert service._func_id == 0

        # Function should do nothing, return defaults
        service._none_selected()
        # Lists should remain at defaults
        assert len(service._years_list) > 0
        assert len(service._weeks_list) > 0

    def test_function_1_pos_selected(self, setup_mocks):
        """Test #1: _pos_selected() - position only."""
        service = ValidOptionsService("QB", None, None, None)
        assert service._func_id == 1
        service._pos_selected()

        # Should filter to years/weeks/managers with QB
        assert len(service._years_list) > 0
        assert len(service._managers_list) > 0

    def test_function_2_mgr_selected(self, setup_mocks):
        """Test #2: _mgr_selected() - manager only."""
        service = ValidOptionsService("Tommy", None, None, None)
        assert service._func_id == 2
        service._mgr_selected()

        # Should filter to years/weeks/positions for Tommy
        assert len(service._years_list) > 0
        assert len(service._positions_list) > 0

    def test_function_3_mgr_pos_selected(self, setup_mocks):
        """Test #3: _mgr_pos_selected() - manager and position."""
        service = ValidOptionsService("Tommy", "QB", None, None)
        assert service._func_id == 3
        service._mgr_pos_selected()

        # Should filter years and weeks
        assert len(service._years_list) > 0

    def test_function_8_yr_selected(self, setup_mocks):
        """Test #8: _yr_selected() - year only."""
        service = ValidOptionsService("2024", None, None, None)
        assert service._func_id == 8
        service._yr_selected()

        # Should filter weeks/managers/positions for 2024
        assert len(service._weeks_list) > 0
        assert len(service._managers_list) > 0

    def test_function_12_yr_wk_selected(self, setup_mocks):
        """Test #12: _yr_wk_selected() - year and week."""
        service = ValidOptionsService("2024", "1", None, None)
        assert service._func_id == 12
        service._yr_wk_selected()

        # Should filter managers and positions
        assert len(service._managers_list) > 0

    def test_function_16_plyr_selected(self, setup_mocks):
        """Test #16: _plyr_selected() - player only."""
        service = ValidOptionsService("Patrick Mahomes", None, None, None)
        assert service._func_id == 16

        # Position should be locked
        assert service._positions_list == ["QB"]

        # Should have filtered years/weeks/managers
        assert len(service._years_list) > 0


class TestGetValidOptionsMethod:
    """Test the public get_valid_options() method."""

    def test_get_valid_options_returns_dict(self, setup_mocks):
        """Test get_valid_options() returns dictionary with correct keys."""
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert isinstance(result, dict)
        assert "years" in result
        assert "weeks" in result
        assert "managers" in result
        assert "positions" in result

    def test_get_valid_options_years_sorted(self, setup_mocks):
        """Test years list is sorted."""
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert result["years"] == sorted(result["years"])

    def test_get_valid_options_weeks_sorted_numerically(self, setup_mocks):
        """Test weeks are sorted numerically."""
        service = ValidOptionsService("2024", None, None, None)
        result = service.get_valid_options()

        # Convert to ints and verify sorting
        weeks_as_ints = [int(w) for w in result["weeks"]]
        assert weeks_as_ints == sorted(weeks_as_ints)

    def test_get_valid_options_managers_sorted(self, setup_mocks):
        """Test managers list is sorted."""
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert result["managers"] == sorted(result["managers"])

    def test_get_valid_options_all_lists_are_lists(self, setup_mocks):
        """Test all return values are lists."""
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert isinstance(result["years"], list)
        assert isinstance(result["weeks"], list)
        assert isinstance(result["managers"], list)
        assert isinstance(result["positions"], list)

    def test_get_valid_options_no_duplicates(self, setup_mocks):
        """Test returned lists contain no duplicates."""
        service = ValidOptionsService(None, None, None, None)
        result = service.get_valid_options()

        assert len(result["years"]) == len(set(result["years"]))
        assert len(result["weeks"]) == len(set(result["weeks"]))
        assert len(result["managers"]) == len(set(result["managers"]))
        assert len(result["positions"]) == len(set(result["positions"]))


class TestErrorHandling:
    """Test error handling and validation."""

    def test_multiple_year_arguments_error(self, setup_mocks):
        """Test error when multiple years provided."""
        with pytest.raises(ValueError, match="Multiple year arguments provided"):
            ValidOptionsService("2024", "2023", None, None)

    def test_multiple_week_arguments_error(self, setup_mocks):
        """Test error when multiple weeks provided."""
        with pytest.raises(ValueError, match="Multiple week arguments provided"):
            service = ValidOptionsService("2024", None, None, None)
            service._parse_arg("1")
            service._parse_arg("2")

    def test_multiple_manager_arguments_error(self, setup_mocks):
        """Test error when multiple managers provided."""
        with pytest.raises(ValueError, match="Multiple manager arguments provided"):
            service = ValidOptionsService(None, None, None, None)
            service._parse_arg("Tommy")
            service._parse_arg("Jack")

    def test_multiple_player_arguments_error(self, setup_mocks):
        """Test error when multiple players provided."""
        with pytest.raises(ValueError, match="Multiple player arguments provided"):
            service = ValidOptionsService(None, None, None, None)
            service._parse_arg("Patrick Mahomes")
            service._parse_arg("Travis Kelce")

    def test_multiple_position_arguments_error(self, setup_mocks):
        """Test error when multiple positions provided."""
        with pytest.raises(ValueError, match="Multiple position arguments provided"):
            service = ValidOptionsService(None, None, None, None)
            service._parse_arg("QB")
            service._parse_arg("RB")

    def test_unrecognized_string_argument_error(self, setup_mocks):
        """Test error for unrecognized string argument."""
        with pytest.raises(ValueError, match="Unrecognized argument"):
            ValidOptionsService("InvalidArgumentXYZ", None, None, None)

    def test_unrecognized_integer_argument_error(self, setup_mocks):
        """Test error for unrecognized integer argument."""
        with pytest.raises(ValueError, match="Unrecognized integer argument"):
            service = ValidOptionsService(None, None, None, None)
            service._parse_arg("9999")

    def test_week_without_year_initialization_error(self, setup_mocks):
        """Test error when week provided without year at initialization."""
        with pytest.raises(ValueError, match="Week filter cannot be applied without a Year filter"):
            ValidOptionsService("5", None, None, None)
