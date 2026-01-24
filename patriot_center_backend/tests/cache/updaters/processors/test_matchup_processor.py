"""Unit tests for matchup_processor module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.processors.matchup_processor import MatchupProcessor


@pytest.fixture(autouse=True)
def globals_setup():
    """Setup common mocks for all tests.

    The mocks are set up to return a pre-defined
    set of values when accessed.
    - `LEAGUE_IDS`: `{2023: "mock_league_id"}`

    Yields:
        None
    """
    with patch(
        "patriot_center_backend.managers.matchup_processor.LEAGUE_IDS",
        {2023: "mock_league_id"},
    ):
        yield


@pytest.fixture
def mock_manager_cache() -> dict[str, Any]:
    """Create a sample cache for testing.

    Returns:
        Sample cache
    """
    return {
        "Manager 1": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                },
                "overall_data": {"playoff_appearances": []},
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                            "regular_season": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                        }
                    },
                    "weeks": {
                        "1": {"matchup_data": {}},
                        "15": {"matchup_data": {}},
                    },
                }
            },
        },
        "Manager 2": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                    },
                },
                "overall_data": {"playoff_appearances": []},
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                            "regular_season": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {
                                    "total": 0.0,
                                    "opponents": {},
                                },
                                "total_matchups": {"total": 0, "opponents": {}},
                            },
                        }
                    },
                    "weeks": {
                        "1": {"matchup_data": {}},
                        "15": {"matchup_data": {}},
                    },
                }
            },
        },
    }


@pytest.fixture
def mock_matchup_processor() -> MatchupProcessor:
    """Create MatchupProcessor instance.

    Returns:
        A MatchupProcessor interface.
    """
    return MatchupProcessor()


class TestMatchupProcessorInit:
    """Test MatchupProcessor initialization."""

    def test_init_sets_default_session_state(self):
        """Test that __init__ initializes empty session state."""
        processor = MatchupProcessor()

        assert processor._playoff_week_start is None
        assert processor._year is None
        assert processor._week is None
        assert processor._weekly_roster_ids == {}
        assert processor._playoff_roster_ids == []


class TestSessionState:
    """Test session state management."""

    def test_set_session_state(self, mock_matchup_processor: MatchupProcessor):
        """Test setting session state.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        playoff_roster_ids = [1]

        mock_matchup_processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids=weekly_roster_ids,
            playoff_roster_ids=playoff_roster_ids,
            playoff_week_start=15,
        )

        assert mock_matchup_processor._year == "2023"
        assert mock_matchup_processor._week == "1"
        assert mock_matchup_processor._weekly_roster_ids == weekly_roster_ids
        assert mock_matchup_processor._playoff_roster_ids == playoff_roster_ids
        assert mock_matchup_processor._playoff_week_start == 15

    def test_clear_session_state(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test clearing session state.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        # First set some state
        mock_matchup_processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1"},
            playoff_roster_ids=[],
            playoff_week_start=15,
        )

        # Then clear it
        mock_matchup_processor.clear_session_state()

        assert mock_matchup_processor._year is None
        assert mock_matchup_processor._week is None
        assert mock_matchup_processor._weekly_roster_ids == {}
        assert mock_matchup_processor._playoff_roster_ids == []


