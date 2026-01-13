"""Unit tests for validator module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.dynamic_filtering.validator import (
    validate_dynamic_filter_args,
    validate_manager,
    validate_player,
    validate_position,
    validate_week,
    validate_year,
)


class TestValidateDynamicFilterArgs:
    """Tests for validate_dynamic_filter_args function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.validate_year') as mock_validate_year, \
             patch('patriot_center_backend.dynamic_filtering.validator.validate_week') as mock_validate_week, \
             patch('patriot_center_backend.dynamic_filtering.validator.validate_manager') as mock_validate_manager, \
             patch('patriot_center_backend.dynamic_filtering.validator.validate_position') as mock_validate_position, \
             patch('patriot_center_backend.dynamic_filtering.validator.validate_player') as mock_validate_player:

            self.mock_validate_year = mock_validate_year
            self.mock_validate_week = mock_validate_week
            self.mock_validate_manager = mock_validate_manager
            self.mock_validate_position = mock_validate_position
            self.mock_validate_player = mock_validate_player

            yield

    def test_raises_when_all_filters_provided(self):
        """Raises ValueError when all 5 filters are provided."""
        with pytest.raises(ValueError, match="Cannot filter by year, week, manager, position, and player"):
            validate_dynamic_filter_args(
                year="2024",
                week="1",
                manager="Tommy",
                position="QB",
                player="Josh Allen"
            )

    def test_raises_when_week_without_year(self):
        """Raises ValueError when week is provided without year."""
        with pytest.raises(ValueError, match="Week filter cannot be applied without a Year filter"):
            validate_dynamic_filter_args(
                year=None,
                week="1",
                manager=None,
                position=None,
                player=None
            )

    def test_calls_validate_year(self):
        """Calls validate_year with the year argument."""
        validate_dynamic_filter_args(
            year="2024",
            week=None,
            manager=None,
            position=None,
            player=None
        )

        self.mock_validate_year.assert_called_once_with("2024")

    def test_calls_validate_week(self):
        """Calls validate_week with week and year arguments."""
        validate_dynamic_filter_args(
            year="2024",
            week="1",
            manager=None,
            position=None,
            player=None
        )

        self.mock_validate_week.assert_called_once_with("1", "2024")

    def test_calls_validate_manager(self):
        """Calls validate_manager with manager, year, and week arguments."""
        validate_dynamic_filter_args(
            year="2024",
            week="1",
            manager="Tommy",
            position=None,
            player=None
        )

        self.mock_validate_manager.assert_called_once_with("Tommy", "2024", "1")

    def test_calls_validate_position(self):
        """Calls validate_position with position, year, week, and manager arguments."""
        validate_dynamic_filter_args(
            year="2024",
            week="1",
            manager="Tommy",
            position="QB",
            player=None
        )

        self.mock_validate_position.assert_called_once_with("QB", "2024", "1", "Tommy")

    def test_calls_validate_player(self):
        """Calls validate_player with player, year, week, manager, and position arguments."""
        validate_dynamic_filter_args(
            year="2024",
            week="1",
            manager="Tommy",
            position=None,
            player="Josh Allen"
        )

        self.mock_validate_player.assert_called_once_with("Josh Allen", "2024", "1", "Tommy", None)

    def test_calls_all_validators_with_no_filters(self):
        """Calls all validators even when no filters are provided."""
        validate_dynamic_filter_args(
            year=None,
            week=None,
            manager=None,
            position=None,
            player=None
        )

        self.mock_validate_year.assert_called_once_with(None)
        self.mock_validate_week.assert_called_once_with(None, None)
        self.mock_validate_manager.assert_called_once_with(None, None, None)
        self.mock_validate_position.assert_called_once_with(None, None, None, None)
        self.mock_validate_player.assert_called_once_with(None, None, None, None, None)


