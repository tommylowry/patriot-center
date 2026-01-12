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
    """
    Setup common mocks for all tests.

    These mocks include:

    - mock_league_ids: a mock of LEAGUE_IDS
    - mock_name_to_manager_username: a mock of NAME_TO_MANAGER_USERNAME
    - mock_username_to_real_name: a mock of USERNAME_TO_REAL_NAME

    The mocks are set up to return a pre-defined set of values when accessed.
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

    # Patch the mocks
    with patch('patriot_center_backend.utils.sleeper_helpers.LEAGUE_IDS', mock_league_ids), \
         patch('patriot_center_backend.utils.sleeper_helpers.USERNAME_TO_REAL_NAME', mock_username_to_real_name):
        yield


class TestFetchSleeperData:
    """Unit tests for fetch_sleeper_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        This fixture sets up the following mocks:

        - mock_get: a mock of requests.get

        The mocks are set up to return a pre-defined set of values when accessed.
        """
        with patch('patriot_center_backend.utils.sleeper_helpers.requests.get') as mock_get:
            self.mock_get = mock_get
            yield
    
    def test_fetch_sleeper_data(self):
        """
        Tests that the fetch_sleeper_data function calls the correct URL and returns the expected JSON response.
        """
        self.mock_get.return_value.json.return_value = {}
        self.mock_get.return_value.status_code = 200
        
        fetch_sleeper_data('test_endpoint')

        self.mock_get.assert_called_once_with('https://api.sleeper.app/v1/test_endpoint')
    
    def test_fetch_sleeper_data_connection_error(self):
        """
        Tests that the fetch_sleeper_data function raises a ConnectionAbortedError when the request to the Sleeper API fails.
        """
        self.mock_get.return_value.json.return_value = {}
        self.mock_get.return_value.status_code = 500
        
        with pytest.raises(ConnectionAbortedError,
                           match="Failed to fetch data from Sleeper API with call to https://api.sleeper.app/v1/test_endpoint"):
            fetch_sleeper_data('test_endpoint')


class TestGetRosterId:
    """Unit tests for get_roster_id function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        These mocks include:

        - mock_fetch_sleeper_data: a mock of fetch_sleeper_data function

        The mocks are set up to return a pre-defined set of values when accessed.
        """
        with patch('patriot_center_backend.utils.sleeper_helpers.fetch_sleeper_data') as mock_fetch_sleeper_data:
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            yield

    def test_get_roster_id(self):
        """
        Tests that the get_roster_id function returns the correct roster ID for a given user ID and year.
        """
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user1'
        year = 2023

        result = get_roster_id(user_id, year, sleeper_rosters_response)

        assert result == 1
    
    def test_2024_roster_id(self):
        """
        Check that the function correctly assigns the roster ID to the user in case the user ID is not found in the sleeper_rosters_response.
        """
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
        """
        Tests that the get_roster_id function does not call the Sleeper API if the sleeper_rosters_response is provided.
        """
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user1'
        year = 2023

        get_roster_id(user_id, year, sleeper_rosters_response)

        self.mock_fetch_sleeper_data.assert_not_called()
    
    def test_get_roster_id_not_found(self):
        """
        Create a mock sleeper_rosters_response with two users, and calls the get_roster_id function
        with the user ID 'user3', year 2023, and the mock sleeper_rosters_response. The test case then checks that the
        returned roster ID is None.
        """
        sleeper_rosters_response = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        user_id = 'user3'
        year = 2023

        result = get_roster_id(user_id, year, sleeper_rosters_response)

        assert result is None

    def test_no_sleeper_rosters_input(self):
        """
        Check that the get_roster_id function calls fetch_sleeper_data with the correct
        arguments when no sleeper_rosters_input is provided, and that the function returns the
        correct roster ID for the given user ID and year.
        """
        self.mock_fetch_sleeper_data.return_value = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        
        user_id = 'user1'
        year = 2023

        result = get_roster_id(user_id, year)

        self.mock_fetch_sleeper_data.assert_called_once_with(f"league/leagueid2023/rosters")
        assert result is 1


class TestGetRosterIds:
    """Unit tests for get_roster_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        These mocks include:

        - mock_fetch_sleeper_data: a mock of fetch_sleeper_data function
        - mock_get_roster_id: a mock of get_roster_id function

        The mocks are set up to return a pre-defined set of values when accessed.
        """
        with patch('patriot_center_backend.utils.sleeper_helpers.fetch_sleeper_data') as mock_fetch_sleeper_data, \
             patch('patriot_center_backend.utils.sleeper_helpers.get_roster_id') as mock_get_roster_id:
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_get_roster_id = mock_get_roster_id
            yield
    
    def test_get_roster_ids(self):
        """
        Test get_roster_ids function with valid data.
        """
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
        """
        Test get_roster_ids function with calls to Sleeper API correct.
        """
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

        self.mock_fetch_sleeper_data.assert_any_call(f"league/leagueid2023/users")
        self.mock_fetch_sleeper_data.assert_any_call(f"league/leagueid2023/rosters")
    
    def test_calls_to_get_roster_id_correct(self):
        """
        Test get_roster_ids function with calls to get_roster_id correct.
        """
        sleeper_output_2 = [
            {'owner_id': 'user1', 'roster_id': 1},
            {'owner_id': 'user2', 'roster_id': 2},
        ]
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {'user_id': 'user1', 'display_name': 'username1'},
                {'user_id': 'user2', 'display_name': 'username2'},
            ],sleeper_output_2
        ]
        self.mock_get_roster_id.side_effect = [1, 2]

        year = 2023
        get_roster_ids(year)

        calls = self.mock_get_roster_id.call_args_list
        assert call('user1', 2023, sleeper_rosters_response=sleeper_output_2) in calls
        assert call('user2', 2023, sleeper_rosters_response=sleeper_output_2) in calls

    def test_error_gets_raised_with_missing_rosters(self):
        """
        Checks that if one or more users are not found in the rosters data, an
        Exception is raised with the correct error message.
        """
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {'user_id': 'user1', 'display_name': 'username1'},
                {'user_id': 'user2', 'display_name': 'username2'},
                {'user_id': 'user3', 'display_name': 'username3'},
            ],
            [
                {'owner_id': 'user1', 'roster_id': 1},
                {'owner_id': 'user2', 'roster_id': 2},
                {'owner_id': None, 'roster_id': 3},
            ]
        ]
        self.mock_get_roster_id.side_effect = [1, 2, None]

        year = 2023

        with pytest.raises(Exception, match="Not all roster IDs are assigned "):
            get_roster_ids(year)


class TestGetCurrentSeasonAndWeek:
    """Unit tests for get_current_season_and_week function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup common mocks for all tests.

        This fixture sets up the following mocks:

        - mock_datetime: a mock of the datetime module
        - mock_fetch_sleeper_data: a mock of the fetch_sleeper_data function

        The mocks are yielded to each test, allowing them to be used as needed.
        """
        with patch('patriot_center_backend.utils.sleeper_helpers.datetime') as mock_datetime, \
             patch('patriot_center_backend.utils.sleeper_helpers.fetch_sleeper_data') as mock_fetch_sleeper_data:
            self.mock_datetime = mock_datetime
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            yield
    
    def test_valid_middle_of_the_season(self):
        """
        Test that get_current_season_and_week function returns the correct season and week number
        when given a valid middle of the season date.
        """
        self.mock_datetime.now.return_value.year = 2023
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 2}
        }

        result = get_current_season_and_week()

        assert result == (2023, 2)
    
    def test_feth_sleeper_called_correct(self):
        """
        Test that fetch_sleeper_data is called with the correct arguments.
        """
        self.mock_datetime.now.return_value.year = 2023
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 2}
        }

        get_current_season_and_week()

        self.mock_fetch_sleeper_data.assert_called_once_with(f"league/leagueid2023")

    def test_valid_offseason(self):
        """
        Test get_current_season_and_week function with offseason data.
        """
        self.mock_datetime.now.return_value.year = 2023
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 17}
        }

        result = get_current_season_and_week()

        assert result == (2023, 17)
    
    def test_valid_preseason(self):
        """
        Test get_current_season_and_week function with preseason data.
        """
        self.mock_datetime.now.return_value.year = 2023
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
        }

        result = get_current_season_and_week()

        assert result == (2023, 0)
    
    def test_old_league(self):
        """
        Test that get_current_season_and_week function returns the correct
        season and week number when given an old league ID.
        """
        self.mock_datetime.now.return_value.year = 2026
        self.mock_fetch_sleeper_data.return_value = {
            'season': 2023,
            'settings': {'last_scored_leg': 17}
        }

        result = get_current_season_and_week()

        assert result == (2023, 17)