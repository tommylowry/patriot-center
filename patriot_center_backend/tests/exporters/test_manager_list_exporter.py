"""Unit tests for manager_list_exporter module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.manager_list_exporter import (
    get_managers_list,
)

MODULE_PATH = "patriot_center_backend.exporters.manager_list_exporter"


class TestGetManagersList:
    """Test get_managers_list method."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
    ):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_list_of_managers_from_cache`: `mock_get_list_of_managers`
        - `get_manager_summary_from_cache`: `mock_get_manager_summary`
        - `get_ranking_details_from_cache`: `mock_get_ranking_details`
        - `get_manager_years_active_from_cache`: `mock_get_manager_years_active`

        Args:
            mock_manager_cache: Sample manager cache

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_list_of_managers_from_cache"
            ) as mock_get_list_of_managers,
            patch(
                f"{MODULE_PATH}.get_manager_summary_from_cache"
            ) as mock_get_manager_summary,
            patch(
                f"{MODULE_PATH}.get_ranking_details_from_cache"
            ) as mock_get_ranking_details,
            patch(
                f"{MODULE_PATH}.get_manager_years_active_from_cache"
            ) as mock_get_manager_years_active,
        ):
            self.mock_get_list_of_managers = mock_get_list_of_managers
            self.mock_get_list_of_managers.return_value = [
                "Manager 1",
                "Manager 2",
            ]

            self.mock_get_manager_summary = mock_get_manager_summary
            self.mock_get_manager_summary.side_effect = [
                mock_manager_cache["Manager 1"]["summary"],
                mock_manager_cache["Manager 2"]["summary"],
            ]

            self.mock_get_ranking_details = mock_get_ranking_details
            self.mock_get_ranking_details.return_value = {}

            self.mock_get_manager_years_active = mock_get_manager_years_active
            self.mock_get_manager_years_active.return_value = ["2023"]

            yield

    def test_get_active_managers_only(self):
        """Test getting only active managers."""
        self.mock_get_ranking_details.return_value = {
            "values": {
                "win_percentage": 60.0,
                "average_points_for": 100.0,
                "average_points_against": 90.0,
                "average_points_differential": 10.0,
                "trades": 5,
                "playoffs": 2,
            },
            "ranks": {
                "win_percentage": 1,
                "average_points_for": 1,
                "average_points_against": 2,
                "average_points_differential": 1,
                "trades": 1,
                "playoffs": 1,
                "is_active_manager": True,
                "worst": 10,
            },
        }

        result = get_managers_list(active_only=True)

        assert "managers" in result
        assert len(result["managers"]) == 2
        assert all("name" in m for m in result["managers"])
        assert all("image_url" in m for m in result["managers"])

    def test_get_all_managers(self):
        """Test getting all managers including inactive."""
        self.mock_get_ranking_details.return_value = {
            "values": {
                "win_percentage": 60.0,
                "average_points_for": 100.0,
                "average_points_against": 90.0,
                "average_points_differential": 10.0,
                "trades": 5,
                "playoffs": 2,
            },
            "ranks": {
                "win_percentage": 1,
                "average_points_for": 1,
                "average_points_against": 2,
                "average_points_differential": 1,
                "trades": 1,
                "playoffs": 1,
                "is_active_manager": True,
                "worst": 10,
            },
        }

        result = get_managers_list(active_only=False)

        assert "managers" in result
        # Should get all managers from cache keys
        assert len(result["managers"]) == 2

    def test_managers_list_sorted_by_weight(self):
        """Test that managers are sorted by weight (best first)."""

        def ranking_side_effect(manager, manager_summary_usage, active_only):
            # Manager 1 should have better stats
            if manager == "Manager 1":
                return {
                    "values": {
                        "win_percentage": 62.5,
                        "average_points_for": 100.0,
                        "average_points_against": 90.0,
                        "average_points_differential": 10.0,
                        "trades": 5,
                        "playoffs": 2,
                    },
                    "ranks": {
                        "win_percentage": 1,
                        "average_points_for": 1,
                        "average_points_against": 2,
                        "average_points_differential": 1,
                        "trades": 1,
                        "playoffs": 1,
                        "is_active_manager": True,
                        "worst": 10,
                    },
                }
            else:
                return {
                    "values": {
                        "win_percentage": 31.2,
                        "average_points_for": 90.0,
                        "average_points_against": 100.0,
                        "average_points_differential": -10.0,
                        "trades": 3,
                        "playoffs": 1,
                    },
                    "ranks": {
                        "win_percentage": 2,
                        "average_points_for": 2,
                        "average_points_against": 1,
                        "average_points_differential": 2,
                        "trades": 2,
                        "playoffs": 2,
                        "is_active_manager": True,
                        "worst": 10,
                    },
                }

        self.mock_get_ranking_details.side_effect = ranking_side_effect

        result = get_managers_list(active_only=True)

        # Manager 1 should be first (better record)
        assert result["managers"][0]["name"] == "Manager 1"