class TestValidateYear:
    """Tests for validate_year function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.LEAGUE_IDS', {2024: "league_id_1", 2023: "league_id_2"}):

            yield

    def test_passes_when_year_is_none(self):
        """Does not raise when year is None."""
        validate_year(None)

    def test_passes_when_year_is_valid(self):
        """Does not raise when year is valid."""
        validate_year("2024")

    def test_raises_when_year_is_invalid(self):
        """Raises ValueError when year is not in LEAGUE_IDS."""
        with pytest.raises(ValueError, match="Invalid year"):
            validate_year("1999")


class TestValidateWeek:
    """Tests for validate_week function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache:

            self.mock_valid_options_cache = {
                "2024": {"weeks": ["1", "2", "3"]},
                "2023": {"weeks": ["1"]}
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    def test_passes_when_week_is_none(self):
        """Does not raise when week is None."""
        validate_week(None, "2024")

    def test_passes_when_week_is_valid(self):
        """Does not raise when week exists in year's weeks."""
        validate_week("1", "2024")

    def test_raises_when_week_is_invalid(self):
        """Raises ValueError when week not in year's weeks."""
        with pytest.raises(ValueError, match="Invalid week"):
            validate_week("99", "2024")

    def test_raises_when_week_not_in_year(self):
        """Raises ValueError when week not available in specified year."""
        with pytest.raises(ValueError, match="Invalid week"):
            validate_week("3", "2023")


class TestValidateManager:
    """Tests for validate_manager function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache, \
             patch('patriot_center_backend.dynamic_filtering.validator.NAME_TO_MANAGER_USERNAME', {"Tommy": "username_1", "Anthony": "username_2"}):

            self.mock_valid_options_cache = {
                "2024": {
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {"managers": ["Tommy"]}
                }
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    def test_passes_when_manager_is_none(self):
        """Does not raise when manager is None."""
        validate_manager(None, "2024", "1")

    def test_passes_when_manager_is_valid(self):
        """Does not raise when manager is valid."""
        validate_manager("Tommy", "2024", "1")

    def test_raises_when_manager_not_in_constants(self):
        """Raises ValueError when manager not in NAME_TO_MANAGER_USERNAME."""
        with pytest.raises(ValueError, match="Invalid manager"):
            validate_manager("NonExistent", None, None)

    def test_raises_when_manager_not_in_year(self):
        """Raises ValueError when manager not in year's managers."""
        with pytest.raises(ValueError, match="Invalid manager"):
            validate_manager("Anthony", "2024", None)

    def test_raises_when_manager_not_in_week(self):
        """Raises ValueError when manager not in week's managers."""
        self.mock_valid_options_cache["2024"]["managers"] = ["Tommy", "Anthony"]
        self.mock_valid_options_cache["2024"]["1"]["managers"] = ["Tommy"]

        with pytest.raises(ValueError, match="Invalid manager"):
            validate_manager("Anthony", "2024", "1")


class TestValidatePosition:
    """Tests for validate_position function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache:

            self.mock_valid_options_cache = {
                "2024": {
                    "positions": ["QB", "RB"],
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {
                        "positions": ["QB"],
                        "managers": ["Tommy"],
                        "Tommy": {"positions": ["QB"]}
                    },
                    "Tommy": {"positions": ["QB", "RB"]}
                }
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    def test_passes_when_position_is_none(self):
        """Does not raise when position is None."""
        validate_position(None, "2024", "1", "Tommy")

    def test_passes_when_position_is_valid(self):
        """Does not raise when position is valid."""
        validate_position("QB", "2024", "1", "Tommy")

    def test_raises_when_position_not_in_allowed_list(self):
        """Raises ValueError when position not in allowed list."""
        with pytest.raises(ValueError, match="Invalid position"):
            validate_position("INVALID", None, None, None)

    def test_raises_when_position_not_in_year(self):
        """Raises ValueError when position not in year's positions."""
        with pytest.raises(ValueError, match="Invalid position"):
            validate_position("WR", "2024", None, None)

    def test_raises_when_position_not_in_week(self):
        """Raises ValueError when position not in week's positions."""
        self.mock_valid_options_cache["2024"]["positions"] = ["QB", "RB"]
        self.mock_valid_options_cache["2024"]["1"]["positions"] = ["QB"]

        with pytest.raises(ValueError, match="Invalid position"):
            validate_position("RB", "2024", "1", None)


class TestValidatePlayer:
    """Tests for validate_player function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.validator.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache, \
             patch('patriot_center_backend.dynamic_filtering.validator.CACHE_MANAGER.get_players_cache') as mock_get_players_cache:

            self.mock_valid_options_cache = {
                "2024": {
                    "players": ["Josh Allen"],
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {
                        "players": ["Josh Allen"],
                        "managers": ["Tommy"],
                        "Tommy": {"players": ["Josh Allen"]}
                    },
                    "Tommy": {"players": ["Josh Allen"]}
                }
            }
            self.mock_players_cache = {
                "Josh Allen": {"position": "QB"},
                "Rico Dowdle": {"position": "RB"}
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = self.mock_players_cache

            yield

    def test_passes_when_player_is_none(self):
        """Does not raise when player is None."""
        validate_player(None, "2024", "1", "Tommy", "QB")

    def test_passes_when_player_is_valid(self):
        """Does not raise when player is valid."""
        validate_player("Josh Allen", "2024", "1", "Tommy", "QB")

    def test_raises_when_player_not_in_cache(self):
        """Raises ValueError when player not in players cache."""
        with pytest.raises(ValueError, match="Invalid player"):
            validate_player("NonExistent", None, None, None, None)

    def test_raises_when_player_position_mismatch(self):
        """Raises ValueError when player's position doesn't match filter."""
        with pytest.raises(ValueError, match="Invalid player"):
            validate_player("Josh Allen", None, None, None, "RB")

    def test_raises_when_player_not_in_year(self):
        """Raises ValueError when player not in year's players."""
        with pytest.raises(ValueError, match="Invalid player"):
            validate_player("Rico Dowdle", "2024", None, None, None)

    def test_raises_when_player_not_in_week(self):
        """Raises ValueError when player not in week's players."""
        self.mock_valid_options_cache["2024"]["players"] = ["Josh Allen", "Rico Dowdle"]
        self.mock_valid_options_cache["2024"]["1"]["players"] = ["Josh Allen"]

        with pytest.raises(ValueError, match="Invalid player"):
            validate_player("Rico Dowdle", "2024", "1", None, None)

    def test_raises_when_player_not_with_manager(self):
        """Raises ValueError when player not with specified manager."""
        self.mock_valid_options_cache["2024"]["players"] = ["Josh Allen", "Rico Dowdle"]
        self.mock_valid_options_cache["2024"]["Tommy"] = {"players": ["Josh Allen"]}

        with pytest.raises(ValueError, match="Invalid player"):
            validate_player("Rico Dowdle", "2024", None, "Tommy", None)
