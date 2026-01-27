"""Unit tests for cache_updater module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.cache_updater import update_all_caches


class TestUpdateAllCaches:
    """Test update_all_caches function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `update_player_ids_cache`: `mock_update_player_ids`
        - `update_weekly_data_caches`: `mock_update_weekly_data`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_updater"
                ".update_player_ids_cache"
            ) as mock_update_player_ids,
            patch(
                "patriot_center_backend.cache.cache_updater"
                ".update_weekly_data_caches"
            ) as mock_update_weekly_data,
        ):
            self.mock_update_player_ids = mock_update_player_ids
            self.mock_update_weekly_data = mock_update_weekly_data

            yield

    def test_calls_update_player_ids_cache(self):
        """Test calls update_player_ids_cache."""
        update_all_caches()

        self.mock_update_player_ids.assert_called_once()

    def test_calls_update_weekly_data_caches(self):
        """Test calls update_weekly_data_caches."""
        update_all_caches()

        self.mock_update_weekly_data.assert_called_once()

    def test_calls_updates_in_correct_order(self):
        """Test calls cache updates in dependency order."""
        call_order = []

        def track_player_ids():
            call_order.append("player_ids")

        def track_weekly_data():
            call_order.append("weekly_data")

        self.mock_update_player_ids.side_effect = track_player_ids
        self.mock_update_weekly_data.side_effect = track_weekly_data

        update_all_caches()

        assert call_order == ["player_ids", "weekly_data"]

    def test_propagates_exception_from_player_ids(self):
        """Test propagates exception from update_player_ids_cache."""
        self.mock_update_player_ids.side_effect = ValueError("API Error")

        with pytest.raises(ValueError) as exc_info:
            update_all_caches()

        assert "API Error" in str(exc_info.value)
        self.mock_update_weekly_data.assert_not_called()

    def test_propagates_exception_from_weekly_data(self):
        """Test propagates exception from update_weekly_data_caches."""
        self.mock_update_weekly_data.side_effect = ValueError("Cache Error")

        with pytest.raises(ValueError) as exc_info:
            update_all_caches()

        assert "Cache Error" in str(exc_info.value)
        self.mock_update_player_ids.assert_called_once()
