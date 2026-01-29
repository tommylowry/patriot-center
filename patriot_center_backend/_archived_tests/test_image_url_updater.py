"""Unit tests for image_url_updater module."""

from time import time
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.image_urls_updater import (
    _get_current_manager_image_url,
    get_image_url,
    update_image_urls_cache,
)


class TestUpdateImageUrlsCache:
    """Test update_image_urls_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_image_urls_cache`: `mock_get_image_urls_cache`
        - `CACHE_MANAGER.save_image_urls_cache`: `mock_save_image_urls_cache`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `NAME_TO_MANAGER_USERNAME`: `mock_name_to_manager_username`
        - `_get_current_manager_image_url`: `mock_get_current_manager_image_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.save_image_urls_cache"
            ) as mock_save_image_urls_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".NAME_TO_MANAGER_USERNAME",
                {"Tommy": "tommy_username"},
            ),
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                "._get_current_manager_image_url"
            ) as mock_get_current_manager_image_url,
        ):
            self.mock_image_urls_cache = {}
            self.mock_get_image_urls_cache = mock_get_image_urls_cache
            self.mock_get_image_urls_cache.return_value = (
                self.mock_image_urls_cache
            )

            self.mock_save_image_urls_cache = mock_save_image_urls_cache

            self.mock_players_cache = {}
            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = self.mock_players_cache

            self.mock_player_ids_cache = {}
            self.mock_get_player_ids_cache = mock_get_player_ids_cache
            self.mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )

            self.mock_get_manager_image_url = mock_get_current_manager_image_url
            self.mock_get_manager_image_url.return_value = (
                "https://sleepercdn.com/avatars/abc123"
            )

            yield

    def test_manager_item_fetches_new_image_url(self):
        """Test that manager items fetch new image URL when not cached."""
        result = update_image_urls_cache("Tommy")

        assert result["name"] == "Tommy"
        assert result["image_url"] == "https://sleepercdn.com/avatars/abc123"
        assert "timestamp" not in result
        self.mock_save_image_urls_cache.assert_called_once()

    def test_manager_item_uses_cached_value_if_fresh(self):
        """Test that manager items use cached value if less than 1 hour old."""
        self.mock_image_urls_cache["Tommy"] = {
            "name": "Tommy",
            "image_url": "https://cached.url/image.jpg",
            "timestamp": time(),
        }

        result = update_image_urls_cache("Tommy")

        assert result["image_url"] == "https://cached.url/image.jpg"
        self.mock_get_manager_image_url.assert_not_called()
        self.mock_save_image_urls_cache.assert_not_called()

    def test_manager_item_refetches_if_stale(self):
        """Test that manager items refetch if more than 1 hour old."""
        self.mock_image_urls_cache["Tommy"] = {
            "name": "Tommy",
            "image_url": "https://old.url/image.jpg",
            "timestamp": time() - 3700,
        }

        result = update_image_urls_cache("Tommy")

        assert result["image_url"] == "https://sleepercdn.com/avatars/abc123"
        self.mock_get_manager_image_url.assert_called_once_with("Tommy")
        self.mock_save_image_urls_cache.assert_called_once()

    def test_draft_pick_item_returns_correct_format(self):
        """Test that draft pick items return correctly formatted data."""
        result = update_image_urls_cache("Round 1 2024 Draft Pick")

        assert result["name"] == "Round 1 2024 Draft Pick"
        assert "NFL_Draft_logo" in result["image_url"]
        assert result["first_name"] == "R1"
        assert result["last_name"] == "2024"

    def test_faab_item_returns_correct_format(self):
        """Test that FAAB items return correctly formatted data."""
        result = update_image_urls_cache("$50 FAAB")

        assert result["name"] == "$50 FAAB"
        assert "Mario-Coin" in result["image_url"]
        assert result["first_name"] == "$50"
        assert result["last_name"] == "FAAB"

    def test_player_with_numeric_id_returns_headshot_url(self):
        """Test that players with numeric IDs return player headshot URLs."""
        self.mock_players_cache["Patrick Mahomes"] = {
            "player_id": "4046",
        }
        self.mock_player_ids_cache["4046"] = {
            "first_name": "Patrick",
            "last_name": "Mahomes",
        }

        result = update_image_urls_cache("Patrick Mahomes")

        assert result["name"] == "Patrick Mahomes"
        assert (
            "sleepercdn.com/content/nfl/players/4046.jpg"
            in (result["image_url"])
        )
        assert result["first_name"] == "Patrick"
        assert result["last_name"] == "Mahomes"

    def test_player_with_non_numeric_id_returns_team_logo_url(self):
        """Test that players with non-numeric IDs return team logo URLs."""
        self.mock_players_cache["Kansas City Chiefs"] = {
            "player_id": "KC",
        }
        self.mock_player_ids_cache["KC"] = {
            "first_name": "Kansas City",
            "last_name": "Chiefs",
        }

        result = update_image_urls_cache("Kansas City Chiefs")

        assert result["name"] == "Kansas City Chiefs"
        assert (
            "sleepercdn.com/images/team_logos/nfl/kc.png"
            in (result["image_url"])
        )

    def test_player_id_directly_in_player_ids_cache(self):
        """Test that player_id passed directly works if in player_ids_cache."""
        self.mock_player_ids_cache["4046"] = {
            "first_name": "Patrick",
            "last_name": "Mahomes",
        }

        result = update_image_urls_cache("4046")

        assert result["name"] == "4046"
        assert (
            "sleepercdn.com/content/nfl/players/4046.jpg"
            in (result["image_url"])
        )

    def test_unknown_item_returns_empty_dict(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that unknown items return empty dict and log warning.

        Args:
            caplog: pytest caplog fixture
        """
        result = update_image_urls_cache("Unknown Item")

        assert result == {}
        assert "Could not find image URL for item: Unknown Item" in caplog.text


