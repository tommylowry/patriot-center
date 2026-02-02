"""Unit tests for aggregation_queries module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.queries.aggregation_queries import (
    get_ffwar_from_cache,
    get_team,
)

MODULE_PATH = "patriot_center_backend.cache.queries.aggregation_queries"


class TestGetFfwarFromCache:
    """Test get_ffwar_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_data_cache`:
            `mock_get_player_data_cache`
        - `get_player_id`: `mock_get_player_id`

        Yields:
            None
        """
        # Clear lru_cache between tests
        get_ffwar_from_cache.cache_clear()

        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_player_data_cache"
            ) as mock_get_player_data_cache,
            patch(f"{MODULE_PATH}.get_player_id") as mock_get_player_id,
        ):
            self.mock_get_player_data_cache = mock_get_player_data_cache
            self.mock_get_player_data_cache.return_value = {
                "2023": {
                    "1": {
                        "12345": {"ffWAR": 1.5},
                        "67890": {"ffWAR": 0.8},
                    }
                }
            }

            self.mock_get_player_id = mock_get_player_id
            self.mock_get_player_id.return_value = "12345"

            yield

        # Clear lru_cache after tests
        get_ffwar_from_cache.cache_clear()

    def test_returns_ffwar_for_valid_player(self):
        """Test returns ffWAR when player exists in cache."""
        result = get_ffwar_from_cache("Jayden Daniels", season="2023", week="1")

        assert result == 1.5

    def test_returns_zero_when_season_is_none(self):
        """Test returns 0.0 when season is None."""
        result = get_ffwar_from_cache("Jayden Daniels", season=None, week="1")

        assert result == 0.0

    def test_returns_zero_when_week_is_none(self):
        """Test returns 0.0 when week is None."""
        result = get_ffwar_from_cache(
            "Jayden Daniels", season="2023", week=None
        )

        assert result == 0.0

    def test_returns_zero_when_both_none(self):
        """Test returns 0.0 when both season and week are None."""
        result = get_ffwar_from_cache("Jayden Daniels", season=None, week=None)

        assert result == 0.0

    def test_returns_zero_when_season_not_in_cache(self):
        """Test returns 0.0 when season not found in cache."""
        result = get_ffwar_from_cache("Jayden Daniels", season="2020", week="1")

        assert result == 0.0

    def test_returns_zero_when_week_not_in_cache(self):
        """Test returns 0.0 when week not found in cache."""
        result = get_ffwar_from_cache("Jayden Daniels", season="2023", week="5")

        assert result == 0.0

    def test_returns_zero_when_player_id_not_in_cache(self):
        """Test returns 0.0 when player ID not found in week data."""
        self.mock_get_player_id.return_value = "99999"

        result = get_ffwar_from_cache("Unknown Player", season="2023", week="1")

        assert result == 0.0

    def test_different_player_returns_different_ffwar(self):
        """Test returns correct ffWAR for different player."""
        self.mock_get_player_id.return_value = "67890"

        result = get_ffwar_from_cache("Brian Robinson", season="2023", week="1")

        assert result == 0.8


class TestGetTeam:
    """Test get_team function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_players_cache`:
            `mock_get_players_cache`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
        ):
            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = {
                "Jayden Daniels": {"team": "WAS"},
                "Brian Robinson": {"team": "WAS"},
                "Terry McLaurin": {"team": "WAS"},
            }

            yield

    def test_returns_team_for_known_player(self):
        """Test returns team when player exists in cache."""
        result = get_team("Jayden Daniels")

        assert result == "WAS"

    def test_returns_none_for_unknown_player(self):
        """Test returns None when player not in cache."""
        result = get_team("Unknown Player")

        assert result is None

    def test_returns_none_when_player_has_no_team(self):
        """Test returns None when player exists but has no team key."""
        self.mock_get_players_cache.return_value = {
            "Jayden Daniels": {"position": "QB"},
        }

        result = get_team("Jayden Daniels")

        assert result is None
