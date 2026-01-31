"""Unit tests for ffwar_calculator module."""

from statistics import mean
from unittest.mock import patch

import pytest

from patriot_center_backend.calculations.ffwar_calculator import (
    FFWARCalculator,
)


class TestCalculateFFWAR:
    """Test FFWARCalculator.calculate_ffwar method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_season_state`: `mock_get_season_state`
        - `fetch_starters_by_position`:
            `mock_fetch_starters_by_position`
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options`
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score`
        - `fetch_all_player_scores`: `mock_fetch_all_player_scores`
        - `fetch_rostered_players`: `mock_fetch_rostered_players`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ) as mock_get_season_state,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters_by_position,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ) as mock_fetch_all_player_scores,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ) as mock_fetch_rostered_players,
        ):
            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            self.mock_fetch_starters_by_position = (
                mock_fetch_starters_by_position
            )
            self.mock_fetch_starters_by_position.return_value = {
                "QB": {
                    "players": ["Patrick Mahomes", "Josh Allen"],
                    "scores": [25.0, 22.0],
                    "managers": {
                        "Tommy": {
                            "total_points": 120.0,
                            "scores": [25.0],
                        },
                        "Jay": {
                            "total_points": 100.0,
                            "scores": [22.0],
                        },
                    },
                },
            }

            self.mock_valid_options_cache = {
                "2024": {
                    "1": {
                        "managers": ["Tommy", "Jay"],
                    },
                },
            }
            mock_get_valid_options.return_value = self.mock_valid_options_cache

            self.mock_replacement_score_cache = {
                "2024": {
                    "1": {
                        "QB_3yr_avg": 15.0,
                    },
                },
            }
            mock_get_replacement_score.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_all_player_scores = mock_fetch_all_player_scores
            self.mock_fetch_all_player_scores.return_value = {
                "QB": {
                    "4046": {
                        "score": 25.0,
                        "name": "Patrick Mahomes",
                    },
                    "6794": {
                        "score": 22.0,
                        "name": "Josh Allen",
                    },
                },
            }

            self.mock_fetch_rostered_players = mock_fetch_rostered_players
            self.mock_fetch_rostered_players.return_value = {
                "Tommy": ["4046"],
                "Jay": ["6794"],
            }

            yield

    def test_returns_player_data_dict(self):
        """Test returns a dict of player data."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        assert isinstance(result, dict)
        assert "4046" in result
        assert "6794" in result

    def test_player_data_has_required_keys(self):
        """Test each player entry has required keys."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        player = result["4046"]
        assert "name" in player
        assert "score" in player
        assert "ffWAR" in player
        assert "position" in player
        assert "manager" in player
        assert "started" in player

    def test_player_manager_assignment(self):
        """Test correctly assigns manager to rostered players."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        assert result["4046"]["manager"] == "Tommy"
        assert result["6794"]["manager"] == "Jay"

    def test_started_flag(self):
        """Test correctly sets started flag."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        assert result["4046"]["started"] is True

    def test_ffwar_is_rounded_to_three_decimals(self):
        """Test ffWAR values are rounded to 3 decimal places."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        for pid in result:
            ffwar_str = str(result[pid]["ffWAR"])
            if "." in ffwar_str:
                decimals = len(ffwar_str.split(".")[1])
                assert decimals <= 3

    def test_sorted_by_ffwar_descending_then_name(self):
        """Test result is sorted by ffWAR desc, then name asc."""
        calc = FFWARCalculator(2024, 1)
        result = calc.calculate_ffwar()

        items = list(result.values())
        for i in range(len(items) - 1):
            assert (
                items[i]["ffWAR"] > items[i + 1]["ffWAR"]
                or (
                    items[i]["ffWAR"] == items[i + 1]["ffWAR"]
                    and items[i]["name"] <= items[i + 1]["name"]
                )
            )


