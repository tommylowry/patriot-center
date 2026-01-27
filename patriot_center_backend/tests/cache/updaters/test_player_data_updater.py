"""Unit tests for player_data_updater module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.player_data_updater import (
    _calculate_ffwar_position,
    _fetch_ffwar,
    _get_all_player_scores,
    _get_all_rostered_players,
    update_player_data_cache,
)


class TestUpdatePlayerDataCache:
    """Test update_player_data_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_data_cache`: `mock_get_player_data_cache`
        - `_fetch_ffwar`: `mock_fetch_ffwar`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".CACHE_MANAGER.get_player_data_cache"
            ) as mock_get_player_data_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                "._fetch_ffwar"
            ) as mock_fetch_ffwar,
        ):
            self.mock_player_data_cache: dict[str, Any] = {}
            self.mock_get_player_data_cache = mock_get_player_data_cache
            self.mock_get_player_data_cache.return_value = (
                self.mock_player_data_cache
            )

            self.mock_fetch_ffwar = mock_fetch_ffwar
            self.mock_fetch_ffwar.return_value = {
                "4046": {"name": "Patrick Mahomes", "ffWAR": 0.5}
            }

            yield

    def test_creates_year_entry_if_not_exists(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test creates year entry in cache if it doesn't exist.

        Args:
            caplog: pytest caplog fixture
        """
        roster_ids = {1: "Tommy", 2: "Mike"}

        update_player_data_cache(2024, 5, roster_ids)

        assert "2024" in self.mock_player_data_cache
        assert "5" in self.mock_player_data_cache["2024"]

    def test_updates_existing_year_entry(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test updates existing year entry in cache.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_player_data_cache["2024"] = {"4": {"existing": "data"}}
        roster_ids = {1: "Tommy", 2: "Mike"}

        update_player_data_cache(2024, 5, roster_ids)

        assert "4" in self.mock_player_data_cache["2024"]
        assert "5" in self.mock_player_data_cache["2024"]

    def test_calls_fetch_ffwar_with_correct_args(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test calls _fetch_ffwar with correct arguments.

        Args:
            caplog: pytest caplog fixture
        """
        roster_ids = {1: "Tommy", 2: "Mike"}

        update_player_data_cache(2024, 5, roster_ids)

        self.mock_fetch_ffwar.assert_called_once_with(2024, 5, roster_ids)

    def test_logs_info_message(self, caplog: pytest.LogCaptureFixture):
        """Test logs info message after update.

        Args:
            caplog: pytest caplog fixture
        """
        roster_ids = {1: "Tommy", 2: "Mike"}

        caplog.set_level(logging.INFO)
        update_player_data_cache(2024, 5, roster_ids)

        assert "Season 2024, Week 5: Player Data Cache Updated" in caplog.text


class TestFetchFfwar:
    """Test _fetch_ffwar function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `_get_all_player_scores`: `mock_get_all_player_scores`
        - `_get_all_rostered_players`: `mock_get_all_rostered_players`
        - `_calculate_ffwar_position`: `mock_calculate_ffwar_position`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                "._get_all_player_scores"
            ) as mock_get_all_player_scores,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                "._get_all_rostered_players"
            ) as mock_get_all_rostered_players,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                "._calculate_ffwar_position"
            ) as mock_calculate_ffwar_position,
        ):
            self.mock_starters_cache = {
                "2024": {
                    "5": {
                        "Tommy": {
                            "Total_Points": 120.5,
                            "Patrick Mahomes": {
                                "position": "QB",
                                "points": 25.0,
                            },
                        },
                        "Mike": {
                            "Total_Points": 110.0,
                            "Josh Allen": {"position": "QB", "points": 22.0},
                        },
                    }
                }
            }
            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_get_all_player_scores = mock_get_all_player_scores
            self.mock_get_all_player_scores.return_value = {
                "QB": {"4046": {"score": 25.0, "name": "Patrick Mahomes"}},
                "RB": {},
                "WR": {},
                "TE": {},
                "K": {},
                "DEF": {},
            }

            self.mock_get_all_rostered_players = mock_get_all_rostered_players
            self.mock_get_all_rostered_players.return_value = {
                "Tommy": ["4046"],
                "Mike": ["6744"],
            }

            self.mock_calculate_ffwar_position = mock_calculate_ffwar_position
            self.mock_calculate_ffwar_position.return_value = {
                "4046": {
                    "name": "Patrick Mahomes",
                    "ffWAR": 0.5,
                    "position": "QB",
                }
            }

            yield

    def test_returns_sorted_ffwar_results(self):
        """Test returns ffWAR results sorted by ffWAR descending then name."""
        self.mock_calculate_ffwar_position.side_effect = [
            {
                "4046": {
                    "name": "Patrick Mahomes",
                    "ffWAR": 0.3,
                    "position": "QB",
                },
                "6744": {"name": "Josh Allen", "ffWAR": 0.5, "position": "QB"},
            },
            {},
            {},
            {},
            {},
            {},
        ]
        roster_ids = {1: "Tommy", 2: "Mike"}

        result = _fetch_ffwar(2024, 5, roster_ids)

        keys = list(result.keys())
        assert keys[0] == "6744"
        assert keys[1] == "4046"

    def test_calls_calculate_ffwar_for_each_position(self):
        """Test calls _calculate_ffwar_position for each position."""
        self.mock_calculate_ffwar_position.return_value = {}
        roster_ids = {1: "Tommy", 2: "Mike"}

        _fetch_ffwar(2024, 5, roster_ids)

        assert self.mock_calculate_ffwar_position.call_count == 6

    def test_skips_empty_ffwar_results(self):
        """Test skips positions with empty ffWAR results."""
        self.mock_calculate_ffwar_position.side_effect = [
            {
                "4046": {
                    "name": "Patrick Mahomes",
                    "ffWAR": 0.5,
                    "position": "QB",
                }
            },
            {},
            {},
            {},
            {},
            {},
        ]
        roster_ids = {1: "Tommy", 2: "Mike"}

        result = _fetch_ffwar(2024, 5, roster_ids)

        assert len(result) == 1
        assert "4046" in result


class TestCalculateFfwarPosition:
    """Test _calculate_ffwar_position function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score,
        ):
            self.mock_replacement_score_cache = {
                "2024": {
                    "5": {
                        "QB_3yr_avg": 15.0,
                        "RB_3yr_avg": 10.0,
                        "WR_3yr_avg": 10.0,
                        "TE_3yr_avg": 8.0,
                        "K_3yr_avg": 7.0,
                        "DEF_3yr_avg": 6.0,
                    }
                }
            }
            self.mock_get_replacement_score = mock_get_replacement_score
            self.mock_get_replacement_score.return_value = (
                self.mock_replacement_score_cache
            )

            yield

    def test_returns_empty_dict_when_no_players(self):
        """Test returns empty dict when no players at position."""
        scores = {
            "Tommy": {"total_points": 120.0, "players": {}},
            "Mike": {"total_points": 110.0, "players": {}},
        }
        all_player_scores: dict[str, dict[str, float | str]] = {}
        all_rostered_players: dict[str, list[str]] = {"Tommy": [], "Mike": []}

        result = _calculate_ffwar_position(
            scores, 2024, 5, "QB", all_player_scores, all_rostered_players
        )

        assert result == {}

    def test_calculates_ffwar_for_rostered_started_player(self):
        """Test calculates ffWAR for rostered and started player."""
        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"Patrick Mahomes": 25.0},
            },
            "Mike": {
                "total_points": 110.0,
                "players": {"Josh Allen": 22.0},
            },
        }
        all_player_scores = {
            "4046": {"score": 25.0, "name": "Patrick Mahomes"},
        }
        all_rostered_players = {"Tommy": ["4046"], "Mike": ["6744"]}

        result = _calculate_ffwar_position(
            scores, 2024, 5, "QB", all_player_scores, all_rostered_players
        )

        assert "4046" in result
        assert result["4046"]["name"] == "Patrick Mahomes"
        assert result["4046"]["started"] is True
        assert result["4046"]["manager"] == "Tommy"

    def test_marks_unstarted_rostered_player(self):
        """Test marks rostered but not started player correctly."""
        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {},
            },
            "Mike": {
                "total_points": 110.0,
                "players": {"Josh Allen": 22.0},
            },
        }
        all_player_scores = {
            "4046": {"score": 25.0, "name": "Patrick Mahomes"},
            "6744": {"score": 22.0, "name": "Josh Allen"},
        }
        all_rostered_players = {"Tommy": ["4046"], "Mike": ["6744"]}

        result = _calculate_ffwar_position(
            scores, 2024, 5, "QB", all_player_scores, all_rostered_players
        )

        assert result["4046"]["started"] is False
        assert result["4046"]["manager"] == "Tommy"

    def test_playoff_adjustment_2021_plus(self):
        """Test playoff adjustment is applied for weeks >= 15 in 2021+."""
        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"Patrick Mahomes": 25.0},
            },
            "Mike": {
                "total_points": 110.0,
                "players": {"Josh Allen": 22.0},
            },
        }
        self.mock_replacement_score_cache["2024"]["15"] = {"QB_3yr_avg": 15.0}
        all_player_scores = {"4046": {"score": 25.0, "name": "Patrick Mahomes"}}
        all_rostered_players = {"Tommy": ["4046"], "Mike": []}

        result = _calculate_ffwar_position(
            scores, 2024, 15, "QB", all_player_scores, all_rostered_players
        )

        assert "4046" in result

    def test_playoff_adjustment_2020_and_earlier(self):
        """Test playoff adjustment applied for weeks >= 14 in year >= 2020."""
        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"Patrick Mahomes": 25.0},
            },
            "Mike": {
                "total_points": 110.0,
                "players": {"Josh Allen": 22.0},
            },
        }
        self.mock_replacement_score_cache["2020"] = {"14": {"QB_3yr_avg": 15.0}}
        all_player_scores = {"4046": {"score": 25.0, "name": "Patrick Mahomes"}}
        all_rostered_players = {"Tommy": ["4046"], "Mike": []}

        result = _calculate_ffwar_position(
            scores, 2020, 14, "QB", all_player_scores, all_rostered_players
        )

        assert "4046" in result


class TestGetAllPlayerScores:
    """Test _get_all_player_scores function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `get_player_info_and_score`: `mock_get_player_info_and_score`
        - `LEAGUE_IDS`: `mock_league_ids`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".get_player_info_and_score"
            ) as mock_get_player_info_and_score,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".LEAGUE_IDS",
                {2024: "league123"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0, "pass_yd": 300}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            self.mock_get_player_info_and_score = mock_get_player_info_and_score
            self.mock_get_player_info_and_score.return_value = (
                True,
                {"full_name": "Patrick Mahomes", "position": "QB"},
                25.0,
                "4046",
            )

            yield

    def test_returns_player_scores_by_position(self):
        """Test returns player scores grouped by position."""
        result = _get_all_player_scores(2024, 5)

        assert "QB" in result
        assert "4046" in result["QB"]
        assert result["QB"]["4046"]["score"] == 25.0
        assert result["QB"]["4046"]["name"] == "Patrick Mahomes"

    def test_raises_exception_when_week_data_fails(self):
        """Test raises exception when week data fetch fails."""
        self.mock_fetch_sleeper_data.side_effect = [[], None]

        with pytest.raises(Exception) as exc_info:
            _get_all_player_scores(2024, 5)

        assert "Could not fetch week data" in str(exc_info.value)

    def test_raises_exception_when_league_settings_fail(self):
        """Test raises exception when league settings fetch fails."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            [],
        ]

        with pytest.raises(Exception) as exc_info:
            _get_all_player_scores(2024, 5)

        assert "Could not fetch league settings" in str(exc_info.value)

    def test_skips_team_entries(self):
        """Test skips TEAM_ entries in week data."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"TEAM_KC": {"pts_allow": 14}, "4046": {"gp": 1.0, "pass_yd": 300}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]

        result = _get_all_player_scores(2024, 5)

        assert "QB" in result
        assert "4046" in result["QB"]

    def test_skips_players_when_get_player_info_returns_false(self):
        """Test skips players when get_player_info_and_score returns False."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 0.0, "pass_yd": 300}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]
        self.mock_get_player_info_and_score.return_value = (
            False,
            {},
            0.0,
            "4046",
        )

        result = _get_all_player_scores(2024, 5)

        assert "4046" not in result["QB"]

    def test_uses_returned_player_id_from_get_player_info(self):
        """Test uses returned player_id from get_player_info_and_score.

        This covers the case where player IDs have non-numeric suffixes
        (like Zach Ertz's '1234ARI') and get_player_info_and_score
        returns the corrected numeric ID.
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046ARI": {"gp": 1.0, "pass_yd": 300}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]
        self.mock_get_player_info_and_score.return_value = (
            True,
            {"full_name": "Patrick Mahomes", "position": "QB"},
            25.0,
            "4046",
        )

        result = _get_all_player_scores(2024, 5)

        assert "4046" in result["QB"]


class TestGetAllRosteredPlayers:
    """Test _get_all_rostered_players function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `LEAGUE_IDS`: `mock_league_ids`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".LEAGUE_IDS",
                {2024: "league123", 2019: "league2019"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = [
                {"roster_id": 1, "players": ["4046", "5678"]},
                {"roster_id": 2, "players": ["6744", "7890"]},
            ]

            yield

    def test_returns_rostered_players_by_manager(self):
        """Test returns rostered players mapped to manager names."""
        roster_ids = {1: "Tommy", 2: "Mike"}

        result = _get_all_rostered_players(roster_ids, 2024, 5)

        assert result["Tommy"] == ["4046", "5678"]
        assert result["Mike"] == ["6744", "7890"]

    def test_handles_2019_early_weeks_roster_swap(self):
        """Test handles historical roster swap for 2019 weeks 1-3."""
        roster_ids = {1: "Cody", 2: "Mike"}

        result = _get_all_rostered_players(roster_ids, 2019, 2)

        assert "Tommy" in result
        assert "Cody" not in result

    def test_does_not_swap_roster_after_week_3(self):
        """Test does not swap roster for 2019 after week 3."""
        roster_ids = {1: "Cody", 2: "Mike"}

        result = _get_all_rostered_players(roster_ids, 2019, 4)

        assert "Cody" in result
        assert "Tommy" not in result

    def test_raises_exception_when_api_fails(self):
        """Test raises exception when Sleeper API fails."""
        self.mock_fetch_sleeper_data.return_value = {}

        roster_ids = {1: "Tommy", 2: "Mike"}

        with pytest.raises(Exception) as exc_info:
            _get_all_rostered_players(roster_ids, 2024, 5)

        assert "Could not fetch matchup data" in str(exc_info.value)
