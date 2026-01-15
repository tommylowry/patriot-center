"""Unit tests for dynamic_filter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.dynamic_filtering.dynamic_filter import filter


class TestFilter:
    """Tests for filter function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `mock_get_players_cache`: `CACHE_MANAGER.get_players_cache`
        - `mock_validate`: `validate_dynamic_filter_args`
        - `mock_find_years`: `find_valid_years`
        - `mock_find_weeks`: `find_valid_weeks`
        - `mock_find_managers`: `find_valid_managers`
        - `mock_find_positions`: `find_valid_positions`
        - `mock_format`: `format_output`

        Yields:
                None
        """
        with (
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".validate_dynamic_filter_args"
            ) as mock_validate,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".find_valid_years"
            ) as mock_find_years,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".find_valid_weeks"
            ) as mock_find_weeks,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".find_valid_managers"
            ) as mock_find_managers,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".find_valid_positions"
            ) as mock_find_positions,
            patch(
                "patriot_center_backend.dynamic_filtering.dynamic_filter"
                ".format_output"
            ) as mock_format,
        ):
            self.mock_get_players_cache = mock_get_players_cache
            self.mock_validate = mock_validate
            self.mock_find_years = mock_find_years
            self.mock_find_weeks = mock_find_weeks
            self.mock_find_managers = mock_find_managers
            self.mock_find_positions = mock_find_positions
            self.mock_format = mock_format

            self.mock_players = {"Jayden Daniels": {"position": "QB"}}
            self.mock_get_players_cache.return_value = self.mock_players

            self.mock_find_years.return_value = {"2024", "2023"}
            self.mock_find_weeks.return_value = {"1", "2"}
            self.mock_find_managers.return_value = {"Tommy", "Anthony"}
            self.mock_find_positions.return_value = {"QB", "RB"}

            yield

    def test_calls_validate_with_all_args(self):
        """Calls validate_dynamic_filter_args with all arguments."""
        filter(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_validate.assert_called_once_with(
            "2024", "1", "Tommy", "QB", None
        )

    def test_calls_find_valid_years_with_filters(self):
        """Calls find_valid_years with manager, position, and player."""
        filter(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_find_years.assert_called_once_with("Tommy", "QB", None)

    def test_calls_find_valid_weeks_with_filters(self):
        """Calls find_valid_weeks with year, manager, position, and player."""
        filter(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_find_weeks.assert_called_once_with(
            "2024", "Tommy", "QB", None
        )

    def test_calls_find_valid_managers_with_filters(self):
        """Calls find_valid_managers with year, week, position, and player."""
        filter(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_find_managers.assert_called_once_with("2024", "1", "QB", None)

    def test_calls_find_valid_positions_when_no_player(self):
        """Calls find_valid_positions when player is not provided."""
        filter(
            year="2024", week="1", manager="Tommy", position=None, player=None
        )

        self.mock_find_positions.assert_called_once_with("2024", "1", "Tommy")

    def test_skips_find_valid_positions_when_player_provided(self):
        """Does not call find_valid_positions when player is provided."""
        filter(
            year="2024",
            week="1",
            manager="Tommy",
            position=None,
            player="Jayden Daniels",
        )

        self.mock_find_positions.assert_not_called()

    def test_locks_position_when_player_provided(self):
        """Uses player's position from cache when player is provided."""
        filter(
            year="2024",
            week=None,
            manager=None,
            position=None,
            player="Jayden Daniels",
        )

        # Should call find_valid_years with the player's position (QB)
        self.mock_find_years.assert_called_once_with(
            None, "QB", "Jayden Daniels"
        )

    def test_calls_format_output_with_results(self):
        """Calls format_output with results from find functions."""
        filter(
            year="2024", week="1", manager="Tommy", position="QB", player=None
        )

        self.mock_format.assert_called_once_with(
            {"2024", "2023"}, {"1", "2"}, {"Tommy", "Anthony"}, {"QB", "RB"}
        )

    def test_with_no_filters(self):
        """Works correctly when no filters are provided."""
        filter()

        self.mock_validate.assert_called_once_with(None, None, None, None, None)
        self.mock_find_years.assert_called_once_with(None, None, None)
        self.mock_find_weeks.assert_called_once_with(None, None, None, None)
        self.mock_find_managers.assert_called_once_with(None, None, None, None)
        self.mock_find_positions.assert_called_once_with(None, None, None)

    def test_player_position_used_in_all_find_calls(self):
        """When player is provided, their position is used in all find calls."""
        filter(
            year="2024",
            week="1",
            manager="Tommy",
            position=None,
            player="Jayden Daniels",
        )

        # Jayden Daniels's position is QB,
        #   so QB should be passed to find functions
        self.mock_find_years.assert_called_once_with(
            "Tommy", "QB", "Jayden Daniels"
        )
        self.mock_find_weeks.assert_called_once_with(
            "2024", "Tommy", "QB", "Jayden Daniels"
        )
        self.mock_find_managers.assert_called_once_with(
            "2024", "1", "QB", "Jayden Daniels"
        )

    def test_format_output_receives_player_position_set(self):
        """When player provided, format_output receives set with position."""
        filter(
            year=None,
            week=None,
            manager=None,
            position=None,
            player="Jayden Daniels",
        )

        # The positions argument should be {"QB"} (player's position)
        call_args = self.mock_format.call_args
        positions_arg = call_args[0][3]  # 4th positional argument
        assert positions_arg == {"QB"}