class TestScrubMatchupData:
    """Test scrub_matchup_data method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `get_season_state`: `mock_get_season_state`
        - `MatchupProcessor._add_matchup_details_to_cache`:
            `mock_add_matchup_to_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".get_season_state"
            ) as mock_get_season_state,
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".MatchupProcessor._add_matchup_details_to_cache"
            ) as mock_add_matchup_to_cache,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = []

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"

            self.mock_add_matchup_to_cache = mock_add_matchup_to_cache

            yield

    def test_scrub_matchup_data_regular_season_win(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test processes regular season matchup and calls cache update.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"
        self.mock_fetch_sleeper_data.return_value = [
            {
                "matchup_id": 1,
                "roster_id": 1,
                "points": 120.5,
                "players": ["player1", "player2"],
            },
            {
                "matchup_id": 1,
                "roster_id": 2,
                "points": 100.0,
                "players": ["player3", "player4"],
            },
        ]

        mock_matchup_processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids=[],
            playoff_week_start=15,
        )

        mock_matchup_processor.scrub_matchup_data()

        # Should call _add_matchup_details_to_cache twice
        # (once for each manager)
        assert self.mock_add_matchup_to_cache.call_count == 2

        # Check that Manager 1's call has correct data
        manager_1_call = next(
            call
            for call in self.mock_add_matchup_to_cache.call_args_list
            if call[0][0]["manager"] == "Manager 1"
        )
        assert manager_1_call[0][0]["opponent_manager"] == "Manager 2"
        assert manager_1_call[0][0]["result"] == "win"
        assert manager_1_call[0][0]["points_for"] == 120.5
        assert manager_1_call[0][0]["points_against"] == 100.0

    def test_scrub_matchup_data_tie(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test scrub_matchup_data correctly determines tie result.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"
        self.mock_fetch_sleeper_data.return_value = [
            {"matchup_id": 1, "roster_id": 1, "points": 100.0, "players": []},
            {"matchup_id": 1, "roster_id": 2, "points": 100.0, "players": []},
        ]

        mock_matchup_processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids=[],
            playoff_week_start=15,
        )

        mock_matchup_processor.scrub_matchup_data()

        # Both managers should have tie result
        assert self.mock_add_matchup_to_cache.call_count == 2
        for call in self.mock_add_matchup_to_cache.call_args_list:
            assert call[0][0]["result"] == "tie"
            assert call[0][0]["points_for"] == 100.0
            assert call[0][0]["points_against"] == 100.0

    def test_scrub_matchup_data_filters_playoff_teams(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test filters out non-playoff teams during playoffs.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        # Only rosters 1 and 2 in playoffs
        self.mock_get_season_state.return_value = "playoffs"
        self.mock_fetch_sleeper_data.return_value = [
            {"matchup_id": 1, "roster_id": 1, "points": 120.5, "players": []},
            {"matchup_id": 1, "roster_id": 2, "points": 100.0, "players": []},
            {"matchup_id": 2, "roster_id": 3, "points": 90.0, "players": []},
            {"matchup_id": 2, "roster_id": 4, "points": 85.0, "players": []},
        ]

        mock_matchup_processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={
                1: "Manager 1",
                2: "Manager 2",
                3: "Manager 3",
                4: "Manager 4",
            },
            playoff_roster_ids=[1, 2],  # Only rosters 1 and 2 in playoffs
            playoff_week_start=15,
        )

        mock_matchup_processor.scrub_matchup_data()

        # Should only process matchup 1 (playoff teams), not matchup 2
        assert self.mock_add_matchup_to_cache.call_count == 2

        # Verify it was called for Manager 1 and Manager 2, not Manager 3 or 4
        call_list = self.mock_add_matchup_to_cache.call_args_list

        managers_called = [call[0][0]["manager"] for call in call_list]
        assert "Manager 1" in managers_called
        assert "Manager 2" in managers_called
        assert "Manager 3" not in managers_called
        assert "Manager 4" not in managers_called


class TestAddMatchupDetailsToCache:
    """Unit tests for _add_matchup_details_to_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `get_season_state`: `mock_get_season_state`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.matchup_processor"
                ".get_season_state"
            ) as mock_get_season_state,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_get_season_state = mock_get_season_state
            self.mock_get_season_state.return_value = "regular_season"
            yield

    def test_add_matchup_details_updates_weekly_cache(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache updates weekly matchup data.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "1"
        mock_matchup_processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
            "result": "win",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup_data)

        # Assert weekly cache was updated
        weekly_data = (
            self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]
        )
        assert weekly_data["matchup_data"]["opponent_manager"] == "Manager 2"
        assert weekly_data["matchup_data"]["points_for"] == 120.5
        assert weekly_data["matchup_data"]["points_against"] == 100.0
        assert weekly_data["matchup_data"]["result"] == "win"

    def test_add_matchup_details_updates_yearly_summary(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache updates yearly summary stats.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "1"
        mock_matchup_processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
            "result": "win",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup_data)

        # Assert yearly overall summary was updated
        year_level = self.mock_manager_cache["Manager 1"]["years"]["2023"]

        yearly_overall = year_level["summary"]["matchup_data"]["overall"]
        assert yearly_overall["wins"]["total"] == 1
        assert yearly_overall["wins"]["opponents"]["Manager 2"] == 1
        assert yearly_overall["points_for"]["total"] == 120.5
        assert yearly_overall["points_for"]["opponents"]["Manager 2"] == 120.5
        assert yearly_overall["total_matchups"]["total"] == 1

        # Assert yearly season-state summary was updated
        yearly_season = year_level["summary"]["matchup_data"]["regular_season"]
        assert yearly_season["wins"]["total"] == 1
        assert yearly_season["points_for"]["total"] == 120.5

    def test_add_matchup_details_updates_top_level_summary(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache updates top-level summary stats.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "playoffs"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "15"
        mock_matchup_processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 150.0,
            "points_against": 145.5,
            "result": "win",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup_data)

        # Assert top-level overall summary was updated
        manager_summary_level = self.mock_manager_cache["Manager 1"]["summary"]

        top_overall = manager_summary_level["matchup_data"]["overall"]
        assert top_overall["wins"]["total"] == 1
        assert top_overall["points_for"]["total"] == 150.0

        # Assert top-level playoff summary was updated
        top_playoffs = manager_summary_level["matchup_data"]["playoffs"]
        assert top_playoffs["wins"]["total"] == 1
        assert top_playoffs["points_for"]["total"] == 150.0

    def test_add_matchup_details_handles_loss(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache correctly handles a loss.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "1"
        mock_matchup_processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 90.0,
            "points_against": 110.5,
            "result": "loss",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup_data)

        # Assert loss was recorded
        year_level = self.mock_manager_cache["Manager 1"]["years"]["2023"]
        yearly_overall = year_level["summary"]["matchup_data"]["overall"]

        assert yearly_overall["losses"]["total"] == 1
        assert yearly_overall["losses"]["opponents"]["Manager 2"] == 1
        assert yearly_overall["wins"]["total"] == 0

    def test_add_matchup_details_handles_tie(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache correctly handles a tie.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "1"
        mock_matchup_processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 100.0,
            "points_against": 100.0,
            "result": "tie",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup_data)

        # Assert loss was recorded
        year_level = self.mock_manager_cache["Manager 1"]["years"]["2023"]
        yearly_overall = year_level["summary"]["matchup_data"]["overall"]

        assert yearly_overall["ties"]["total"] == 1
        assert yearly_overall["ties"]["opponents"]["Manager 2"] == 1

    def test_add_matchup_details_raises_on_invalid_data(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test _add_matchup_details_to_cache raises on invalid matchup data.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        mock_matchup_processor._year = "2023"
        mock_matchup_processor._week = "1"
        mock_matchup_processor._playoff_week_start = 15

        # Missing opponent_manager
        invalid_matchup = {
            "manager": "Manager 1",
            "points_for": 100.0,
            "points_against": 100.0,
            "result": "win",
        }

        with pytest.raises(ValueError, match="Invalid matchup data") as e:
            mock_matchup_processor._add_matchup_details_to_cache(
                invalid_matchup
            )
        assert "Invalid matchup data" in str(e.value)

    def test_processor_modifies_cache_in_place(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test that processor modifies the cache that was passed in.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        self.mock_get_season_state.return_value = "regular_season"

        original_cache = self.mock_manager_cache

        mock_matchup_processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids=[],
            playoff_week_start=15,
        )

        matchup = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
            "result": "win",
        }
        mock_matchup_processor._add_matchup_details_to_cache(matchup)

        # Verify cache was modified (same object reference)
        mgr_summary = self.mock_manager_cache["Manager 1"]["summary"]
        assert self.mock_manager_cache is original_cache
        assert mgr_summary["matchup_data"]["overall"]["wins"]["total"] == 1


