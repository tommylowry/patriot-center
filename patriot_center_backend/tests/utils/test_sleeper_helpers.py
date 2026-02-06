"""Unit tests for sleeper_helpers module."""

import logging
from unittest.mock import patch

import pytest

from patriot_center_backend.utils.sleeper_helpers import (
    fetch_all_player_ids,
    fetch_sleeper_data,
    fetch_user_metadata,
    get_league_info,
    get_playoff_roster_ids,
    get_roster_id,
    get_roster_ids,
    get_season_state,
)

MODULE_PATH = "patriot_center_backend.utils.sleeper_helpers"

@pytest.fixture(autouse=True)
def globals_setup():
    """Setup common mocks for all tests.

    The mocks are set up to return a pre-defined
    set of values when accessed.
    - `LEAGUE_IDS`: `{2023: "league123"}`

    Yields:
        None
    """
    with patch(f"{MODULE_PATH}.LEAGUE_IDS", {2023: "league123"}):
        yield

class TestFetchSleeperData:
    """Test fetch_sleeper_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `SLEEPER_CLIENT.fetch`: `mock_sleeper_client_fetch`

        Yields:
            None
        """
        with patch(f"{MODULE_PATH}.SLEEPER_CLIENT") as mock_sleeper_client:
            self.mock_sleeper_client = mock_sleeper_client
            self.mock_sleeper_client.fetch.return_value = {"data": "value"}

            yield

    def test_returns_parsed_json(self):
        """Test returns parsed JSON from API."""
        result = fetch_sleeper_data("league/123")

        assert result == {"data": "value"}

    def test_delegates_to_sleeper_client(self):
        """Test delegates to SLEEPER_CLIENT.fetch with correct args."""
        fetch_sleeper_data("league/123/rosters")

        self.mock_sleeper_client.fetch.assert_called_once_with(
            "league/123/rosters", bypass_cache=False
        )

    def test_passes_bypass_cache_to_client(self):
        """Test passes bypass_cache parameter to SLEEPER_CLIENT."""
        fetch_sleeper_data("league/123", bypass_cache=True)

        self.mock_sleeper_client.fetch.assert_called_once_with(
            "league/123", bypass_cache=True
        )


class TestGetPlayoffRosterIds:
    """Test get_playoff_roster_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".LEAGUE_IDS", {
                    2019: "league2019", 2020: "league2020", 2024: "league2024"
                }
            ),
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_returns_empty_list_for_regular_season_pre_2021(self):
        """Test returns empty list for regular season weeks pre-2021."""
        result = get_playoff_roster_ids(2020, 13)

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_returns_empty_list_for_regular_season_2021_plus(self):
        """Test returns empty list for regular season weeks 2021+."""
        result = get_playoff_roster_ids(2024, 14)

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_fetches_winners_bracket_for_playoff_week_pre_2021(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2019, 14)

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league2019/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_fetches_winners_bracket_for_championship_pre_2021(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 3, "t1": 1, "t2": 2},
            {"r": 3, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2019, 16)

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league2019/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_fetches_winners_bracket_for_playoff_week(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2024, 15)

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league2024/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_excludes_consolation_matchups(self):
        """Test excludes consolation bracket matchups (p=5)."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4, "p": 5},
        ]

        result = get_playoff_roster_ids(2024, 15)

        assert 3 not in result
        assert 4 not in result

    def test_raises_error_for_week_17_pre_2021(self):
        """Test raises ValueError for week 17 in pre-2021 seasons."""
        self.mock_fetch_sleeper_data.return_value = []

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2020, 17)

        assert "Cannot get playoff roster IDs for week 17" in str(
            exc_info.value
        )

    def test_raises_error_when_api_returns_non_list(self):
        """Test raises ValueError when API returns non-list."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2024, 15)

        assert "Cannot get playoff roster IDs" in str(exc_info.value)

    def test_raises_error_when_no_rosters_found(self):
        """Test raises ValueError when no rosters found for round."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 2, "t1": 1, "t2": 2},
        ]

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2024, 15)

        assert "Cannot get playoff roster IDs" in str(exc_info.value)


