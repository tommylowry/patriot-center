"""Unit tests for sleeper_helpers module."""

from unittest.mock import call, patch

import pytest

from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_current_season_and_week,
    get_roster_id,
    get_roster_ids,
)


@pytest.fixture(autouse=True)
def globals_setup():
    """Setup common mocks for all tests.

    The mocks are set up to return a pre-defined
    set of values when accessed.
    - `mock_league_ids`: `LEAGUE_IDS`
    - `mock_username_to_real_name`: `USERNAME_TO_REAL_NAME`

    Yields:
        None
    """
    # Mock values
    mock_username_to_real_name = {
        "username1": "Manager 1",
        "username2": "Manager 2",
        "username3": "Manager 3"
    }
    mock_league_ids = {
        2023: "leagueid2023",
        2024: "leagueid2024"
    }

    with (
        patch(
            'patriot_center_backend.utils.sleeper_helpers'
            '.LEAGUE_IDS',
            mock_league_ids,
        ),

        patch(
            'patriot_center_backend.utils.sleeper_helpers'
            '.USERNAME_TO_REAL_NAME',
            mock_username_to_real_name,
        ),
    ):

        yield


class TestFetchSleeperData:
    """Unit tests for fetch_sleeper_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `mock_get`: `requests.get`

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.sleeper_helpers'
                '.requests.get'
            ) as mock_get,
        ):

            self.mock_get = mock_get

            yield


    def test_fetch_sleeper_data(self):
        """Test calls the correct URL and returns the expected JSON response."""
        self.mock_get.return_value.json.return_value = {}
        self.mock_get.return_value.status_code = 200

        fetch_sleeper_data('test_endpoint')

        self.mock_get.assert_called_once_with(
            'https://api.sleeper.app/v1/test_endpoint'
        )

    def test_fetch_sleeper_data_connection_error(self):
        """Test raises a ConnectionAbortedError when the request fails."""
        self.mock_get.return_value.json.return_value = {}
        self.mock_get.return_value.status_code = 500


        error_message = (
            r"Failed to fetch data from Sleeper API with "
            r"call to https://api.sleeper.app/v1/test_endpoint"
        )
        with pytest.raises(ConnectionAbortedError, match=error_message):
            fetch_sleeper_data('test_endpoint')


class TestGetRosterId:
    """Unit tests for get_roster_id function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `mock_fetch_sleeper_data`: `fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.sleeper_helpers'
                '.fetch_sleeper_data'
            ) as mock_fetch_sleeper_data,
        ):

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield


    def test_get_roster_id(self):
        """Test returns the correct roster ID for a given user ID and year."""
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user1'
        year = 2023

        result = get_roster_id(user_id, year, sleeper_rosters_response)

        assert result == 1

    def test_2024_roster_id(self):
        """Check correctly assigns the roster ID for a user in 2024 league."""
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
            {'owner_id': None, 'roster_id': 3},
        ]
        user_id = 'user3'
        year = 2024

        result = get_roster_id(user_id, year, sleeper_rosters_response)

        assert result == 3

    def test_sleeper_api_not_called(self):
        """Test does not call API if sleeper_rosters_response is provided."""
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user1'
        year = 2023

        get_roster_id(user_id, year, sleeper_rosters_response)

        self.mock_fetch_sleeper_data.assert_not_called()

    def test_get_roster_id_not_found(self):
        """Check returns None if user ID is not found in sleeper response."""
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user3'
        year = 2023

        result = get_roster_id(user_id, year, sleeper_rosters_response)

        assert result is None

    def test_no_sleeper_rosters_input(self):
        """Test when sleeper_rosters_response not provided."""
        self.mock_fetch_sleeper_data.return_value = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]

        user_id = 'user1'
        year = 2023

        result = get_roster_id(user_id, year)

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/leagueid2023/rosters"
        )
        assert result == 1


class TestGetRosterIds:
    """Unit tests for get_roster_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `mock_fetch_sleeper_data`: `fetch_sleeper_data`
        - `mock_get_roster_id`: `get_roster_id`

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.sleeper_helpers'
                '.fetch_sleeper_data'
            ) as mock_fetch_sleeper_data,
            patch(
                'patriot_center_backend.utils.sleeper_helpers'
                '.get_roster_id'
            ) as mock_get_roster_id
        ):

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_get_roster_id = mock_get_roster_id

            yield


    def test_get_roster_ids(self):
        """Test get_roster_ids function with valid data."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {'user_id': 'user1', 'display_name': 'username1'},
                {'user_id': 'user2', 'display_name': 'username2'},
            ],
            [
                {'owner_id': 'user1', 'roster_id': 1},
                {'owner_id': 'user2', 'roster_id': 2},
            ]
        ]
        self.mock_get_roster_id.side_effect = [1, 2]

        year = 2023
        result = get_roster_ids(year)

        assert result == {1: "Manager 1", 2: "Manager 2"}

    def test_calls_to_sleeper_correct(self):
        """Test get_roster_ids function with calls to Sleeper API correct."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {'user_id': 'user1', 'display_name': 'username1'},
                {'user_id': 'user2', 'display_name': 'username2'},
            ],
            [
                {'owner_id': 'user1', 'roster_id': 1},
                {'owner_id': 'user2', 'roster_id': 2},
            ]
        ]
        self.mock_get_roster_id.side_effect = [1, 2]

        year = 2023
        get_roster_ids(year)

        self.mock_fetch_sleeper_data.assert_any_call(
            "league/leagueid2023/users"
        )
        self.mock_fetch_sleeper_data.assert_any_call(
            "league/leagueid2023/rosters"
        )

    def test_calls_to_get_roster_id_correct(self):
        """Test get_roster_ids function with calls to get_roster_id correct."""
        sleeper_output_2 = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {'user_id': 'user1', 'display_name': 'username1'},
                {'user_id': 'user2', 'display_name': 'username2'},
            ],
            sleeper_output_2
        ]
        self.mock_get_roster_id.side_effect = [1, 2]

        year = 2023
        get_roster_ids(year)

        calls = self.mock_get_roster_id.call_args_list
        assert call(
            'user1', 2023, sleeper_rosters_response=sleeper_output_2
        ) in calls
        assert call(
            'user2', 2023, sleeper_rosters_response=sleeper_output_2
        ) in calls


class TestGetCurrentSeasonAndWeek:
    """Unit tests for get_current_season_and_week function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `mock_fetch_sleeper_data`: `fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.sleeper_helpers'
                '.fetch_sleeper_data'
            ) as mock_fetch_sleeper_data,
        ):

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_valid_middle_of_the_season(self):
        """Test returns the correct season and week number in valid data."""
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 2}
        }

        result = get_current_season_and_week()

        assert result == (2023, 2)

    def test_feth_sleeper_called_correct(self):
        """Test that fetch_sleeper_data is called with the correct arguments."""
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2024,
            'settings': {'last_scored_leg': 2}
        }

        get_current_season_and_week()

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/leagueid2024"
        )

    def test_valid_offseason(self):
        """Test get_current_season_and_week function with offseason data."""
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 17}
        }

        result = get_current_season_and_week()

        assert result == (2023, 17)

    def test_valid_preseason(self):
        """Test get_current_season_and_week function with preseason data."""
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
        }

        result = get_current_season_and_week()

        assert result == (2023, 0)