class TestScrubPlayoffData:
    """Test scrub_playoff_data method."""

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
                "patriot_center_backend.managers.matchup_processor"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_scrub_playoff_data_adds_appearances(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test that scrub_playoff_data adds playoff appearances.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        mock_matchup_processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids=[1, 2],
            playoff_week_start=15,
        )

        mock_matchup_processor.scrub_playoff_data()

        # Check that playoff appearances were added
        mgr1_overall = (
            self.mock_manager_cache["Manager 1"]["summary"]["overall_data"]
        )
        mgr2_overall = (
            self.mock_manager_cache["Manager 2"]["summary"]["overall_data"]
        )

        assert "2023" in mgr1_overall["playoff_appearances"]
        assert "2023" in mgr2_overall["playoff_appearances"]

    def test_scrub_playoff_data_skips_duplicates(
        self, mock_matchup_processor: MatchupProcessor
    ):
        """Test that duplicate playoff appearances are not added.

        Args:
            mock_matchup_processor: A MatchupProcessor interface.
        """
        # Pre-populate with existing playoff appearance
        mgr1_overall = (
            self.mock_manager_cache["Manager 1"]["summary"]["overall_data"]
        )
        mgr1_overall["playoff_appearances"].append("2023")

        mock_matchup_processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={1: "Manager 1"},
            playoff_roster_ids=[1],
            playoff_week_start=15,
        )

        mock_matchup_processor.scrub_playoff_data()

        # Should still only have one appearance
        appearances = mgr1_overall["playoff_appearances"]
        assert appearances.count("2023") == 1
