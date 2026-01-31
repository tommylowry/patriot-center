"""Unit tests for player_scores_fetcher module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.players.player_scores_fetcher import (
    fetch_all_player_scores,
    fetch_rostered_players,
    fetch_starters_by_position,
)


class TestFetchAllPlayerScores:
    """Test fetch_all_player_scores function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `get_player_info_and_score`:
            `mock_get_player_info_and_score`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".get_player_info_and_score"
            ) as mock_get_player_info_and_score,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "1": {
                        "positions": ["QB", "RB"],
                        "managers": ["Tommy", "Jay"],
                    },
                },
            }
            mock_get_valid_options.return_value = self.mock_valid_options_cache

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            self.mock_get_player_info_and_score = mock_get_player_info_and_score
            self.mock_get_player_info_and_score.return_value = (
                True,
                {"position": "QB", "full_name": "Patrick Mahomes"},
                25.5,
                "4046",
            )

            yield

    def test_returns_scores_grouped_by_position(self):
        """Test returns player scores grouped by position."""
        result = fetch_all_player_scores(2024, 1)

        assert "QB" in result
        assert "RB" in result
        assert result["QB"]["4046"]["score"] == 25.5
        assert result["QB"]["4046"]["name"] == "Patrick Mahomes"

    def test_skips_team_entries(self):
        """Test skips TEAM_ entries in week data."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"TEAM_KC": {"pts": 30}, "4046": {"gp": 1.0}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]

        fetch_all_player_scores(2024, 1)

        self.mock_get_player_info_and_score.assert_called_once()

    def test_skips_player_when_apply_is_false(self):
        """Test skips player when get_player_info_and_score returns False."""
        self.mock_get_player_info_and_score.return_value = (
            False,
            {},
            0.0,
            "4046",
        )

        result = fetch_all_player_scores(2024, 1)

        assert result["QB"] == {}

    def test_raises_when_positions_missing(self):
        """Test raises Exception when positions not in valid options."""
        self.mock_valid_options_cache["2024"]["1"] = {
            "managers": ["Tommy", "Jay"],
        }

        with pytest.raises(Exception) as exc_info:
            fetch_all_player_scores(2024, 1)

        assert "Valid options not found" in str(exc_info.value)

    def test_raises_when_week_data_not_dict(self):
        """Test raises Exception when Sleeper API returns non-dict."""
        self.mock_fetch_sleeper_data.side_effect = [
            None,
            {"scoring_settings": {}},
        ]

        with pytest.raises(Exception) as exc_info:
            fetch_all_player_scores(2024, 1)

        assert "Could not fetch week data" in str(exc_info.value)

    def test_raises_when_league_settings_not_dict(self):
        """Test raises Exception when league settings returns non-dict."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            None,
        ]

        with pytest.raises(Exception) as exc_info:
            fetch_all_player_scores(2024, 1)

        assert "Could not fetch league settings" in str(exc_info.value)

    def test_raises_when_scoring_settings_missing(self):
        """Test raises Exception when scoring_settings not in response."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            {"no_scoring": True},
        ]

        with pytest.raises(Exception) as exc_info:
            fetch_all_player_scores(2024, 1)

        assert "Could not find scoring settings" in str(exc_info.value)


class TestFetchRosteredPlayers:
    """Test fetch_rostered_players function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_roster_ids`: `mock_get_roster_ids`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".get_roster_ids"
            ) as mock_get_roster_ids,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_get_roster_ids = mock_get_roster_ids
            self.mock_get_roster_ids.return_value = {
                1: "Tommy",
                2: "Jay",
            }

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = [
                {"roster_id": 1, "players": ["4046", "6794"]},
                {"roster_id": 2, "players": ["5001", "5002"]},
            ]

            yield

    def test_returns_rostered_players_by_manager(self):
        """Test returns mapping of manager names to player ID lists."""
        result = fetch_rostered_players(2024, 1)

        assert result["Tommy"] == ["4046", "6794"]
        assert result["Jay"] == ["5001", "5002"]

    def test_raises_when_api_returns_non_list(self):
        """Test raises Exception when matchup data is not a list."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(Exception) as exc_info:
            fetch_rostered_players(2024, 1)

        assert "Could not fetch matchup data" in str(exc_info.value)


class TestFetchStartersByPosition:
    """Test fetch_starters_by_position function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options`
        - `CACHE_MANAGER.get_starters_cache`:
            `mock_get_starters_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.players.player_scores_fetcher"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "1": {
                        "positions": ["QB", "RB"],
                        "managers": ["Tommy", "Jay"],
                    },
                },
            }
            mock_get_valid_options.return_value = self.mock_valid_options_cache

            self.mock_starters_cache = {
                "2024": {
                    "1": {
                        "Tommy": {
                            "Total_Points": 120.0,
                            "Patrick Mahomes": {
                                "points": 25.0,
                                "position": "QB",
                            },
                            "Saquon Barkley": {
                                "points": 18.0,
                                "position": "RB",
                            },
                        },
                        "Jay": {
                            "Total_Points": 100.0,
                            "Josh Allen": {
                                "points": 22.0,
                                "position": "QB",
                            },
                        },
                    },
                },
            }
            mock_get_starters_cache.return_value = self.mock_starters_cache

            yield

    def test_returns_scores_grouped_by_position(self):
        """Test returns starter scores grouped by position."""
        result = fetch_starters_by_position(2024, 1)

        assert "QB" in result
        assert "RB" in result

    def test_populates_players_list(self):
        """Test populates players list for each position."""
        result = fetch_starters_by_position(2024, 1)

        assert "Patrick Mahomes" in result["QB"]["players"]
        assert "Josh Allen" in result["QB"]["players"]

    def test_populates_scores_list(self):
        """Test populates scores list for each position."""
        result = fetch_starters_by_position(2024, 1)

        assert 25.0 in result["QB"]["scores"]
        assert 22.0 in result["QB"]["scores"]

    def test_sets_total_points_for_all_managers_at_all_positions(self):
        """Test sets total_points for all managers at all positions."""
        result = fetch_starters_by_position(2024, 1)

        assert result["QB"]["managers"]["Tommy"]["total_points"] == 120.0
        assert result["QB"]["managers"]["Jay"]["total_points"] == 100.0
        assert result["RB"]["managers"]["Tommy"]["total_points"] == 120.0
        assert result["RB"]["managers"]["Jay"]["total_points"] == 100.0

    def test_manager_with_no_position_starter_has_empty_scores(self):
        """Test manager with no starter at position has empty scores list."""
        result = fetch_starters_by_position(2024, 1)

        # Jay has no RB starter
        assert result["RB"]["managers"]["Jay"]["scores"] == []

    def test_manager_with_no_position_starter_still_has_total_points(self):
        """Test manager with no starter at position still has total_points."""
        result = fetch_starters_by_position(2024, 1)

        # Jay has no RB but should still have total_points set
        assert result["RB"]["managers"]["Jay"]["total_points"] == 100.0

    def test_populates_per_manager_scores(self):
        """Test populates per-manager scores for each position."""
        result = fetch_starters_by_position(2024, 1)

        assert result["QB"]["managers"]["Tommy"]["scores"] == [25.0]
        assert result["QB"]["managers"]["Jay"]["scores"] == [22.0]
