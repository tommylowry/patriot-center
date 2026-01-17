"""Unit tests for matchup_queries module."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.cache_queries.matchup_queries import (
    get_matchup_details_from_cache,
    get_overall_data_details_from_cache,
)


class TestGetMatchupDetailsFromCache:
    """Test get_matchup_details_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.cache_queries.matchup_queries"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
        ):
            self.mock_manager_cache = mock_manager_cache

            mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_all_time_stats(self):
        """Test getting all-time matchup stats."""
        result = get_matchup_details_from_cache("Manager 1")

        assert result["overall"]["wins"] == 10
        assert result["overall"]["losses"] == 5
        assert result["overall"]["ties"] == 1

        # 10/(10+5+1) * 100 = 62.5%
        assert result["overall"]["win_percentage"] == 62.5
        assert "average_points_for" in result["overall"]
        assert "average_points_against" in result["overall"]

    def test_single_season_stats(self):
        """Test getting stats for a specific season."""
        result = get_matchup_details_from_cache("Manager 1", year="2023")

        assert result["overall"]["wins"] == 6
        assert result["overall"]["losses"] == 2
        assert result["overall"]["ties"] == 0

    def test_manager_with_no_playoffs(self):
        """Test manager who never made playoffs."""
        result = get_matchup_details_from_cache("Manager 3")

        assert result["playoffs"]["wins"] == 0
        assert result["playoffs"]["losses"] == 0
        assert result["playoffs"]["win_percentage"] == 0.0
        assert result["playoffs"]["average_points_for"] == 0.0

    def test_win_percentage_calculation(self):
        """Test win percentage is calculated correctly."""
        result = get_matchup_details_from_cache("Manager 2")

        # 5 wins out of 16 games (5+10+1) = 31.25%
        # Rounded to 1 decimal
        assert result["overall"]["win_percentage"] == 31.2

    def test_zero_matchups_no_division_by_zero(self):
        """Test that zero matchups doesn't cause division by zero."""
        result = get_matchup_details_from_cache("Manager 3")

        assert result["overall"]["win_percentage"] == 0.0
        assert result["overall"]["average_points_for"] == 0.0

    def test_get_matchup_details_immutable(self):
        """Test that function doesn't modify cache."""
        original = deepcopy(self.mock_manager_cache)

        get_matchup_details_from_cache("Manager 1")

        assert self.mock_manager_cache == original

