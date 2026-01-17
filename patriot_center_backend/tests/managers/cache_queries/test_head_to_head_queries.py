"""Unit tests for head_to_head_queries module."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.cache_queries.head_to_head_queries import (
    get_head_to_head_details_from_cache,
    get_head_to_head_overall_from_cache,
)


class TestGetHeadToHeadDetailsFromCache:
    """Test get_head_to_head_details_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
    ):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `get_image_url`: `mock_get_image_url`

        Args:
            mock_manager_cache: Sample manager cache

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.get_image_url",
            ) as mock_get_image_url,
        ):
            mock_get_manager_cache.return_value = mock_manager_cache
            mock_get_image_url.return_value = {"data": "data"}

            yield

    def test_get_h2h_details(self):
        """Test getting head-to-head details."""
        result = get_head_to_head_details_from_cache(
            "Manager 1", {}, year=None, opponent="Manager 2"
        )

        # Should return single opponent dict
        assert isinstance(result, dict)
        assert "opponent" in result
        assert "wins" in result
        assert result["wins"] == 7


class TestGetHeadToHeadOverallFromCache:
    """Test get_head_to_head_overall_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
    ):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `get_matchup_card`: `mock_get_matchup_card`

        Args:
            mock_manager_cache: Sample manager cache

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.get_matchup_card",
            ) as mock_get_matchup_card,
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.validate_matchup_data",
            ) as mock_validate,
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries.get_head_to_head_details_from_cache",
            ) as mock_h2h_details,
            patch(
                "patriot_center_backend.managers.cache_queries"
                ".head_to_head_queries._evaluate_matchup",
            ) as mock_evaluate_matchup,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_matchup_card_value = {"year": "2023", "week": "1"}
            self.mock_h2h_details_value = {"wins": 0, "losses": 0, "ties": 0}
            self.mock_evaluate_matchup = mock_evaluate_matchup

            mock_get_manager_cache.return_value = self.mock_manager_cache
            mock_get_matchup_card.return_value = self.mock_matchup_card_value
            mock_validate.return_value = ""
            mock_h2h_details.return_value = self.mock_h2h_details_value

            yield

    def test_h2h_overall_stats(self, caplog: pytest.LogCaptureFixture):
        """Test comprehensive H2H stats calculation.

        Args:
            caplog: pytest caplog
        """
        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", {}
        )

        # Verify warning was printed out for no victories for Manager 2
        assert "No victories found for Manager 2" in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Check for manager-specific win keys
        assert "manager_1_wins" in result
        assert "manager_2_wins" in result
        assert "ties" in result

    def test_h2h_no_matchups(self, caplog: pytest.LogCaptureFixture):
        """Test H2H when managers never played.

        Args:
            caplog: pytest caplog
        """
        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 3", {}
        )

        assert "No victories found for Manager 1" in caplog.text
        assert "No victories found for Manager 3" in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should handle gracefully even with no matchups
        assert result is not None
        assert isinstance(result, dict)

    def test_h2h_list_all_matchups(self):
        """Test H2H with list_all_matchups=True returns matchup history."""
        # Setup weeks data with matchups
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "win",
                    "points_for": 120.5,
                    "points_against": 100.0
                },
                "transactions": {}
            },
            "2": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "loss",
                    "points_for": 90.0,
                    "points_against": 110.0
                },
                "transactions": {}
            }
        }

        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", {}, list_all_matchups=True
        )

        # Should return a list of matchup cards
        assert isinstance(result, list)
        assert len(result) == 2

    def test_h2h_with_specific_year(self, caplog: pytest.LogCaptureFixture):
        """Test H2H stats filtered to specific year.

        Args:
            caplog: pytest caplog
        """
        # Setup weeks data
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "win",
                    "points_for": 120.5,
                    "points_against": 100.0
                },
                "transactions": {}
            }
        }
        self.mock_manager_cache.update(
            {
                "Manager 1": {
                    "years": {
                        "2023": {
                            "summary": {
                                "matchup_data": {
                                    "overall": {
                                        "points_for": {
                                            "opponents": {
                                                "Manager 2": 100.0
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

        self.mock_manager_cache["Manager 2"] = deepcopy(
            self.mock_manager_cache["Manager 1"]
        )

        self.mock_manager_cache.update(
            {
                "Manager 2": {
                    "years": {
                        "2023": {
                            "summary": {
                                "matchup_data": {
                                    "overall": {
                                        "points_for": {
                                            "opponents": {
                                                "Manager 1": 100.0
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )
        self.mock_h2h_details_value = {"wins": 1, "losses": 0, "ties": 0}

        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", {}, year="2023"
        )

        assert "No victories found for Manager 2 against " in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should return dict with stats
        assert isinstance(result, dict)
        assert "manager_1_wins" in result

    def test_h2h_manager2_wins(self, caplog: pytest.LogCaptureFixture):
        """Test H2H when manager2 wins (result='loss' for manager1).

        Args:
            caplog: pytest caplog
        """
        # Setup weeks data where Manager 2 wins
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "loss",
                    "points_for": 90.0,
                    "points_against": 110.0
                },
                "transactions": {}
            },
            "2": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "loss",
                    "points_for": 85.0,
                    "points_against": 115.0
                },
                "transactions": {}
            }
        }
        self.mock_manager_cache["Manager 2"] = deepcopy(
            self.mock_manager_cache["Manager 1"]
        )

        self.mock_h2h_details_value = {"wins": 0, "losses": 2, "ties": 0}
        self.mock_matchup_card_value = {
            "year": "2023", "week": "1", "margin": 20.0
        }

        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", {}
        )

        assert "No victories found for Manager 1 against " in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should process manager2's wins correctly
        assert isinstance(result, dict)
        assert "manager_2_wins" in result