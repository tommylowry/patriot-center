"""Unit tests for _url_builders module."""

import logging
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters._url_builders import (
    build_draft_pick_url,
    build_faab_url,
    build_manager_url,
    build_player_id_url,
    build_player_url,
    build_url,
)


class TestBuildManagerUrl:
    """Test build_manager_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_user_metadata`: `mock_fetch_user_metadata`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.cache.updaters._url_builders"
            ".fetch_user_metadata"
        ) as mock_fetch_user_metadata:
            self.mock_fetch_user_metadata = mock_fetch_user_metadata
            self.mock_fetch_user_metadata.return_value = {
                "avatar": "abc123def456",
            }

            yield

    def test_returns_url_dict_with_avatar(self):
        """Test returns URL dict with avatar URL."""
        result = build_manager_url("Tommy")

        assert result["name"] == "Tommy"
        assert "sleepercdn.com/avatars/abc123def456" in result["image_url"]
        assert "timestamp" in result

    def test_returns_empty_dict_when_no_avatar(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when manager has no avatar.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_user_metadata.return_value = {}

        with caplog.at_level(logging.WARNING):
            result = build_manager_url("Tommy")

        assert result == {}
        assert "does not have an avatar" in caplog.text


class TestBuildDraftPickUrl:
    """Test build_draft_pick_url function."""

    def test_returns_correct_structure(self):
        """Test returns correct structure with name and image URL."""
        result = build_draft_pick_url("Tommy's 2024 Round 1 Draft Pick")

        assert result["name"] == "Tommy's 2024 Round 1 Draft Pick"
        assert "NFL_Draft_logo" in result["image_url"]
        assert result["first_name"] == "Tommy's"
        assert result["last_name"] == "2024 R1"

    def test_parses_multi_word_round(self):
        """Test correctly parses draft pick with multi-digit round."""
        result = build_draft_pick_url("Jay's 2025 Round 10 Draft Pick")

        assert result["first_name"] == "Jay's"
        assert result["last_name"] == "2025 R10"


class TestBuildFaabUrl:
    """Test build_faab_url function."""

    def test_returns_correct_structure(self):
        """Test returns correct structure with FAAB info."""
        result = build_faab_url("$10 FAAB")

        assert result["name"] == "$10 FAAB"
        assert "Mario-Coin" in result["image_url"]
        assert result["first_name"] == "$10"
        assert result["last_name"] == "FAAB"


class TestBuildPlayerIdUrl:
    """Test build_player_id_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`:
            `mock_get_player_ids_cache`
        - `get_player_name`: `mock_get_player_name`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".get_player_name"
            ) as mock_get_player_name,
        ):
            self.mock_player_ids_cache = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                },
            }
            mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )
            self.mock_get_player_name = mock_get_player_name
            self.mock_get_player_name.return_value = "Patrick Mahomes"

            yield

    def test_returns_nfl_player_url_for_numeric_id(self):
        """Test returns NFL player image URL for numeric player ID."""
        result = build_player_id_url("4046")

        assert "sleepercdn.com/content/nfl/players/4046.jpg" in (
            result["image_url"]
        )
        assert result["name"] == "Patrick Mahomes"

    def test_returns_team_logo_url_for_non_numeric_id(self):
        """Test returns team logo URL for non-numeric player ID."""
        self.mock_get_player_name.return_value = "Seattle Seahawks"
        self.mock_player_ids_cache["SEA"] = {
            "first_name": "Seattle",
            "last_name": "Seahawks",
        }

        result = build_player_id_url("SEA")

        assert "team_logos/nfl/sea.png" in result["image_url"]

    def test_returns_empty_dict_when_no_name(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when player has no full name.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_get_player_name.return_value = None

        with caplog.at_level(logging.WARNING):
            result = build_player_id_url("9999")

        assert result == {}
        assert "does not have a full name" in caplog.text


class TestBuildPlayerUrl:
    """Test build_player_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_player_id`: `mock_get_player_id`
        - `build_player_id_url`: `mock_build_player_id_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".get_player_id"
            ) as mock_get_player_id,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_player_id_url"
            ) as mock_build_player_id_url,
        ):
            self.mock_get_player_id = mock_get_player_id
            self.mock_get_player_id.return_value = "4046"

            self.mock_build_player_id_url = mock_build_player_id_url
            self.mock_build_player_id_url.return_value = {
                "name": "Patrick Mahomes",
                "image_url": "https://example.com/mahomes.jpg",
            }

            yield

    def test_delegates_to_build_player_id_url(self):
        """Test delegates to build_player_id_url with resolved ID."""
        result = build_player_url("Patrick Mahomes")

        self.mock_get_player_id.assert_called_once_with("Patrick Mahomes")
        self.mock_build_player_id_url.assert_called_once_with("4046")
        assert result["name"] == "Patrick Mahomes"

    def test_returns_empty_dict_when_no_player_id(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when player ID not found.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_get_player_id.return_value = None

        with caplog.at_level(logging.WARNING):
            result = build_player_url("Unknown Player")

        assert result == {}
        assert "does not have a player_id" in caplog.text


class TestBuildUrl:
    """Test build_url dispatcher function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `build_manager_url`: `mock_build_manager_url`
        - `build_draft_pick_url`: `mock_build_draft_pick_url`
        - `build_faab_url`: `mock_build_faab_url`
        - `build_player_id_url`: `mock_build_player_id_url`
        - `build_player_url`: `mock_build_player_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_manager_url"
            ) as mock_build_manager_url,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_draft_pick_url"
            ) as mock_build_draft_pick_url,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_faab_url"
            ) as mock_build_faab_url,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_player_id_url"
            ) as mock_build_player_id_url,
            patch(
                "patriot_center_backend.cache.updaters._url_builders"
                ".build_player_url"
            ) as mock_build_player_url,
        ):
            self.mock_build_manager_url = mock_build_manager_url
            self.mock_build_draft_pick_url = mock_build_draft_pick_url
            self.mock_build_faab_url = mock_build_faab_url
            self.mock_build_player_id_url = mock_build_player_id_url
            self.mock_build_player_url = mock_build_player_url

            yield

    def test_dispatches_to_manager_builder(self):
        """Test dispatches to build_manager_url for manager type."""
        build_url("Tommy", "manager")

        self.mock_build_manager_url.assert_called_once_with("Tommy")

    def test_dispatches_to_draft_pick_builder(self):
        """Test dispatches to build_draft_pick_url for draft_pick type."""
        build_url("Tommy's 2024 Round 1 Draft Pick", "draft_pick")

        self.mock_build_draft_pick_url.assert_called_once_with(
            "Tommy's 2024 Round 1 Draft Pick"
        )

    def test_dispatches_to_faab_builder(self):
        """Test dispatches to build_faab_url for faab type."""
        build_url("$10 FAAB", "faab")

        self.mock_build_faab_url.assert_called_once_with("$10 FAAB")

    def test_dispatches_to_player_id_builder(self):
        """Test dispatches to build_player_id_url for player_id type."""
        build_url("4046", "player_id")

        self.mock_build_player_id_url.assert_called_once_with("4046")

    def test_dispatches_to_player_builder(self):
        """Test dispatches to build_player_url for player type."""
        build_url("Patrick Mahomes", "player")

        self.mock_build_player_url.assert_called_once_with("Patrick Mahomes")