class TestGetOverallDataDetailsFromCache:
    """Test get_overall_data_details_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `get_matchup_card`: `mock_get_matchup_card`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.cache_queries.matchup_queries"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.cache_queries.matchup_queries"
                ".get_matchup_card"
            ) as mock_get_matchup_card,
        ):
            self.mock_manager_cache = mock_manager_cache

            self.mock_get_matchup_card = mock_get_matchup_card

            mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_all_time_overall_data(self):
        """Test getting all-time overall data."""
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        # Add week 17 data for 2023 and 2022 to sample_manager_cache for
        # opponent lookup
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        result = get_overall_data_details_from_cache("Manager 1", {})

        assert isinstance(result["placements"], list)
        assert len(result["placements"]) == 2

        years = [p["year"] for p in result["placements"]]
        assert "2023" in years
        assert "2022" in years

        placement_2023 = next(
            p for p in result["placements"] if p["year"] == "2023"
        )
        assert placement_2023["placement"] == 1
        assert placement_2023["matchup_card"] == {"mock": "matchup_card"}
        assert result["playoff_appearances"] == 2

    def test_single_season_overall_data(self):
        """Test getting single season overall data."""
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        result = get_overall_data_details_from_cache("Manager 1", {})

        assert isinstance(result["placements"], list)
        assert len(result["placements"]) == 2  # Still returns all-time data

        placement_2023 = next(
            p for p in result["placements"] if p["year"] == "2023"
        )
        assert placement_2023["placement"] == 1

    def test_manager_with_no_playoff_appearances(self):
        """Test manager with no playoff appearances."""
        result = get_overall_data_details_from_cache("Manager 3", {})

        assert result["playoff_appearances"] == 0
        assert result["placements"] == []
        self.mock_get_matchup_card.assert_not_called()

    def test_week_selection_for_year_2020_and_earlier(self):
        """Test that week 16 is used for years 2020 and earlier."""
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        mgr_cache = self.mock_manager_cache["Manager 1"]
        # Add placement for 2020
        mgr_cache["summary"]["overall_data"]["placement"]["2020"] = 2
        mgr_cache["years"]["2020"] = {
            "weeks": {"16": {"matchup_data": {"opponent_manager": "Manager 2"}}}
        }
        # Also add week 17 data for other years
        mgr_cache["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        mgr_cache["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        get_overall_data_details_from_cache("Manager 1", {})

        # Find the call for 2020 - should use week '16'
        calls = self.mock_get_matchup_card.call_args_list
        call_for_2020 = [c for c in calls if c[0][2] == "2020"]
        assert len(call_for_2020) == 1
        assert call_for_2020[0][0][3] == "16"  # week parameter should be '16'

    def test_week_selection_for_year_after_2020(self):
        """Test that week 17 is used for years after 2020."""
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        get_overall_data_details_from_cache("Manager 1", {})

        # All calls should use week '17' since both years are after 2020
        for call in self.mock_get_matchup_card.call_args_list:
            assert call[0][3] == "17"  # week parameter should be '17'

    def test_missing_opponent_skips_matchup_card(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that missing opponent results in warning and empty matchup_card.

        Args:
            caplog: pytest LogCaptureFixture
        """
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        # Don't add week 17 data for 2022 - opponent will be missing
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {"weeks": {}}
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }

        result = get_overall_data_details_from_cache("Manager 1", {})

        # Verify warning was printed for missing opponent
        assert "Unable to retreive opponent" in caplog.text
        assert "year 2022" in caplog.text

        # Verify get_matchup_card was NOT called for 2022 (missing opponent)
        calls = self.mock_get_matchup_card.call_args_list
        call_years = [c[0][2] for c in calls]
        assert "2022" not in call_years
        assert "2023" in call_years  # 2023 should still be called

        # Verify the placement for 2022 has empty matchup_card
        assert isinstance(result["placements"], list)
        placement_2022 = next(
            p for p in result["placements"] if p["year"] == "2022"
        )
        assert placement_2022["matchup_card"] == {}

    def test_matchup_card_included_in_each_placement(self):
        """Test that matchup_card is included in each placement item."""
        self.mock_get_matchup_card.side_effect = [
            {"card": "2023_card"},
            {"card": "2022_card"}
        ]

        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        result = get_overall_data_details_from_cache("Manager 1", {})

        assert isinstance(result["placements"], list)
        for placement in result["placements"]:
            assert "matchup_card" in placement

    def test_passes_correct_params_to_get_matchup_card(self):
        """Test that all parameters are passed to get_matchup_card."""
        self.mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        image_urls = {"url": "http://example.com"}

        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        self.mock_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        get_overall_data_details_from_cache("Manager 1", image_urls)

        # Verify get_matchup_card was called with the correct parameters
        call_args = self.mock_get_matchup_card.call_args_list[0][0]
        assert call_args[0] == "Manager 1"
        # call_args[1] is opponent
        # call_args[2] is year
        # call_args[3] is week
        assert call_args[4] == image_urls

    def test_get_overall_data_immutable(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test that function doesn't modify cache.

        Args:
            caplog: pytest LogCaptureFixture
        """
        original = deepcopy(self.mock_manager_cache)

        get_overall_data_details_from_cache("Manager 1", {})

        # Verify warning was printed for missing opponent
        assert "Unable to retreive opponent" in caplog.text
        assert "year 2023 week 17" in caplog.text
        assert "year 2022 week 17" in caplog.text

        assert self.mock_manager_cache == original
