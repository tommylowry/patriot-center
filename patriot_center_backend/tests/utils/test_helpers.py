"""Unit tests for helpers module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.utils.helpers import (
    get_player_id,
    get_player_name,
    get_player_position,
    get_user_id,
    recursive_replace,
)

MODULE_PATH = "patriot_center_backend.utils.helpers"


class TestGetPlayerId:
    """Test get_player_id function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`:
            `mock_get_player_ids_cache`

        Yields:
            None
        """
        # Clear the LRU cache before each test
        from patriot_center_backend.utils.helpers import _get_player_name_to_id

        _get_player_name_to_id.cache_clear()

        with patch(
            f"{MODULE_PATH}.CACHE_MANAGER.get_player_ids_cache"
        ) as mock_get_player_ids_cache:
            self.mock_player_ids_cache: dict[str, Any] = {
                "4046": {"full_name": "Patrick Mahomes"},
                "6794": {"full_name": "Jayden Daniels"},
            }
            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache

            yield

    def test_returns_id_for_known_player(self):
        """Test returns player ID for known player name."""
        result = get_player_id("Patrick Mahomes")

        assert result == "4046"

    def test_returns_none_for_unknown_player(self):
        """Test returns None for unknown player name."""
        result = get_player_id("Unknown Player")

        assert result is None

    def test_returns_correct_id_for_second_player(self):
        """Test returns correct ID for another player."""
        result = get_player_id("Jayden Daniels")

        assert result == "6794"


class TestGetPlayerName:
    """Test get_player_name function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`:
            `mock_get_player_ids_cache`

        Yields:
            None
        """
        with patch(
            f"{MODULE_PATH}.CACHE_MANAGER.get_player_ids_cache"
        ) as mock_get_player_ids_cache:
            self.mock_player_ids_cache: dict[str, Any] = {
                "4046": {"full_name": "Patrick Mahomes"},
            }
            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache

            yield

    def test_returns_name_for_known_id(self):
        """Test returns player name for known player ID."""
        result = get_player_name("4046")

        assert result == "Patrick Mahomes"

    def test_returns_none_for_unknown_id(self):
        """Test returns None for unknown player ID."""
        result = get_player_name("9999")

        assert result is None


class TestGetPlayerPosition:
    """Test get_player_position function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`:
            `mock_get_player_ids_cache`

        Yields:
            None
        """
        with patch(
            f"{MODULE_PATH}.CACHE_MANAGER.get_player_ids_cache"
        ) as mock_get_player_ids_cache:
            self.mock_player_ids_cache: dict[str, Any] = {
                "4046": {"full_name": "Patrick Mahomes", "position": "QB"},
            }
            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache

            yield

    def test_returns_position_for_known_id(self):
        """Test returns player position for known player ID."""
        result = get_player_position("4046")

        assert result == "QB"

    def test_returns_none_for_unknown_id(self):
        """Test returns None for unknown player ID."""
        result = get_player_position("9999")

        assert result is None


class TestGetUserId:
    """Test get_user_id function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`:
            `mock_get_manager_cache`

        Yields:
            None
        """
        with patch(
            f"{MODULE_PATH}.CACHE_MANAGER.get_manager_cache"
        ) as mock_get_manager_cache:
            self.mock_manager_cache: dict[str, Any] = {
                "Tommy": {
                    "summary": {"user_id": "123456789"},
                },
            }
            mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_returns_user_id_for_known_manager(self):
        """Test returns user ID for known manager name."""
        result = get_user_id("Tommy")

        assert result == "123456789"

    def test_returns_none_for_unknown_manager(self):
        """Test returns None for unknown manager name."""
        result = get_user_id("Unknown Manager")

        assert result is None

    def test_returns_none_when_no_summary(self):
        """Test returns None when manager has no summary."""
        self.mock_manager_cache["Jay"] = {}

        result = get_user_id("Jay")

        assert result is None


class TestRecursiveReplace:
    """Test recursive_replace function."""

    def test_replaces_in_string(self):
        """Test replaces substring in a string."""
        result = recursive_replace("Patrick Mahomes", "Patrick", "Pat")

        assert result == "Pat Mahomes"

    def test_replaces_in_dict_values(self):
        """Test replaces in dictionary values."""
        data = {"name": "Patrick Mahomes", "team": "KC"}

        result = recursive_replace(data, "Patrick", "Pat")

        assert result["name"] == "Pat Mahomes"
        assert result["team"] == "KC"

    def test_replaces_in_dict_keys(self):
        """Test replaces in dictionary keys."""
        data = {"Patrick Mahomes": 25.5}

        result = recursive_replace(data, "Patrick", "Pat")

        assert "Pat Mahomes" in result
        assert "Patrick Mahomes" not in result

    def test_replaces_in_list_elements(self):
        """Test replaces in list elements."""
        data = ["Patrick Mahomes", "Josh Allen"]

        result = recursive_replace(data, "Patrick", "Pat")

        assert result == ["Pat Mahomes", "Josh Allen"]

    def test_replaces_in_nested_structure(self):
        """Test replaces in deeply nested structure."""
        data = {
            "managers": {
                "Tommy": {
                    "players": ["Patrick Mahomes"],
                },
            },
        }

        result = recursive_replace(data, "Patrick", "Pat")

        assert result["managers"]["Tommy"]["players"] == ["Pat Mahomes"]

    def test_returns_non_string_types_unchanged(self):
        """Test returns int, float, bool unchanged."""
        assert recursive_replace(42, "old", "new") == 42
        assert recursive_replace(3.14, "old", "new") == 3.14
        assert recursive_replace(True, "old", "new") is True

    def test_returns_none_unchanged(self):
        """Test returns None unchanged."""
        assert recursive_replace(None, "old", "new") is None

    def test_replaces_in_mixed_list(self):
        """Test replaces in list with mixed types."""
        data = ["Patrick Mahomes", 25.5, {"name": "Patrick Mahomes"}]

        result = recursive_replace(data, "Patrick", "Pat")

        assert result[0] == "Pat Mahomes"
        assert result[1] == 25.5
        assert result[2]["name"] == "Pat Mahomes"
