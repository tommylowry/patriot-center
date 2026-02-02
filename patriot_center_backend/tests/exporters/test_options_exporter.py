"""Unit tests for options_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.options_exporter import (
    get_options_list,
)

MODULE_PATH = "patriot_center_backend.exporters.options_exporter"


class TestGetOptionsList:
    """Test get_options_list method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_options_list_from_cache`:
            `mock_get_options_list_from_cache`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_options_list_from_cache"
            ) as mock_get_options_list_from_cache,
        ):
            self.mock_get_options_list_from_cache = (
                mock_get_options_list_from_cache
            )
            self.mock_get_options_list_from_cache.return_value = {}

            yield

    def test_get_options_list(self):
        """Test getting options list returns cache data."""
        self.mock_get_options_list_from_cache.return_value = {
            "Jayden Daniels": {
                "type": "player",
                "name": "Jayden Daniels",
                "position": "QB",
            },
            "Tommy": {
                "type": "manager",
                "name": "Tommy",
            },
        }

        result = get_options_list()

        assert "Jayden Daniels" in result
        assert "Tommy" in result

    def test_get_options_list_empty(self):
        """Test getting options list when cache is empty."""
        self.mock_get_options_list_from_cache.return_value = {}

        result = get_options_list()

        assert result == {}

    def test_get_options_list_calls_cache_query(self):
        """Test that cache query function is called."""
        get_options_list()

        self.mock_get_options_list_from_cache.assert_called_once()
