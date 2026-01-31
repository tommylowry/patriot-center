"""Unit tests for player_cache_updater module."""

from copy import deepcopy
from unittest.mock import call, patch

import pytest

from patriot_center_backend.cache.updaters.player_cache_updater import (
    update_players_cache,
    update_players_cache_with_list,
)


class TestUpdatePlayersCache:
    """Test update_players_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `update_image_urls_cache`: `mock_update_image_urls_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_cache_updater"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_cache_updater"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_cache_updater"
                ".update_image_urls_cache"
            ) as mock_update_image_urls_cache,
        ):
            self.mock_player_ids_cache = {}
            self.mock_players_cache = {}

            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache
            mock_get_players_cache.return_value = self.mock_players_cache

            self.mock_update_image_urls_cache = mock_update_image_urls_cache

            yield

    def test_update_with_single_player_id(self):
        """Updates the players cache with a single player_id."""
        self.mock_player_ids_cache.update(
            {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                    "team": "KC",
                }
            }
        )

        item = "4046"
        update_players_cache(item)

        assert "Patrick Mahomes" in self.mock_players_cache

        player_check = self.mock_players_cache["Patrick Mahomes"]
        assert player_check["player_id"] == "4046"
        assert player_check["position"] == "QB"
        assert player_check["slug"] == "patrick%20mahomes"

    def test_update_with_apostrophe_in_name(self):
        """Updates player cache with player_id of player with apostrophe."""
        self.mock_player_ids_cache.update(
            {
                "5678": {
                    "full_name": "D'Andre Swift",
                    "first_name": "D'Andre",
                    "last_name": "Swift",
                    "position": "RB",
                    "team": "PHI",
                }
            }
        )

        item = "5678"
        update_players_cache(item)

        assert "D'Andre Swift" in self.mock_players_cache

        # Check that the slug attribute is set correctly
        assert self.mock_players_cache["D'Andre Swift"]["slug"] == (
            "d%27andre%20swift"
        )

    def test_player_already_in_cache(self):
        """Update players cache when player is already in cache."""
        self.mock_players_cache.update(
            {
                "Patrick Mahomes": {
                    "player_id": "4046",
                    "position": "QB",
                    "slug": "patrick%20mahomes",
                }
            }
        )
        self.mock_player_ids_cache.update(
            {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                    "team": "KC",
                }
            }
        )

        # Create a deep copy of the original cache
        original_cache = deepcopy(self.mock_players_cache)

        item = "4046"
        update_players_cache(item)

        # Cache should remain unchanged
        assert self.mock_players_cache == original_cache

    def test_player_not_in_player_ids(self, caplog: pytest.LogCaptureFixture):
        """Test update_players_cache gives warning when not in player_ids.

        Args:
            caplog: pytest caplog
        """
        item = "9999"
        update_players_cache(item)

        # Verify warning was logged for player not in player_ids
        assert "player_id 9999 not found" in caplog.text

        # Should handle gracefully - player won't be added since no metadata
        assert len(self.mock_players_cache) == 0

    def test_update_with_none_raises_error(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test update_players_cache logs a warning when given empty string.

        Args:
            caplog: pytest caplog
        """
        item = ""
        update_players_cache(item)

        # Verify warning was logged for player not in player_ids
        assert "not found in player_ids" in caplog.text


class TestUpdatePlayersCacheWithList:
    """Test update_players_cache_with_list function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `update_players_cache`: `mock_update_players`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_cache_updater"
                ".update_players_cache"
            ) as mock_update_players,
        ):
            self.mock_update_players = mock_update_players

            yield

    def test_update_with_valid_matchup(self):
        """Test updates the players cache correctly with valid matchups."""
        item = [{"players": ["4046", "5678"]}, {"players": ["9999"]}]
        update_players_cache_with_list(item)

        # Verify that the correct player IDs were passed to update_players_cache
        calls = self.mock_update_players.call_args_list
        assert call("4046") in calls, "4046 not found in calls"
        assert call("5678") in calls, "5678 not found in calls"
        assert call("9999") in calls, "9999 not found in calls"

    def test_update_with_list_passes_any_type(self):
        """Test calls update_players_cache when given a list with any type."""
        item = [{"players": [123]}]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with(123)

    def test_update_ignores_non_dict_types(self):
        """Test that ignores non-dict types in the input list."""
        item = [{"players": ["4046"]}, "invalid type in list"]
        update_players_cache_with_list(item)

        # Check that update_players_cache was called with the correct player ID
        self.mock_update_players.assert_called_once_with("4046")

    def test_warns_with_invalid_item(self, caplog: pytest.LogCaptureFixture):
        """Test handles warning when given invalid item.

        Args:
            caplog: pytest caplog
        """
        item = "invalid input type"
        update_players_cache_with_list(item)  # type: ignore

        # Verify warning prints
        assert "is not a list" in caplog.text

        # Verify update_players_cache was not called
        self.mock_update_players.assert_not_called()

    def test_warns_when_update_not_called(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test handles warning when given invalid item in list.

        Args:
            caplog: pytest caplog
        """
        item = ["invalid type in list"]
        update_players_cache_with_list(item)  # type: ignore

        # Verify warning prints
        assert "did not have a matchup dict with players" in caplog.text

        # Verify update_players_cache was not called
        self.mock_update_players.assert_not_called()
