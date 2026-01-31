"""Unit tests for weekly_data_updater module."""

from unittest.mock import MagicMock, patch

import pytest

from patriot_center_backend.cache.updaters.weekly_data_updater import (
    update_weekly_data_caches,
)


class TestUpdateWeeklyDataCaches:
    """Test update_weekly_data_caches function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `ManagerMetadataManager`: `mock_manager_updater_class`
        - `ReplacementScoreCacheBuilder`: `mock_replacement_builder_class`
        - `get_league_status`: `mock_get_league_status`
        - `assign_placements_retroactively`: `mock_assign_placements`
        - `update_player_data_cache`: `mock_update_player_data`
        - `log_cache_update`: `mock_log_cache_update`
        - `set_last_updated`: `mock_set_last_updated`
        - `CACHE_MANAGER.save_all_caches`: `mock_save_all_caches`
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".ManagerMetadataManager"
            ) as mock_manager_updater_class,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".ReplacementScoreCacheBuilder"
            ) as mock_replacement_builder_class,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".get_league_status"
            ) as mock_get_league_status,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".assign_placements_retroactively"
            ) as mock_assign_placements,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".update_player_data_cache"
            ) as mock_update_player_data,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".log_cache_update"
            ) as mock_log_cache_update,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".set_last_updated"
            ) as mock_set_last_updated,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.save_all_caches"
            ) as mock_save_all_caches,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_manager_updater_instance = MagicMock()
            mock_manager_updater_class.return_value = (
                self.mock_manager_updater_instance
            )

            self.mock_replacement_builder_instance = MagicMock()
            mock_replacement_builder_class.return_value = (
                self.mock_replacement_builder_instance
            )
            self.mock_replacement_builder_class = (
                mock_replacement_builder_class
            )

            self.mock_get_league_status = mock_get_league_status
            self.mock_get_league_status.return_value = ([1, 2, 3], False)

            self.mock_assign_placements = mock_assign_placements
            self.mock_update_player_data = mock_update_player_data
            self.mock_log_cache_update = mock_log_cache_update
            self.mock_set_last_updated = mock_set_last_updated
            self.mock_save_all_caches = mock_save_all_caches

            yield

    def test_builds_replacement_scores_for_each_year(self):
        """Test builds replacement scores for each year in LEAGUE_IDS."""
        update_weekly_data_caches()

        self.mock_replacement_builder_class.assert_called_once_with(2024)
        self.mock_replacement_builder_instance.update.assert_called_once()

    def test_skips_year_when_no_weeks_to_update(self):
        """Test skips processing when no weeks to update."""
        self.mock_get_league_status.return_value = ([], False)

        update_weekly_data_caches()

        self.mock_manager_updater_instance.cache_week_data.assert_not_called()

    def test_processes_each_week(self):
        """Test processes each week in weeks_to_update."""
        update_weekly_data_caches()

        assert (
            self.mock_manager_updater_instance.cache_week_data.call_count == 3
        )
        assert self.mock_update_player_data.call_count == 3

    def test_assigns_placements_on_last_week_when_complete(self):
        """Test assigns placements on last week when season is complete."""
        self.mock_get_league_status.return_value = ([15, 16, 17], True)

        update_weekly_data_caches()

        self.mock_assign_placements.assert_called_once_with(2024)

    def test_does_not_assign_placements_when_season_incomplete(self):
        """Test does not assign placements when season is not complete."""
        self.mock_get_league_status.return_value = ([1, 2, 3], False)

        update_weekly_data_caches()

        self.mock_assign_placements.assert_not_called()

    def test_logs_cache_update_for_each_week(self):
        """Test logs cache update for each week."""
        update_weekly_data_caches()

        assert self.mock_log_cache_update.call_count == 3

    def test_sets_last_updated_for_each_week(self):
        """Test sets last updated for each processed week."""
        update_weekly_data_caches()

        assert self.mock_set_last_updated.call_count == 3
        self.mock_set_last_updated.assert_any_call(2024, 1)
        self.mock_set_last_updated.assert_any_call(2024, 2)
        self.mock_set_last_updated.assert_any_call(2024, 3)

    def test_saves_all_caches_at_end(self):
        """Test saves all caches after processing."""
        update_weekly_data_caches()

        self.mock_save_all_caches.assert_called_once()

    def test_does_not_assign_placements_on_non_last_week(self):
        """Test does not assign placements on non-last week even if complete."""
        self.mock_get_league_status.return_value = ([15, 16, 17], True)

        update_weekly_data_caches()

        # Should only be called once (on week 17, the max)
        self.mock_assign_placements.assert_called_once()