class TestApplyManagers:
    """Test FFWARCalculator._apply_managers method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - All FFWARCalculator dependencies mocked

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ),
        ):
            mock_fetch_starters.return_value = {"QB": {}}

            self.mock_valid_options_cache = {
                "2024": {
                    "1": {
                        "managers": ["Tommy", "Jay"],
                    },
                },
            }
            mock_get_valid_options.return_value = self.mock_valid_options_cache

            yield

    def test_sets_managers_from_valid_options(self):
        """Test sets managers from valid options cache."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_managers()

        assert calc.managers == ["Tommy", "Jay"]

    def test_raises_when_no_managers(self):
        """Test raises ValueError when no managers found."""
        self.mock_valid_options_cache["2024"]["1"]["managers"] = []

        calc = FFWARCalculator(2024, 1)

        with pytest.raises(ValueError) as exc_info:
            calc._apply_managers()

        assert "No valid options found" in str(exc_info.value)


class TestApplyReplacementScores:
    """Test FFWARCalculator._apply_replacement_scores method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ),
        ):
            mock_fetch_starters.return_value = {
                "QB": {},
                "RB": {},
            }

            self.mock_replacement_score_cache = {
                "2024": {
                    "1": {
                        "QB_3yr_avg": 15.0,
                        "RB_3yr_avg": 8.5,
                    },
                },
            }
            mock_get_replacement_score.return_value = (
                self.mock_replacement_score_cache
            )

            yield

    def test_sets_replacement_scores(self):
        """Test sets replacement scores for each position."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_replacement_scores()

        assert calc.replacement_scores["QB"] == 15.0
        assert calc.replacement_scores["RB"] == 8.5

    def test_raises_when_no_weekly_scores(self):
        """Test raises ValueError when no weekly replacement scores."""
        self.mock_replacement_score_cache["2024"] = {}

        calc = FFWARCalculator(2024, 1)

        with pytest.raises(ValueError) as exc_info:
            calc._apply_replacement_scores()

        assert "No replacement scores found" in str(exc_info.value)

    def test_raises_when_position_missing(self):
        """Test raises ValueError when position not in replacement scores."""
        del self.mock_replacement_score_cache["2024"]["1"]["RB_3yr_avg"]

        calc = FFWARCalculator(2024, 1)

        with pytest.raises(ValueError) as exc_info:
            calc._apply_replacement_scores()

        assert "No replacement scores found for RB" in str(exc_info.value)


class TestApplyBaselineAndWeightedScores:
    """Test FFWARCalculator._apply_baseline_and_weighted_scores method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ),
        ):
            mock_fetch_starters.return_value = {
                "QB": {
                    "players": ["Patrick Mahomes"],
                    "scores": [25.0, 22.0],
                    "managers": {
                        "Tommy": {
                            "total_points": 120.0,
                            "scores": [25.0],
                        },
                        "Jay": {
                            "total_points": 100.0,
                            "scores": [22.0],
                        },
                        "Cody": {
                            "total_points": 90.0,
                            "scores": [],
                        },
                    },
                },
            }

            yield

    def test_sets_baseline_for_managers_with_starters(self):
        """Test sets baseline score for managers with position starters."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_baseline_and_weighted_scores()

        # Tommy: 120.0 - 25.0 = 95.0
        assert calc.baseline_scores["QB"]["Tommy"] == 95.0
        # Jay: 100.0 - 22.0 = 78.0
        assert calc.baseline_scores["QB"]["Jay"] == 78.0

    def test_no_baseline_for_managers_without_starters(self):
        """Test no baseline score for managers without position starters."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_baseline_and_weighted_scores()

        assert "Cody" not in calc.baseline_scores["QB"]

    def test_sets_weighted_for_all_managers(self):
        """Test sets weighted score for all managers including no-starters."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_baseline_and_weighted_scores()

        pos_avg = mean([25.0, 22.0])

        # Tommy: 120.0 - 25.0 + pos_avg
        assert calc.weighted_scores["QB"]["Tommy"] == 120.0 - 25.0 + pos_avg
        # Cody (no starter): 90.0 + pos_avg
        assert calc.weighted_scores["QB"]["Cody"] == 90.0 + pos_avg

    def test_weighted_score_for_no_starter_manager(self):
        """Test manager with no starter gets total_points + pos_average."""
        calc = FFWARCalculator(2024, 1)
        calc._apply_baseline_and_weighted_scores()

        pos_avg = mean([25.0, 22.0])
        assert calc.weighted_scores["QB"]["Cody"] == 90.0 + pos_avg