class TestGetImageUrl:
    """Test get_image_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_image_urls_cache`: `mock_get_image_urls_cache`
        - `NAME_TO_MANAGER_USERNAME`: `mock_name_to_manager_username`
        - `update_image_urls_cache`: `mock_update_image_urls_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".NAME_TO_MANAGER_USERNAME",
                {"Tommy": "tommy_username"},
            ),
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".update_image_urls_cache"
            ) as mock_update_image_urls_cache,
        ):
            self.mock_image_urls_cache = {}
            self.mock_get_image_urls_cache = mock_get_image_urls_cache
            self.mock_get_image_urls_cache.return_value = (
                self.mock_image_urls_cache
            )

            self.mock_update_image_urls_cache = mock_update_image_urls_cache
            self.mock_update_image_urls_cache.return_value = {
                "name": "Test",
                "image_url": "https://test.url/image.jpg",
            }

            yield

    def test_manager_item_calls_update_and_returns_string(self):
        """Test that manager items call update and return string by default."""
        self.mock_update_image_urls_cache.return_value = {
            "name": "Tommy",
            "image_url": "https://tommy.url/image.jpg",
        }

        result = get_image_url("Tommy")

        assert result == "https://tommy.url/image.jpg"
        self.mock_update_image_urls_cache.assert_called_once_with("Tommy")

    def test_manager_item_returns_dict_when_dictionary_true(self):
        """Test that manager items return dict when dictionary=True."""
        self.mock_update_image_urls_cache.return_value = {
            "name": "Tommy",
            "image_url": "https://tommy.url/image.jpg",
        }

        result = get_image_url("Tommy", dictionary=True)

        assert isinstance(result, dict)
        assert result["name"] == "Tommy"
        assert result["image_url"] == "https://tommy.url/image.jpg"

    def test_cached_item_returns_string_by_default(self):
        """Test that cached items return string by default."""
        self.mock_image_urls_cache["Patrick Mahomes"] = {
            "name": "Patrick Mahomes",
            "image_url": "https://cached.url/image.jpg",
        }

        result = get_image_url("Patrick Mahomes")

        assert result == "https://cached.url/image.jpg"
        self.mock_update_image_urls_cache.assert_not_called()

    def test_cached_item_returns_dict_when_dictionary_true(self):
        """Test that cached items return dict when dictionary=True."""
        self.mock_image_urls_cache["Patrick Mahomes"] = {
            "name": "Patrick Mahomes",
            "image_url": "https://cached.url/image.jpg",
            "first_name": "Patrick",
            "last_name": "Mahomes",
            "timestamp": time(),
        }

        result = get_image_url("Patrick Mahomes", dictionary=True)

        assert isinstance(result, dict)
        assert result["name"] == "Patrick Mahomes"
        assert "timestamp" not in result

    def test_uncached_item_calls_update(self):
        """Test that uncached items call update_image_urls_cache."""
        result = get_image_url("Unknown Player")

        self.mock_update_image_urls_cache.assert_called_once_with(
            "Unknown Player"
        )
        assert result == "https://test.url/image.jpg"

    def test_invalid_cached_image_url_recaches(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that invalid cached image_url triggers recache.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_image_urls_cache["Bad Entry"] = {
            "name": "Bad Entry",
            "image_url": 12345,
        }

        get_image_url("Bad Entry")

        assert "is not a string" in caplog.text


class TestGetCurrentManagerImageUrl:
    """Test _get_current_manager_image_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_url_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
        ):
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_returns_avatar_url_for_valid_manager(self):
        """Test returns correct avatar URL for valid manager."""
        self.mock_manager_cache["Tommy"] = {
            "summary": {"user_id": "user123"},
        }
        self.mock_fetch_sleeper_data.return_value = {"avatar": "abc123"}

        result = _get_current_manager_image_url("Tommy")

        assert result == "https://sleepercdn.com/avatars/abc123"
        self.mock_fetch_sleeper_data.assert_called_once_with("user/user123")

    def test_returns_empty_string_when_no_user_id(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty string when manager has no user_id.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_manager_cache["Tommy"] = {"summary": {}}

        result = _get_current_manager_image_url("Tommy")

        assert result == ""
        assert "does not have a user_id" in caplog.text

    def test_returns_empty_string_when_manager_not_in_cache(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty string when manager not in cache.

        Args:
            caplog: pytest caplog fixture
        """
        result = _get_current_manager_image_url("Unknown Manager")

        assert result == ""
        assert "does not have a user_id" in caplog.text

    def test_returns_empty_string_when_api_fails(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty string when Sleeper API fails.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_manager_cache["Tommy"] = {
            "summary": {"user_id": "user123"},
        }
        self.mock_fetch_sleeper_data.return_value = []

        result = _get_current_manager_image_url("Tommy")

        assert result == ""
        assert "Sleeper API call failed" in caplog.text

    def test_returns_empty_string_when_no_avatar_in_response(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty string when API response has no avatar.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_manager_cache["Tommy"] = {
            "summary": {"user_id": "user123"},
        }
        self.mock_fetch_sleeper_data.return_value = {"display_name": "tommy"}

        result = _get_current_manager_image_url("Tommy")

        assert result == ""
        assert "does not have an avatar" in caplog.text
