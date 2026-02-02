"""Unit tests for option_queries module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.queries.option_queries import (
    get_options_list_from_cache,
)

MODULE_PATH = "patriot_center_backend.cache.queries.option_queries"


class TestGetOptionsListFromCache:
    """Test get_options_list_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_players_cache`:
            `mock_get_players_cache`
        - `NAME_TO_MANAGER_USERNAME`: mocked constant

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                f"{MODULE_PATH}.NAME_TO_MANAGER_USERNAME",
                {
                    "Tommy": "tommylowry",
                    "Benz": "bbennick",
                },
            ),
        ):
            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = {
                "Jayden Daniels": {
                    "type": "player",
                    "name": "Jayden Daniels",
                },
                "Brian Robinson": {
                    "type": "player",
                    "name": "Brian Robinson",
                },
            }

            yield

    def test_returns_players_and_managers(self):
        """Test returns both players and manager entries."""
        result = get_options_list_from_cache()

        assert "Jayden Daniels" in result
        assert "Brian Robinson" in result
        assert "Tommy" in result
        assert "Benz" in result

    def test_manager_entries_have_correct_structure(self):
        """Test manager entries include type, name, full_name, slug."""
        result = get_options_list_from_cache()

        assert result["Tommy"]["type"] == "manager"
        assert result["Tommy"]["name"] == "Tommy"
        assert result["Tommy"]["full_name"] == "Tommy"
        assert result["Tommy"]["slug"] == "Tommy"

    def test_returns_deepcopy_of_players(self):
        """Test modifying result does not affect original cache."""
        result = get_options_list_from_cache()

        result["Jayden Daniels"]["type"] = "modified"

        # Call again - should still be original
        result2 = get_options_list_from_cache()
        assert result2["Jayden Daniels"]["type"] == "player"

    def test_empty_players_cache(self):
        """Test with empty players cache still adds managers."""
        self.mock_get_players_cache.return_value = {}

        result = get_options_list_from_cache()

        assert "Tommy" in result
        assert "Benz" in result
        assert len(result) == 2