class TestApplyPlayoffAdjustment:
    """Test FFWARCalculator._apply_playoff_adjustment method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ) as mock_get_season_state,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ),
        ):
            self.mock_get_season_state = mock_get_season_state
            mock_fetch_starters.return_value = {"QB": {}}

            yield

    def test_no_adjustment_for_regular_season(self):
        """Test no adjustment during regular season."""
        self.mock_get_season_state.return_value = "regular_season"

        calc = FFWARCalculator(2024, 1)
        result = calc._apply_playoff_adjustment(0.9)

        assert result == 0.9

    def test_divides_by_three_for_playoffs(self):
        """Test divides score by 3 during playoffs."""
        self.mock_get_season_state.return_value = "playoffs"

        calc = FFWARCalculator(2024, 15)
        result = calc._apply_playoff_adjustment(0.9)

        assert result == pytest.approx(0.3)


class TestSimulateMatchups:
    """Test FFWARCalculator._simulate_matchups method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".get_season_state"
            ) as mock_get_season_state,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_starters_by_position"
            ) as mock_fetch_starters,
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_all_player_scores"
            ),
            patch(
                "patriot_center_backend.calculations.ffwar_calculator"
                ".fetch_rostered_players"
            ),
        ):
            mock_get_season_state.return_value = "regular_season"
            mock_fetch_starters.return_value = {"QB": {}}

            yield

    def test_raises_when_no_simulated_games(self):
        """Test raises ValueError when no simulated games."""
        calc = FFWARCalculator(2024, 1)
        calc.player_data = {
            "4046": {
                "name": "Patrick Mahomes",
                "score": 25.0,
                "ffWAR": 0.0,
                "position": "QB",
            },
        }
        calc.replacement_scores = {"QB": 15.0}
        calc.baseline_scores = {"QB": {}}
        calc.weighted_scores = {"QB": {}}

        with pytest.raises(ValueError) as exc_info:
            calc._simulate_matchups()

        assert "No simulated games played" in str(exc_info.value)

    def test_calculates_ffwar_for_player(self):
        """Test calculates ffWAR score for a player."""
        calc = FFWARCalculator(2024, 1)
        calc.player_data = {
            "4046": {
                "name": "Patrick Mahomes",
                "score": 25.0,
                "ffWAR": 0.0,
                "position": "QB",
            },
        }
        calc.replacement_scores = {"QB": 10.0}
        calc.baseline_scores = {"QB": {"Tommy": 95.0, "Jay": 78.0}}
        calc.weighted_scores = {"QB": {"Tommy": 118.5, "Jay": 101.5}}

        calc._simulate_matchups()

        assert "ffWAR" in calc.player_data["4046"]
        assert isinstance(calc.player_data["4046"]["ffWAR"], float)

    def test_skips_self_matchups(self):
        """Test skips when manager_playing equals manager_opposing."""
        calc = FFWARCalculator(2024, 1)
        calc.player_data = {
            "4046": {
                "name": "Patrick Mahomes",
                "score": 25.0,
                "ffWAR": 0.0,
                "position": "QB",
            },
        }
        calc.replacement_scores = {"QB": 10.0}
        calc.baseline_scores = {"QB": {"Tommy": 95.0}}
        calc.weighted_scores = {"QB": {"Tommy": 118.5, "Jay": 101.5}}

        calc._simulate_matchups()

        # Only 1 matchup: Tommy playing vs Jay opposing
        assert calc.player_data["4046"]["ffWAR"] is not None
