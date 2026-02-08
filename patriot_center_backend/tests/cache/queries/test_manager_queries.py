"""Unit tests for manager_queries module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.queries.manager_queries import (
    get_list_of_managers_from_cache,
    get_manager_summary_from_cache,
    get_manager_years_active_from_cache,
)

MODULE_PATH = "patriot_center_backend.cache.queries.manager_queries"


class TestGetManagerSummaryFromCache:
    """Test get_manager_summary_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_metadata_cache`:
            `mock_get_manager_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
        ):
            mock_get_manager_cache.return_value = mock_manager_cache

            yield

    def test_returns_summary_for_valid_manager(self):
        """Test returns summary dict for existing manager."""
        result = get_manager_summary_from_cache("Manager 1")

        assert "matchup_data" in result
        assert "transactions" in result
        assert "overall_data" in result

    def test_raises_for_unknown_manager(self):
        """Test raises ValueError for manager not in cache."""
        with pytest.raises(ValueError, match="NotAManager"):
            get_manager_summary_from_cache("NotAManager")

    def test_raises_when_summary_is_empty(self):
        """Test raises ValueError when manager not in cache."""
        with pytest.raises(ValueError, match="NoSummaryManager"):
            get_manager_summary_from_cache("NoSummaryManager")


class TestGetListOfManagersFromCache:
    """Test get_list_of_managers_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_metadata_cache`:
            `mock_get_manager_cache`
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`
        - `LEAGUE_IDS`: mocked constant

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2023: "979405891168493568"},
            ),
        ):
            mock_get_manager_cache.return_value = mock_manager_cache
            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = {
                "2023": {
                    "managers": ["Manager 1", "Manager 2"],
                }
            }

            yield

    def test_active_only_returns_active_managers(self):
        """Test active_only=True returns only active managers."""
        result = get_list_of_managers_from_cache(active_only=True)

        assert result == ["Manager 1", "Manager 2"]

    def test_all_managers_returns_all_cache_keys(self):
        """Test active_only=False returns all managers from cache."""
        result = get_list_of_managers_from_cache(active_only=False)

        assert "Manager 1" in result
        assert "Manager 2" in result
        assert "Manager 3" in result
        assert len(result) == 3


class TestGetManagerYearsActiveFromCache:
    """Test get_manager_years_active_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_metadata_cache`:
            `mock_get_manager_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
        ):
            mock_get_manager_cache.return_value = mock_manager_cache

            yield

    def test_returns_years_for_valid_manager(self):
        """Test returns years active for existing manager."""
        result = get_manager_years_active_from_cache("Manager 1")

        assert "2023" in result

    def test_returns_empty_for_manager_with_no_years(self):
        """Test returns empty keys for manager with empty years dict."""
        result = get_manager_years_active_from_cache("Manager 3")

        assert len(list(result)) == 0

    def test_raises_when_manager_not_in_cache(self):
        """Test raises KeyError when manager not in cache."""
        with pytest.raises(KeyError):
            get_manager_years_active_from_cache("NotAManager")
