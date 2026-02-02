"""Unit tests for award_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.award_exporter import (
    get_manager_awards,
)

MODULE_PATH = "patriot_center_backend.exporters.award_exporter"


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_image_url`: `mock_get_image_url`
        - `get_manager_awards_from_cache`: `mock_get_awards`
        - `get_manager_score_awards_from_cache`:
            `mock_get_score_awards`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_image_url"
            ) as mock_get_image_url,
            patch(
                f"{MODULE_PATH}.get_manager_awards_from_cache"
            ) as mock_get_awards,
            patch(
                f"{MODULE_PATH}.get_manager_score_awards_from_cache"
            ) as mock_get_score_awards,
        ):
            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.side_effect = (
                lambda m, dictionary=False: (
                    {
                        "name": m,
                        "image_url": "https://sleepercdn.com/avatars/abc123",
                    }
                    if dictionary
                    else "https://sleepercdn.com/avatars/abc123"
                )
            )

            self.mock_get_awards = mock_get_awards
            self.mock_get_awards.return_value = {}

            self.mock_get_score_awards = mock_get_score_awards
            self.mock_get_score_awards.return_value = {}

            yield

    def test_get_awards(self):
        """Test getting manager awards."""
        self.mock_get_awards.return_value = {
            "first_place": 1,
            "second_place": 0,
            "third_place": 1,
            "playoff_appearances": 2,
        }
        self.mock_get_score_awards.return_value = {
            "highest_weekly_score": {},
            "lowest_weekly_score": {},
            "biggest_blowout_win": {},
            "biggest_blowout_loss": {},
        }

        result = get_manager_awards("Tommy")

        assert "manager" in result
        assert result["manager"]["name"] == "Tommy"
        assert "image_url" in result
        assert "awards" in result
        # Awards should be combined from both sources
        assert "first_place" in result["awards"]
        assert "highest_weekly_score" in result["awards"]

    def test_get_awards_calls_both_query_functions(self):
        """Test that both award query functions are called."""
        get_manager_awards("Tommy")

        self.mock_get_awards.assert_called_once_with("Tommy")
        self.mock_get_score_awards.assert_called_once_with("Tommy")

    def test_get_awards_merges_score_awards_into_awards(self):
        """Test that score awards are merged into the awards dict."""
        self.mock_get_awards.return_value = {"first_place": 2}
        self.mock_get_score_awards.return_value = {
            "highest_weekly_score": {"score": 180.5}
        }

        result = get_manager_awards("Tommy")

        assert result["awards"]["first_place"] == 2
        assert result["awards"]["highest_weekly_score"] == {"score": 180.5}

    def test_get_awards_returns_deepcopy(self):
        """Test that result is a deep copy (immutable)."""
        awards_data = {"first_place": 2}
        self.mock_get_awards.return_value = awards_data

        result = get_manager_awards("Tommy")

        result["awards"]["first_place"] = 999
        assert awards_data["first_place"] == 2