class TestGetSeasonState:
    """Test get_season_state function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.utils.formatters.fetch_sleeper_data"
        ) as mock_fetch_sleeper:
            self.mock_fetch_sleeper = mock_fetch_sleeper

            yield

    def test_regular_season(self):
        """Test regular season detection."""
        week = "5"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        self.mock_fetch_sleeper.assert_not_called()

    def test_playoffs(self):
        """Test playoff detection."""
        week = "15"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"
        self.mock_fetch_sleeper.assert_not_called()

    def test_playoffs_late_week(self):
        """Test playoff detection in late weeks."""
        week = "17"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"

    def test_fetch_playoff_week_from_api(self):
        """Test fetching playoff_week_start from API when not provided."""
        self.mock_fetch_sleeper.return_value = {
            "settings": {"playoff_week_start": 15}
        }

        week = "10"
        year = "2023"
        playoff_week_start = None

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        self.mock_fetch_sleeper.assert_called_once_with("league/league123")

    def test_missing_week_raises_error(self):
        """Test that missing week raises ValueError."""
        week = None
        year = "2023"
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)  # type: ignore

    def test_empty_week_raises_error(self):
        """Test that empty week raises ValueError."""
        week = ""
        year = "2023"
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_missing_year_raises_error(self):
        """Test that missing year raises ValueError."""
        week = "5"
        year = None
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)  # type: ignore

    def test_empty_year_raises_error(self):
        """Test that empty year raises ValueError."""
        week = "5"
        year = ""
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_boundary_week_before_playoffs(self):
        """Test week just before playoffs."""
        week = "14"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"


class TestGetRosterId:
    """Test get_roster_id function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.fetch_sleeper_data") as mock_fetch,
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch

            yield

    def test_returns_roster_id_for_matching_user(self):
        """Test returns roster ID when user_id matches."""
        rosters = [
            {"owner_id": "user_1", "roster_id": 1},
            {"owner_id": "user_2", "roster_id": 2},
        ]

        result = get_roster_id("user_1", 2024, sleeper_rosters_response=rosters)

        assert result == 1

    def test_returns_none_when_user_not_found(self, caplog):
        """Test returns None when user ID not found in rosters.

        Args:
            caplog: pytest caplog fixture
        """
        rosters = [
            {"owner_id": "user_1", "roster_id": 1},
        ]

        with caplog.at_level(logging.WARNING):
            result = get_roster_id(
                "user_999", 2024, sleeper_rosters_response=rosters
            )

        assert result is None
        assert "not found in rosters" in caplog.text

    def test_fetches_rosters_when_not_provided(self):
        """Test fetches rosters from API when not provided."""
        self.mock_fetch_sleeper_data.return_value = [
            {"owner_id": "user_1", "roster_id": 1},
        ]

        result = get_roster_id("user_1", 2024)

        assert result == 1
        self.mock_fetch_sleeper_data.assert_called_once()

    def test_raises_when_api_returns_non_list(self):
        """Test raises ValueError when API returns non-list."""
        self.mock_fetch_sleeper_data.return_value = {"error": True}

        with pytest.raises(ValueError) as exc_info:
            get_roster_id("user_1", 2024)

        assert "list form" in str(exc_info.value)

    def test_2024_special_case_assigns_skipped_roster(self, caplog):
        """Test 2024 special case assigns missing owner roster.

        Args:
            caplog: pytest caplog fixture
        """
        rosters = [
            {"owner_id": "user_1", "roster_id": 1},
            {"owner_id": None, "roster_id": 2},
        ]

        with caplog.at_level(logging.WARNING):
            result = get_roster_id(
                "user_999", 2024, sleeper_rosters_response=rosters
            )

        assert result == 2


