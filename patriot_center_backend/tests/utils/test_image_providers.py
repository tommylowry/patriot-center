"""Unit tests for image_providers module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.utils.image_providers import (
    get_current_manager_image_url,
    get_image_url,
)


class TestGetImageUrl:
    """Test get_image_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.image_providers'
                '.CACHE_MANAGER.get_player_ids_cache'
            ) as mock_get_player_ids_cache,

            patch(
                'patriot_center_backend.utils.image_providers'
                '.CACHE_MANAGER.get_players_cache'
            ) as mock_get_players_cache,

            patch(
                'patriot_center_backend.utils.image_providers'
                '.get_current_manager_image_url'
            ) as mock_get_mgr_url,

            patch(
                'patriot_center_backend.utils.image_providers'
                '.NAME_TO_MANAGER_USERNAME',
                {"Manager 1": "user1"}
            ),
        ):

            self.mock_player_ids_cache = {}
            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache

            self.mock_players_cache = {}
            mock_get_players_cache.return_value = self.mock_players_cache

            self.mock_get_mgr_url = mock_get_mgr_url
            self.mock_get_mgr_url.return_value = ""

            yield

    def test_draft_pick_string_url(self):
        """Test draft pick returns NFL Draft logo URL."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        image_urls = {}

        result = get_image_url(item, image_urls)

        assert "NFL_Draft_logo" in result

    def test_draft_pick_dictionary(self):
        """Test draft pick returns dict when dictionary=True."""
        item = "Manager 1's 2023 Round 3 Draft Pick"
        image_urls = {}

        result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert "NFL_Draft_logo" in result["image_url"]
        assert result["first_name"] == "Manager"
        assert result["last_name"] == "1's 2023 R3"

    def test_faab_string_url(self):
        """Test FAAB returns Mario coin URL."""
        item = "$50 FAAB"
        image_urls = {}

        result = get_image_url(item, image_urls)

        assert "Mario-Coin" in result

    def test_faab_dictionary(self):
        """Test FAAB returns dict when dictionary=True."""
        item = "$50 FAAB"
        image_urls = {}

        result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert "Mario-Coin" in result["image_url"]
        assert result["first_name"] == "$50"
        assert result["last_name"] == "FAAB"

    def test_manager_string_url(self):
        """Test manager returns Sleeper avatar URL."""
        self.mock_get_mgr_url.return_value = (
            "http://sleepercdn.com/avatars/avatar123"
        )

        item = "Manager 1"
        image_urls = {}

        result = get_image_url(item, image_urls)

        assert result == "http://sleepercdn.com/avatars/avatar123"

    def test_manager_dictionary(self):
        """Test manager returns dict when dictionary=True."""
        self.mock_get_mgr_url.return_value = (
            "http://sleepercdn.com/avatars/avatar123"
        )

        item = "Manager 1"
        image_urls = {}

        result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == "http://sleepercdn.com/avatars/avatar123"
        assert result["name"] == "Manager 1"

    def test_player_numeric_id_url(self):
        """Test player with numeric ID returns player headshot URL."""
        self.mock_players_cache.update(
            {"Patrick Mahomes": {"player_id": "4046"}}
        )
        self.mock_player_ids_cache.update(
            {"4046": {"first_name": "Patrick", "last_name": "Mahomes"}}
        )

        item = "Patrick Mahomes"
        image_urls = {}

        result = get_image_url(item, image_urls)

        assert result == "https://sleepercdn.com/content/nfl/players/4046.jpg"

    def test_player_numeric_id_dictionary(self):
        """Test player with numeric ID returns dict when dictionary=True."""
        self.mock_players_cache.update(
            {"Patrick Mahomes": {"player_id": "4046"}}
        )
        self.mock_player_ids_cache.update(
            {"4046": {"first_name": "Patrick", "last_name": "Mahomes"}}
        )

        item = "Patrick Mahomes"
        image_urls = {}

        result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == (
            "https://sleepercdn.com/content/nfl/players/4046.jpg"
        )
        assert result["first_name"] == "Patrick"
        assert result["last_name"] == "Mahomes"

    def test_team_defense_url(self):
        """Test team defense (non-numeric ID) returns team logo URL."""
        self.mock_players_cache.update(
            {"Kansas City Chiefs": {"player_id": "KC"}}
        )
        self.mock_player_ids_cache.update(
            {"KC": {"first_name": "Kansas City", "last_name": "Chiefs"}}
        )

        item = "Kansas City Chiefs"
        image_urls = {}

        result = get_image_url(item, image_urls)

        assert result == "https://sleepercdn.com/images/team_logos/nfl/kc.png"

    def test_team_defense_dictionary(self):
        """Test team defense returns dict when dictionary=True."""
        self.mock_players_cache.update(
            {"Kansas City Chiefs": {"player_id": "KC"}}
        )
        self.mock_player_ids_cache.update(
            {"KC": {"first_name": "Kansas City", "last_name": "Chiefs"}}
        )

        item = "Kansas City Chiefs"
        image_urls = {}

        result = get_image_url(item, image_urls, dictionary=True)

        assert isinstance(result, dict)
        assert result["image_url"] == (
            "https://sleepercdn.com/images/team_logos/nfl/kc.png"
        )
        assert result["first_name"] == "Kansas City"
        assert result["last_name"] == "Chiefs"

    def test_unknown_item(self, caplog: pytest.LogCaptureFixture):
        """Test with unknown item returns empty string.

        Args:
            caplog: pytest caplog
        """
        item = "Unknown Item"
        image_urls = {}

        result = get_image_url(item, image_urls)

        # Verify warning was printed for unknown item
        assert "Could not find image URL" in caplog.text

        assert result == ""


class TestGetCurrentManagerImageUrl:
    """Test get_current_manager_image_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.utils.image_providers'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,

            patch(
                'patriot_center_backend.utils.image_providers'
                '.fetch_sleeper_data'
            ) as mock_fetch_sleeper,
        ):

            self.mock_manager_cache = {}
            mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_sleeper_data = {}
            mock_fetch_sleeper.return_value = self.mock_sleeper_data

            yield

    def test_manager_not_in_cache(self):
        """Test fetching manager image URL when not in cache."""
        self.mock_sleeper_data.update({"user_id": "12345", "avatar": "abc123"})
        self.mock_manager_cache.update(
            {"Manager 1": {"summary": {"user_id": "12345"}}}
        )

        manager = "Manager 1"
        image_urls = {}

        result = get_current_manager_image_url(manager, image_urls)

        assert result == "https://sleepercdn.com/avatars/abc123"
        assert image_urls["Manager 1"] == (
            "https://sleepercdn.com/avatars/abc123"
        )

    def test_manager_already_in_cache(self):
        """Test returning cached manager image URL."""
        manager = "Manager 1"
        image_urls = {"Manager 1": "https://sleepercdn.com/avatars/cached123"}

        result = get_current_manager_image_url(manager, image_urls)

        assert result == "https://sleepercdn.com/avatars/cached123"

    def test_missing_user_id(self):
        """Test when manager doesn't have user_id in cache."""
        self.mock_manager_cache.update(
            {"Manager 1": {"summary": {}}}
        )

        manager = "Manager 1"
        image_urls = {}

        with pytest.raises(
            ValueError, match="Manager 1 does not have a user_id in "
        ):
            get_current_manager_image_url(manager, image_urls)
