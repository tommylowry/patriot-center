"""Unit tests for head_to_head_queries module."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.queries.head_to_head_queries import (
    _evaluate_matchup,
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
        - `CACHE_MANAGER.get_manager_metadata_cache`: `mock_get_manager_cache`
        - `get_image_url`: `mock_get_image_url`

        Args:
            mock_manager_cache: Sample manager cache

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.get_image_url",
            ) as mock_get_image_url,
        ):
            mock_get_manager_cache.return_value = mock_manager_cache
            mock_get_image_url.return_value = {"data": "data"}

            yield

    def test_get_h2h_details(self):
        """Test getting head-to-head details."""
        result = get_head_to_head_details_from_cache(
            "Manager 1", year=None, opponent="Manager 2"
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
        - `CACHE_MANAGER.get_manager_metadata_cache`: `mock_get_manager_cache`
        - `get_matchup_card`: `mock_get_matchup_card`

        Args:
            mock_manager_cache: Sample manager cache

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.CACHE_MANAGER.get_manager_metadata_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.get_matchup_card",
            ) as mock_get_matchup_card,
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.validate_matchup_data",
            ) as mock_validate,
            patch(
                "patriot_center_backend.cache.queries"
                ".head_to_head_queries.get_head_to_head_details_from_cache",
            ) as mock_h2h_details,
            patch(
                "patriot_center_backend.cache.queries"
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
            self.mock_evaluate_matchup.return_value = (
                {"year": "2023", "week": "1"},
                {"year": "2023", "week": "1"},
            )

            yield

    def test_h2h_overall_stats(self, caplog: pytest.LogCaptureFixture):
        """Test comprehensive H2H stats calculation.

        Args:
            caplog: pytest caplog
        """
        result = get_head_to_head_overall_from_cache("Manager 1", "Manager 2")

        # Verify warning was printed out for no victories for Manager 2
        assert "No victories found for Manager 2" in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Check for manager-specific win keys
        assert "manager_1_wins" in result
        assert "manager_2_wins" in result
        assert "ties" in result

        # Verify _evaluate_matchup was called for manager 1's win
        self.mock_evaluate_matchup.assert_called_once()

    def test_h2h_no_matchups(self, caplog: pytest.LogCaptureFixture):
        """Test H2H when managers never played.

        Args:
            caplog: pytest caplog
        """
        result = get_head_to_head_overall_from_cache("Manager 1", "Manager 3")

        assert "No victories found for Manager 1" in caplog.text
        assert "No victories found for Manager 3" in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should handle gracefully even with no matchups
        assert result is not None
        assert isinstance(result, dict)

        # Verify _evaluate_matchup was NOT called (no matchups found)
        self.mock_evaluate_matchup.assert_not_called()

    def test_h2h_list_all_matchups(self):
        """Test H2H with list_all_matchups=True returns matchup history."""
        # Setup weeks data with matchups
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "win",
                    "points_for": 120.5,
                    "points_against": 100.0,
                },
                "transactions": {},
            },
            "2": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "loss",
                    "points_for": 90.0,
                    "points_against": 110.0,
                },
                "transactions": {},
            },
        }

        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", list_all_matchups=True
        )

        # Should return a list of matchup cards
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify _evaluate_matchup was NOT called (list_all_matchups mode)
        self.mock_evaluate_matchup.assert_not_called()

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
                    "points_against": 100.0,
                },
                "transactions": {},
            }
        }
        self.mock_manager_cache["Manager 1"]["years"]["2023"].update(
            {
                "summary": {
                    "matchup_data": {
                        "overall": {
                            "points_for": {"opponents": {"Manager 2": 100.0}}
                        }
                    }
                }
            }
        )

        self.mock_manager_cache["Manager 2"] = deepcopy(
            self.mock_manager_cache["Manager 1"]
        )

        self.mock_manager_cache["Manager 2"]["years"]["2023"].update(
            {
                "summary": {
                    "matchup_data": {
                        "overall": {
                            "points_for": {"opponents": {"Manager 1": 100.0}}
                        }
                    }
                }
            }
        )

        self.mock_h2h_details_value = {"wins": 1, "losses": 0, "ties": 0}

        result = get_head_to_head_overall_from_cache(
            "Manager 1", "Manager 2", year="2023"
        )

        assert "No victories found for Manager 2 against " in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should return dict with stats
        assert isinstance(result, dict)
        assert "manager_1_wins" in result

        # Verify _evaluate_matchup was called for manager 1's win
        self.mock_evaluate_matchup.assert_called_once()

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
                    "points_against": 110.0,
                },
                "transactions": {},
            },
            "2": {
                "matchup_data": {
                    "opponent_manager": "Manager 2",
                    "result": "loss",
                    "points_for": 85.0,
                    "points_against": 115.0,
                },
                "transactions": {},
            },
        }
        self.mock_manager_cache["Manager 2"] = deepcopy(
            self.mock_manager_cache["Manager 1"]
        )

        self.mock_h2h_details_value = {"wins": 0, "losses": 2, "ties": 0}
        self.mock_matchup_card_value = {
            "year": "2023",
            "week": "1",
            "margin": 20.0,
        }

        result = get_head_to_head_overall_from_cache("Manager 1", "Manager 2")

        assert "No victories found for Manager 1 against " in caplog.text
        assert "Cannot compute average margin of victory" in caplog.text

        # Should process manager2's wins correctly
        assert isinstance(result, dict)
        assert "manager_2_wins" in result

        # Verify _evaluate_matchup was called for manager 2's wins (2 times)
        assert self.mock_evaluate_matchup.call_count == 2


class TestEvaluateMatchup:
    """Test _evaluate_matchup function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common test data for all tests.

        Yields:
            None
        """
        self.matchup_card = {
            "year": "2023",
            "week": "5",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
            "manager_1_score": 120.5,
            "manager_2_score": 100.0,
        }

        yield

    def test_first_win_sets_last_win_and_biggest_blowout(self):
        """Test first win sets both last_win and biggest_blowout."""
        biggest_blowout = {}
        last_win = {}
        margins = []

        result_last_win, result_biggest_blowout = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=20.5,
            margins=margins,
        )

        assert result_last_win == self.matchup_card
        assert result_biggest_blowout == self.matchup_card
        assert margins == [20.5]

    def test_first_win_only_sets_last_win_when_biggest_blowout_exists(self):
        """Test first win only sets last_win when biggest_blowout exists."""
        existing_blowout = {
            "year": "2022",
            "week": "10",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
            "manager_1_score": 150.0,
            "manager_2_score": 90.0,
        }
        biggest_blowout = deepcopy(existing_blowout)
        last_win = {}
        margins = []

        result_last_win, result_biggest_blowout = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=20.5,
            margins=margins,
        )

        assert result_last_win == self.matchup_card
        assert result_biggest_blowout == existing_blowout
        assert margins == [20.5]

    def test_more_recent_win_updates_last_win(self):
        """Test more recent win (later year/week) updates last_win."""
        existing_last_win = {
            "year": "2023",
            "week": "3",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = deepcopy(existing_last_win)
        biggest_blowout = deepcopy(existing_last_win)
        margins = [15.0]

        result_last_win, _ = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=10.0,
            margins=margins,
        )

        # Week 5 > week 3, so should update
        assert result_last_win == self.matchup_card
        assert margins == [15.0, 10.0]

    def test_older_win_does_not_update_last_win(self):
        """Test older win does not update last_win."""
        existing_last_win = {
            "year": "2023",
            "week": "10",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = deepcopy(existing_last_win)
        biggest_blowout = {"year": "2023", "week": "1"}
        margins = [15.0]

        result_last_win, _ = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=10.0,
            margins=margins,
        )

        # Week 5 < week 10, so should NOT update
        assert result_last_win == existing_last_win
        assert margins == [15.0, 10.0]

    def test_more_recent_year_updates_last_win(self):
        """Test win in more recent year updates last_win."""
        existing_last_win = {
            "year": "2022",
            "week": "15",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = deepcopy(existing_last_win)
        biggest_blowout = deepcopy(existing_last_win)
        margins = [30.0]

        result_last_win, _ = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=20.5,
            margins=margins,
        )

        # 2023 > 2022, so should update even though week 5 < week 15
        assert result_last_win == self.matchup_card
        assert margins == [30.0, 20.5]

    def test_larger_margin_updates_biggest_blowout(self):
        """Test larger victory margin updates biggest_blowout."""
        existing_blowout = {
            "year": "2023",
            "week": "1",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = {"year": "2023", "week": "10"}
        biggest_blowout = deepcopy(existing_blowout)
        margins = [15.0]

        _, result_biggest_blowout = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=25.0,
            margins=margins,
        )

        # 25.0 > 15.0, so should update biggest_blowout
        assert result_biggest_blowout == self.matchup_card
        assert margins == [15.0, 25.0]

    def test_smaller_margin_does_not_update_biggest_blowout(self):
        """Test smaller victory margin does not update biggest_blowout."""
        existing_blowout = {
            "year": "2023",
            "week": "1",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = {"year": "2023", "week": "10"}
        biggest_blowout = deepcopy(existing_blowout)
        margins = [30.0]

        _, result_biggest_blowout = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=10.0,
            margins=margins,
        )

        # 10.0 < 30.0, so should NOT update biggest_blowout
        assert result_biggest_blowout == existing_blowout
        assert margins == [30.0, 10.0]

    def test_equal_margin_updates_biggest_blowout(self):
        """Test equal victory margin updates biggest_blowout (most recent)."""
        existing_blowout = {
            "year": "2023",
            "week": "1",
            "manager_1": "Tommy",
            "manager_2": "Manager 2",
        }
        last_win = {"year": "2023", "week": "10"}
        biggest_blowout = deepcopy(existing_blowout)
        margins = [20.5]

        _, result_biggest_blowout = _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=20.5,
            margins=margins,
        )

        # Equal margin (20.5 == max([20.5, 20.5])), so updates to most recent
        assert result_biggest_blowout == self.matchup_card
        assert margins == [20.5, 20.5]

    def test_margins_list_always_updated(self):
        """Test victory margin is always appended to margins list."""
        last_win = {"year": "2024", "week": "1"}
        biggest_blowout = {"year": "2024", "week": "1"}
        margins = [5.0, 10.0, 15.0]

        _evaluate_matchup(
            biggest_blowout=biggest_blowout,
            last_win=last_win,
            matchup_card=self.matchup_card,
            victory_margin=8.0,
            margins=margins,
        )

        assert margins == [5.0, 10.0, 15.0, 8.0]
