"""Unit tests for helpers module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.utils.helpers import get_user_id

MODULE_PATH = "patriot_center_backend.utils.helpers"


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