class TestGetRosterIds:
    """Test get_roster_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `LEAGUE_IDS`: mock league IDs
        - `USERNAME_TO_REAL_NAME`: mock username mapping

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.fetch_sleeper_data") as mock_fetch,
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024", 2019: "league2019"},
            ),
            patch(
                f"{MODULE_PATH}.USERNAME_TO_REAL_NAME",
                {
                    "tommylowry": "Tommy",
                    "Jrazzam": "Jay",
                    "codestoppable": "Cody",
                },
            ),
            patch(f"{MODULE_PATH}.get_user_id") as mock_get_user_id,
        ):
            self.mock_fetch_sleeper_data = mock_fetch
            self.mock_get_user_id = mock_get_user_id

            # Default: users call then rosters call
            self.mock_fetch_sleeper_data.side_effect = [
                # Users response
                [
                    {"user_id": "u1", "display_name": "tommylowry"},
                    {"user_id": "u2", "display_name": "Jrazzam"},
                ],
                # Rosters response
                [
                    {"owner_id": "u1", "roster_id": 1},
                    {"owner_id": "u2", "roster_id": 2},
                ],
            ]

            yield

    def test_returns_roster_id_to_name_mapping(self):
        """Test returns mapping of roster IDs to real names."""
        result = get_roster_ids(2024, 1)

        assert result == {1: "Tommy", 2: "Jay"}

    def test_raises_when_users_api_returns_non_list(self):
        """Test raises ValueError when users API returns non-list."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"error": True},
        ]

        with pytest.raises(ValueError) as exc_info:
            get_roster_ids(2024, 1)

        assert "users in list form" in str(exc_info.value)

    def test_raises_when_rosters_api_returns_non_list(self):
        """Test raises ValueError when rosters API returns non-list."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {"user_id": "u1", "display_name": "tommylowry"},
            ],
            {"error": True},
        ]

        with pytest.raises(ValueError) as exc_info:
            get_roster_ids(2024, 1)

        assert "rosters in list form" in str(exc_info.value)

    def test_2024_assigns_davey_for_none_owner(self):
        """Test 2024 special case assigns Davey for None owner_id."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {"user_id": "u1", "display_name": "tommylowry"},
                {"user_id": "u2", "display_name": "Jrazzam"},
            ],
            [
                {"owner_id": "u1", "roster_id": 1},
                {"owner_id": None, "roster_id": 2},
            ],
        ]

        result = get_roster_ids(2024, 1)

        assert result[2] == "Davey"

    def test_2019_replaces_cody_with_tommy_weeks_1_3(self):
        """Test 2019 special case replaces Cody with Tommy in weeks 1-3."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {"user_id": "u1", "display_name": "codestoppable"},
                {"user_id": "u2", "display_name": "Jrazzam"},
            ],
            [
                {"owner_id": "u1", "roster_id": 1},
                {"owner_id": "u2", "roster_id": 2},
            ],
        ]

        result = get_roster_ids(2019, 2)

        assert result[1] == "Tommy"


class TestGetLeagueInfo:
    """Test get_league_info function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.fetch_sleeper_data") as mock_fetch,
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch
            self.mock_fetch_sleeper_data.return_value = {
                "league_id": "league2024",
                "settings": {"waiver_type": 2},
            }

            yield

    def test_returns_league_info(self):
        """Test returns league info dict."""
        result = get_league_info(2024)

        assert result["league_id"] == "league2024"

    def test_raises_when_no_league_id(self):
        """Test raises ValueError when no league ID for year."""
        with pytest.raises(ValueError) as exc_info:
            get_league_info(2018)

        assert "No league ID found" in str(exc_info.value)

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.return_value = "not_a_dict"

        with pytest.raises(ValueError) as exc_info:
            get_league_info(2024)

        assert "failed to retrieve league info" in str(exc_info.value)


class TestFetchUserMetadata:
    """Test fetch_user_metadata function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_user_id`: `mock_get_user_id`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(f"{MODULE_PATH}.get_user_id") as mock_get_user_id,
            patch(f"{MODULE_PATH}.fetch_sleeper_data") as mock_fetch,
        ):
            self.mock_get_user_id = mock_get_user_id
            self.mock_get_user_id.return_value = "123456789"

            self.mock_fetch_sleeper_data = mock_fetch
            self.mock_fetch_sleeper_data.return_value = {
                "user_id": "123456789",
                "display_name": "tommylowry",
                "avatar": "abc123",
            }

            yield

    def test_returns_user_metadata(self):
        """Test returns user metadata dict."""
        result = fetch_user_metadata("Tommy")

        assert result["user_id"] == "123456789"
        assert result["display_name"] == "tommylowry"

    def test_raises_when_no_user_id(self):
        """Test raises ValueError when no user ID found."""
        self.mock_get_user_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            fetch_user_metadata("Unknown")

        assert "No user ID found" in str(exc_info.value)

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.return_value = "not_a_dict"

        with pytest.raises(ValueError) as exc_info:
            fetch_user_metadata("Tommy")

        assert "failed to retrieve user info" in str(exc_info.value)

    def test_raises_when_api_returns_empty(self):
        """Test raises ValueError when API returns empty response."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            fetch_user_metadata("Tommy")

        assert "failed to retrieve user info" in str(exc_info.value)

    def test_passes_bypass_cache_to_fetch(self):
        """Test passes bypass_cache parameter to fetch_sleeper_data."""
        fetch_user_metadata("Tommy", bypass_cache=True)

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "user/123456789", bypass_cache=True
        )

    def test_default_bypass_cache_is_false(self):
        """Test default bypass_cache is False."""
        fetch_user_metadata("Tommy")

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "user/123456789", bypass_cache=False
        )


class TestFetchAllPlayerIds:
    """Test fetch_all_player_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with patch(f"{MODULE_PATH}.fetch_sleeper_data") as mock_fetch:
            self.mock_fetch_sleeper_data = mock_fetch
            self.mock_fetch_sleeper_data.return_value = {
                "4046": {"full_name": "Patrick Mahomes"},
                "6794": {"full_name": "Jayden Daniels"},
            }

            yield

    def test_returns_player_ids_dict(self):
        """Test returns player IDs dictionary."""
        result = fetch_all_player_ids()

        assert "4046" in result
        assert result["4046"]["full_name"] == "Patrick Mahomes"

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.return_value = "not_a_dict"

        with pytest.raises(ValueError) as exc_info:
            fetch_all_player_ids()

        assert "failed to retrieve player info" in str(exc_info.value)

    def test_raises_when_api_returns_empty(self):
        """Test raises ValueError when API returns empty response."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            fetch_all_player_ids()

        assert "failed to retrieve player info" in str(exc_info.value)
