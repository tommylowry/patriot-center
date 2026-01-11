
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.cache_queries.ranking_queries import (
    get_ranking_details_from_cache,
)


@pytest.fixture
def mock_valid_options_cache():
    """Create a sample valid options cache."""
    return {
        "2025": {
            "managers": ["Manager 1", "Manager 2", "Manager 3"]
        }
    }


class TestGetRankingDetailsFromCache:
    """Test get_ranking_details_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache, mock_valid_options_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.cache_queries.ranking_queries.CACHE_MANAGER.get_manager_cache') as mock_get_manager, \
             patch('patriot_center_backend.managers.cache_queries.ranking_queries.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options:
            
            mock_get_manager.return_value = mock_manager_cache
            mock_get_valid_options.return_value = mock_valid_options_cache

            yield
    
    def test_get_rankings(self):
        """Test getting ranking details."""
        result = get_ranking_details_from_cache("Manager 1")

        # Should return dictionary with rankings
        assert isinstance(result, dict)
        assert "is_active_manager" in result
        assert "worst" in result
        assert result["worst"] == 3  # Total number of managers