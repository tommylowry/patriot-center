"""Unit tests for summary_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.summary_exporter import (
    get_manager_summary,
)

MODULE_PATH = "patriot_center_backend.exporters.summary_exporter"


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `validate_manager_query`: (returns nothing)
        - `get_image_url`: `mock_get_image_url`
        - `get_manager_years_active_from_cache`:
            `mock_get_manager_years_active`
        - `get_matchup_details_from_cache`: `mock_get_matchup`
        - `get_transaction_details_from_cache`: `mock_get_trans`
        - `get_overall_data_details_from_cache`: `mock_get_overall`
        - `get_ranking_details_from_cache`: `mock_get_ranking`
        - `get_head_to_head_details_from_cache`: `mock_get_h2h`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.validate_manager_query"
            ) as mock_validate_manager_query,
            patch(
                f"{MODULE_PATH}.get_image_url"
            ) as mock_get_image_url,
            patch(
                f"{MODULE_PATH}.get_manager_years_active_from_cache"
            ) as mock_get_manager_years_active,
            patch(
                f"{MODULE_PATH}.get_matchup_details_from_cache"
            ) as mock_get_matchup,
            patch(
                f"{MODULE_PATH}.get_transaction_details_from_cache"
            ) as mock_get_trans,
            patch(
                f"{MODULE_PATH}.get_overall_data_details_from_cache"
            ) as mock_get_overall,
            patch(
                f"{MODULE_PATH}.get_ranking_details_from_cache"
            ) as mock_get_ranking,
            patch(
                f"{MODULE_PATH}.get_head_to_head_details_from_cache"
            ) as mock_get_h2h,
        ):
            self.mock_validate_manager_query = mock_validate_manager_query

            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.return_value = (
                "https://sleepercdn.com/avatars/abc123"
            )

            self.mock_get_manager_years_active = mock_get_manager_years_active
            self.mock_get_manager_years_active.return_value = [
                "2023", "2022"
            ]

            self.mock_get_matchup = mock_get_matchup
            self.mock_get_matchup.return_value = {}

            self.mock_get_trans = mock_get_trans
            self.mock_get_trans.return_value = {}

            self.mock_get_overall = mock_get_overall
            self.mock_get_overall.return_value = {}

            self.mock_get_ranking = mock_get_ranking
            self.mock_get_ranking.return_value = {}

            self.mock_get_h2h = mock_get_h2h
            self.mock_get_h2h.return_value = {}

            yield

    def test_get_manager_summary_all_time(self):
        """Test getting manager summary for all-time stats."""
        self.mock_get_matchup.return_value = {"overall": {"wins": 10}}
        self.mock_get_trans.return_value = {"trades": {"total": 5}}
        self.mock_get_overall.return_value = {
            "placements": [],
            "playoff_appearances": 2,
        }
        self.mock_get_ranking.return_value = {"ranks": {}, "values": {}}

        result = get_manager_summary("Tommy")

        assert result["manager_name"] == "Tommy"
        assert result["image_url"] == (
            "https://sleepercdn.com/avatars/abc123"
        )
        assert result["years_active"] == ["2023", "2022"]
        assert result["matchup_data"] == {"overall": {"wins": 10}}
        assert result["transactions"] == {"trades": {"total": 5}}
        assert result["overall_data"] == {
            "placements": [],
            "playoff_appearances": 2,
        }
        assert result["rankings"] == {"ranks": {}, "values": {}}
        assert result["head_to_head"] == {}

    def test_get_manager_summary_single_year(self):
        """Test getting manager summary for specific year."""
        self.mock_get_matchup.return_value = {"overall": {"wins": 6}}
        self.mock_get_trans.return_value = {"trades": {"total": 2}}
        self.mock_get_overall.return_value = {
            "placements": [],
            "playoff_appearances": 1,
        }
        self.mock_get_ranking.return_value = {"ranks": {}, "values": {}}

        result = get_manager_summary("Tommy", year="2023")

        assert result["manager_name"] == "Tommy"

        # Verify year was passed to underlying functions
        self.mock_get_matchup.assert_called_once_with(
            "Tommy", year="2023"
        )
        self.mock_get_trans.assert_called_once_with(
            "Tommy", year="2023"
        )
        self.mock_get_ranking.assert_called_once_with(
            "Tommy", year="2023"
        )
        self.mock_get_h2h.assert_called_once_with(
            "Tommy", year="2023"
        )

    def test_get_manager_summary_validates_manager(self):
        """Test that validate_manager_query is called."""
        get_manager_summary("Tommy", year="2023")

        self.mock_validate_manager_query.assert_called_once_with(
            "Tommy", "2023"
        )

    def test_get_manager_summary_validates_manager_no_year(self):
        """Test that validate_manager_query is called without year."""
        get_manager_summary("Tommy")

        self.mock_validate_manager_query.assert_called_once_with(
            "Tommy", None
        )

    def test_get_manager_summary_validation_error_propagates(self):
        """Test that ValueError from validation propagates."""
        self.mock_validate_manager_query.side_effect = ValueError(
            "Manager NotAManager not found in cache."
        )

        with pytest.raises(ValueError, match="NotAManager"):
            get_manager_summary("NotAManager")

    def test_get_manager_summary_returns_deepcopy(self):
        """Test that result is a deep copy (immutable)."""
        matchup_data = {"overall": {"wins": 10}}
        self.mock_get_matchup.return_value = matchup_data

        result = get_manager_summary("Tommy")

        # Modifying result should not affect mock return value
        result["matchup_data"]["overall"]["wins"] = 999
        assert matchup_data["overall"]["wins"] == 10
