from unittest.mock import patch

import pytest

from patriot_center_backend.managers.cache_queries.award_queries import (
    get_manager_awards_from_cache,
    get_manager_score_awards_from_cache,
)


class TestGetManagerAwardsFromCache:
    """Test get_manager_awards_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.cache_queries.award_queries.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.cache_queries.award_queries.get_image_url') as mock_get_image_url:

            mock_get_manager.return_value = mock_manager_cache
            mock_get_image_url.return_value = "https://image.example"

            yield

    def test_manager_awards(self):
        """Test getting manager awards."""
        result = get_manager_awards_from_cache("Manager 1", {})

        # Should include various award categories
        assert "first_place" in result
        assert "second_place" in result
        assert "third_place" in result
        assert "playoff_appearances" in result
        assert result["first_place"] == 1  # From placement 2023
        assert result["playoff_appearances"] == 2


class TestGetManagerScoreAwardsFromCache:
    """Test get_manager_score_awards_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.cache_queries.award_queries.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.cache_queries.award_queries.get_matchup_card') as mock_get_matchup_card, \
             patch('patriot_center_backend.managers.cache_queries.award_queries.validate_matchup_data') as mock_validate:

            self.mock_get_matchup_card = mock_get_matchup_card
            
            mock_get_manager.return_value = mock_manager_cache
            self.mock_get_matchup_card.return_value = {"data": "data"}
            mock_validate.return_value = ""
            
            yield

    def test_score_awards(self):
        """Test getting scoring-related awards."""
        result = get_manager_score_awards_from_cache("Manager 1", {})

        # Should include score-based awards
        assert isinstance(result, dict)

        assert "highest_weekly_score" in result
        assert "lowest_weekly_score" in result
        assert "biggest_blowout_win" in result
        assert "biggest_blowout_loss" in result

        assert result["highest_weekly_score"]
        assert result["lowest_weekly_score"]
        assert result["biggest_blowout_win"]
        assert not result["biggest_blowout_loss"] # Empty because it didn't exist

        # biggest_blowout_loss doesn't exist, so 3 out of 4 called
        assert self.mock_get_matchup_card.call_count == 3