"""Unit tests for validator module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.dynamic_filtering.validator import (
    _traverse_for_year_and_manager,
    _validate_manager,
    _validate_player,
    _validate_position,
    _validate_week,
    _validate_year,
    validate_dynamic_filter_args,
)


class TestValidateDynamicFilterArgs:
    """Tests for validate_dynamic_filter_args function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `_validate_year`: `mock_validate_year`
        - `_validate_week`: `mock_validate_week`
        - `_validate_manager`: `mock_validate_manager`
        - `_validate_position`: `mock_validate_position`
        - `_validate_player`: `mock_validate_player`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._validate_year"
            ) as mock_validate_year,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._validate_week"
            ) as mock_validate_week,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._validate_manager"
            ) as mock_validate_manager,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._validate_position"
            ) as mock_validate_position,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._validate_player"
            ) as mock_validate_player,
        ):
            self.mock_validate_year = mock_validate_year
            self.mock_validate_week = mock_validate_week
            self.mock_validate_manager = mock_validate_manager
            self.mock_validate_position = mock_validate_position
            self.mock_validate_player = mock_validate_player

            yield

    def test_raises_when_all_filters_provided(self):
        """Raises ValueError when all 5 filters are provided."""
        with pytest.raises(
            ValueError,
            match="Cannot filter by year, week, manager, position, and player",
        ):
            validate_dynamic_filter_args(
                year="2024",
                week="1",
                manager="Tommy",
                position="QB",
                player="Josh Allen",
            )

    def test_calls_validate_year(self):
        """Calls validate_year with the year argument."""
        validate_dynamic_filter_args(
            year="2024", week=None, manager=None, position=None, player=None
        )

        self.mock_validate_year.assert_called_once_with("2024")

    def test_calls_validate_week(self):
        """Calls validate_week with week and year arguments."""
        validate_dynamic_filter_args(
            year="2024", week="1", manager=None, position=None, player=None
        )

        self.mock_validate_week.assert_called_once_with("1", "2024")

    def test_calls_validate_manager(self):
        """Calls validate_manager with manager, year, and week arguments."""
        validate_dynamic_filter_args(
            year="2024", week="1", manager="Tommy", position=None, player=None
        )

        self.mock_validate_manager.assert_called_once_with("Tommy", "2024", "1")

    def test_calls_validate_position(self):
        """Calls with position, year, week, and manager arguments."""
        validate_dynamic_filter_args(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_validate_position.assert_called_once_with(
            "QB", "2024", "1", "Tommy"
        )

    def test_calls_validate_player(self):
        """Calls with player, year, week, manager, and position arguments."""
        validate_dynamic_filter_args(
            year="2024",
            week="1",
            manager="Tommy",
            position=None,
            player="Josh Allen",
        )

        self.mock_validate_player.assert_called_once_with(
            "Josh Allen", "2024", "1", "Tommy", None
        )

    def test_calls_all_validators_with_no_filters(self):
        """Calls all validators even when no filters are provided."""
        validate_dynamic_filter_args(
            year=None, week=None, manager=None, position=None, player=None
        )

        self.mock_validate_year.assert_called_once_with(None)
        self.mock_validate_week.assert_called_once_with(None, None)
        self.mock_validate_manager.assert_called_once_with(None, None, None)
        self.mock_validate_position.assert_called_once_with(
            None, None, None, None
        )
        self.mock_validate_player.assert_called_once_with(
            None, None, None, None, None
        )


class TestValidateYear:
    """Tests for _validate_year function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `LEAGUE_IDS`: `{2024: "league_id_1", 2023: "league_id_2"}`

        Yields:
                None
        """
        with patch(
            "patriot_center_backend.dynamic_filtering.validator.LEAGUE_IDS",
            {2024: "league_id_1", 2023: "league_id_2"},
        ):
            yield

    def test_passes_when_year_is_none(self):
        """Does not raise when year is None."""
        _validate_year(None)

    def test_passes_when_year_is_valid(self):
        """Does not raise when year is valid."""
        _validate_year("2024")

    def test_raises_when_year_is_invalid(self):
        """Raises ValueError when year is not in LEAGUE_IDS."""
        with pytest.raises(ValueError, match="Invalid year"):
            _validate_year("1999")


class TestValidateWeek:
    """Tests for _validate_week function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
        ):
            self.mock_valid_options_cache = {
                "2024": {"weeks": ["1", "2", "3"]},
                "2023": {"weeks": ["1"]},
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            yield

    def test_passes_when_week_is_none(self):
        """Does not raise when week is None."""
        _validate_week(None, "2024")

    def test_passes_when_week_is_valid(self):
        """Does not raise when week exists in year's weeks."""
        _validate_week("1", "2024")

    def test_raises_when_week_is_invalid(self):
        """Raises ValueError when week not in year's weeks."""
        with pytest.raises(ValueError, match="Invalid week"):
            _validate_week("99", "2024")

    def test_raises_when_week_not_in_year(self):
        """Raises ValueError when week not available in specified year."""
        with pytest.raises(ValueError, match="Invalid week"):
            _validate_week("3", "2023")

    def test_raises_when_week_without_year(self):
        """Raises ValueError when week is provided without year."""
        with pytest.raises(
            ValueError,
            match="Week filter cannot be applied without a Year filter",
        ):
            _validate_week("1", None)


class TestValidateManager:
    """Tests for _validate_manager function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`
        - `NAME_TO_MANAGER_USERNAME`:
            `{"Tommy": "username_1", "Anthony": "username_2"}`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".NAME_TO_MANAGER_USERNAME",
                {"Tommy": "username_1", "Anthony": "username_2"},
            ),
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {"managers": ["Tommy"]},
                }
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            yield

    def test_passes_when_manager_is_none(self):
        """Does not raise when manager is None."""
        _validate_manager(None, "2024", "1")

    def test_passes_when_manager_is_valid(self):
        """Does not raise when manager is valid."""
        _validate_manager("Tommy", "2024", "1")

    def test_raises_when_manager_not_in_constants(self):
        """Raises ValueError when manager not in NAME_TO_MANAGER_USERNAME."""
        with pytest.raises(ValueError, match="Invalid manager"):
            _validate_manager("NonExistent", None, None)

    def test_raises_when_manager_not_in_year(self):
        """Raises ValueError when manager not in year's managers."""
        with pytest.raises(ValueError, match="Invalid manager"):
            _validate_manager("Anthony", "2024", None)

    def test_raises_when_manager_not_in_week(self):
        """Raises ValueError when manager not in week's managers."""
        self.mock_valid_options_cache["2024"]["managers"] = ["Tommy", "Anthony"]
        self.mock_valid_options_cache["2024"]["1"]["managers"] = ["Tommy"]

        with pytest.raises(ValueError, match="Invalid manager"):
            _validate_manager("Anthony", "2024", "1")


class TestValidatePosition:
    """Tests for _validate_position function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`
        - `_traverse_for_year_and_manager`: `mock_traverse`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._traverse_for_year_and_manager"
            ) as mock_traverse,
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "positions": ["QB", "RB"],
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {
                        "positions": ["QB"],
                        "managers": ["Tommy"],
                        "Tommy": {"positions": ["QB"]},
                    },
                }
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            self.mock_traverse = mock_traverse

            yield

    def test_passes_when_position_is_none(self):
        """Does not raise when position is None."""
        _validate_position(None, "2024", "1", "Tommy")

    def test_passes_when_position_is_valid(self):
        """Does not raise when position is valid."""
        _validate_position("QB", "2024", "1", "Tommy")

    def test_raises_when_position_not_in_allowed_list(self):
        """Raises ValueError when position not in allowed list."""
        with pytest.raises(ValueError, match="Invalid position"):
            _validate_position("INVALID", None, None, None)

    def test_raises_when_position_not_in_year(self):
        """Raises ValueError when position not in year's positions."""
        with pytest.raises(ValueError, match="Invalid position"):
            _validate_position("WR", "2024", None, None)

    def test_raises_when_position_not_in_week(self):
        """Raises ValueError when position not in week's positions."""
        self.mock_valid_options_cache["2024"]["positions"] = ["QB", "RB"]
        self.mock_valid_options_cache["2024"]["1"]["positions"] = ["QB"]

        with pytest.raises(ValueError, match="Invalid position"):
            _validate_position("RB", "2024", "1", None)

    def test_calls_traverse_when_year_and_manager(self):
        """Calls when year and manager provided."""
        _validate_position("QB", "2024", None, "Tommy")

        self.mock_traverse.assert_called_once_with(
            "2024", "Tommy", "QB", "position"
        )

    def test_does_not_call_traverse_when_no_manager(self):
        """Does not call _traverse_for_year_and_manager when manager is None."""
        _validate_position("QB", "2024", None, None)

        self.mock_traverse.assert_not_called()


class TestValidatePlayer:
    """Tests for _validate_player function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `_traverse_for_year_and_manager`: `mock_traverse`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                "._traverse_for_year_and_manager"
            ) as mock_traverse,
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "players": ["Josh Allen"],
                    "managers": ["Tommy"],
                    "weeks": ["1"],
                    "1": {
                        "players": ["Josh Allen"],
                        "managers": ["Tommy"],
                        "Tommy": {"players": ["Josh Allen"]},
                    },
                }
            }
            self.mock_players_cache = {
                "Josh Allen": {"position": "QB"},
                "Rico Dowdle": {"position": "RB"},
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = self.mock_players_cache

            self.mock_traverse = mock_traverse

            yield

    def test_passes_when_player_is_none(self):
        """Does not raise when player is None."""
        _validate_player(None, "2024", "1", "Tommy", "QB")

    def test_passes_when_player_is_valid(self):
        """Does not raise when player is valid."""
        _validate_player("Josh Allen", "2024", "1", "Tommy", "QB")

    def test_raises_when_player_not_in_cache(self):
        """Raises ValueError when player not in players cache."""
        with pytest.raises(ValueError, match="Invalid player"):
            _validate_player("NonExistent", None, None, None, None)

    def test_raises_when_player_position_mismatch(self):
        """Raises ValueError when player's position doesn't match filter."""
        with pytest.raises(ValueError, match="Invalid player"):
            _validate_player("Josh Allen", None, None, None, "RB")

    def test_raises_when_player_not_in_year(self):
        """Raises ValueError when player not in year's players."""
        with pytest.raises(ValueError, match="Invalid player"):
            _validate_player("Rico Dowdle", "2024", None, None, None)

    def test_raises_when_player_not_in_week(self):
        """Raises ValueError when player not in week's players."""
        self.mock_valid_options_cache["2024"]["players"] = [
            "Josh Allen",
            "Rico Dowdle",
        ]
        self.mock_valid_options_cache["2024"]["1"]["players"] = ["Josh Allen"]

        with pytest.raises(ValueError, match="Invalid player"):
            _validate_player("Rico Dowdle", "2024", "1", None, None)

    def test_calls_traverse_when_year_and_manager(self):
        """Calls when year and manager provided."""
        _validate_player("Josh Allen", "2024", None, "Tommy", None)

        self.mock_traverse.assert_called_once_with(
            "2024", "Tommy", "Josh Allen", "player"
        )

    def test_does_not_call_traverse_when_no_manager(self):
        """Does not call _traverse_for_year_and_manager when manager is None."""
        _validate_player("Josh Allen", "2024", None, None, None)

        self.mock_traverse.assert_not_called()


class TestTraverseForYearAndManager:
    """Tests for _traverse_for_year_and_manager function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.validator"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
        ):
            self.mock_valid_options_cache = {
                "2024": {
                    "weeks": ["1", "2", "3"],
                    "1": {
                        "Tommy": {
                            "players": ["Josh Allen", "Stefon Diggs"],
                            "positions": ["QB", "WR"],
                        },
                        "Anthony": {
                            "players": ["Lamar Jackson"],
                            "positions": ["QB"],
                        },
                    },
                    "2": {
                        "Tommy": {
                            "players": ["Josh Allen", "James Cook"],
                            "positions": ["QB", "RB"],
                        },
                        "Anthony": {
                            "players": ["Lamar Jackson", "Derrick Henry"],
                            "positions": ["QB", "RB"],
                        },
                    },
                    "3": {
                        "Tommy": {
                            "players": ["Josh Allen"],
                            "positions": ["QB"],
                        }
                    },
                },
                "2025": {
                    "weeks": ["1"],
                    "1": {
                        "Tommy": {
                            "players": ["Trey McBride"],
                            "positions": ["TE"],
                        }
                    },
                },
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            yield

    # ===== Player validation =====
    def test_passes_when_player_found_in_week(self):
        """Does not raise when player found in any week for manager."""
        _traverse_for_year_and_manager("2024", "Tommy", "Josh Allen", "player")

    def test_passes_when_player_found_in_only_one_week(self):
        """Does not raise when player found in only one week."""
        _traverse_for_year_and_manager(
            "2024", "Tommy", "Stefon Diggs", "player"
        )

    def test_passes_when_player_found_in_any_year(self):
        """Does not raise when player found in any year."""
        _traverse_for_year_and_manager(None, "Tommy", "Trey McBride", "player")

    def test_raises_when_player_not_found_in_any_week(self):
        """Raises ValueError when player not in any week for manager."""
        with pytest.raises(ValueError, match="Invalid player"):
            _traverse_for_year_and_manager(
                "2024", "Tommy", "Lamar Jackson", "player"
            )

    def test_raises_when_player_not_found_in_any_year(self):
        """Raises ValueError when player not in any week for manager."""
        with pytest.raises(ValueError, match="Invalid player"):
            _traverse_for_year_and_manager(
                None, "Tommy", "Washington Commanders", "player"
            )

    def test_raises_when_player_with_wrong_manager(self):
        """Raises ValueError when player exists but not for manager."""
        with pytest.raises(ValueError, match="Invalid player"):
            _traverse_for_year_and_manager(
                "2024", "Anthony", "Josh Allen", "player"
            )

    # ===== Position validation =====
    def test_passes_when_position_found_in_week(self):
        """Does not raise when position found in any week for manager."""
        _traverse_for_year_and_manager("2024", "Tommy", "QB", "position")

    def test_passes_when_position_found_in_only_one_week(self):
        """Does not raise when position found in only one week."""
        _traverse_for_year_and_manager("2024", "Tommy", "WR", "position")

    def test_passes_when_position_found_in_any_year(self):
        """Does not raise when position found in any year."""
        _traverse_for_year_and_manager(None, "Tommy", "TE", "position")

    def test_raises_when_position_not_found_in_any_week(self):
        """Raises ValueError when position not in any week for manager."""
        with pytest.raises(ValueError, match="Invalid position"):
            _traverse_for_year_and_manager("2024", "Tommy", "TE", "position")

    def test_raises_when_position_not_found_in_any_year(self):
        """Raises ValueError when position not in any year for manager."""
        with pytest.raises(ValueError, match="Invalid position"):
            _traverse_for_year_and_manager(None, "Tommy", "K", "position")

    # ===== Edge cases =====
    def test_raises_when_manager_not_in_any_week(self):
        """Raises ValueError when manager not in any week."""
        with pytest.raises(ValueError, match="Invalid player"):
            _traverse_for_year_and_manager(
                "2024", "Owen", "Josh Allen", "player"
            )

    def test_raises_when_year_has_no_weeks(self):
        """Raises ValueError when year has no weeks."""
        self.mock_valid_options_cache["2023"] = {"weeks": []}

        with pytest.raises(ValueError, match="Invalid player"):
            _traverse_for_year_and_manager(
                "2023", "Tommy", "Josh Allen", "player"
            )

    def test_raises_when_year_not_in_cache(self):
        """Raises ValueError when year not in cache."""
        with pytest.raises(ValueError, match="Invalid position"):
            _traverse_for_year_and_manager("1999", "Tommy", "QB", "position")
