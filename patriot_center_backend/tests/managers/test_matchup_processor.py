"""
Unit tests for matchup_processor module.

Tests the MatchupProcessor class which handles matchup and playoff data processing.
All tests mock API calls and avoid modifying real cache files.
"""
import pytest
from unittest.mock import patch, MagicMock
from copy import deepcopy
from patriot_center_backend.managers.matchup_processor import MatchupProcessor


@pytest.fixture
def sample_cache():
    """Create a sample cache for testing."""
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
                        "total_matchups": {"total": 0, "opponents": {}}
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}}
                    }
                },
                "overall_data": {
                    "playoff_appearances": []
                }
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
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {}
                        },
                        "15": {
                            "matchup_data": {}
                        }
                    }
                }
            }
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
                        "total_matchups": {"total": 0, "opponents": {}}
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}}
                    }
                },
                "overall_data": {
                    "playoff_appearances": []
                }
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
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}}
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {}
                        },
                        "15": {
                            "matchup_data": {}
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def processor(sample_cache):
    """Create MatchupProcessor instance."""
    return MatchupProcessor(cache=sample_cache, playoff_week_start=15)


class TestMatchupProcessorInit:
    """Test MatchupProcessor initialization."""

    def test_init_stores_cache(self, sample_cache):
        """Test that __init__ stores cache reference."""
        processor = MatchupProcessor(cache=sample_cache, playoff_week_start=15)

        assert processor._cache == sample_cache
        assert processor._playoff_week_start == 15

    def test_init_sets_default_session_state(self, sample_cache):
        """Test that __init__ initializes empty session state."""
        processor = MatchupProcessor(cache=sample_cache, playoff_week_start=15)

        assert processor._year is None
        assert processor._week is None
        assert processor._weekly_roster_ids == {}
        assert processor._playoff_roster_ids == {}


class TestSessionState:
    """Test session state management."""

    def test_set_session_state(self, processor):
        """Test setting session state."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        playoff_roster_ids = {1: "Manager 1"}

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids=weekly_roster_ids,
            playoff_roster_ids=playoff_roster_ids,
            playoff_week_start=15
        )

        assert processor._year == "2023"
        assert processor._week == "1"
        assert processor._weekly_roster_ids == weekly_roster_ids
        assert processor._playoff_roster_ids == playoff_roster_ids
        assert processor._playoff_week_start == 15

    def test_clear_session_state(self, processor):
        """Test clearing session state."""
        # First set some state
        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1"},
            playoff_roster_ids={},
            playoff_week_start=15
        )

        # Then clear it
        processor.clear_session_state()

        assert processor._year is None
        assert processor._week is None
        assert processor._weekly_roster_ids == {}
        assert processor._playoff_roster_ids == {}


class TestScrubMatchupData:
    """Test scrub_matchup_data method."""

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_regular_season_win(self, mock_season_state, mock_fetch, processor):
        """Test processing a regular season win."""
        mock_season_state.return_value = "regular_season"
        mock_fetch.return_value = ([
            {
                "matchup_id": 1,
                "roster_id": 1,
                "points": 120.5,
                "players": ["player1", "player2"]
            },
            {
                "matchup_id": 1,
                "roster_id": 2,
                "points": 100.0,
                "players": ["player3", "player4"]
            }
        ], 200)

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids={},
            playoff_week_start=15
        )

        processor.scrub_matchup_data("2023", "1")

        # Check that matchup was added to weekly cache
        assert "1" in processor._cache["Manager 1"]["years"]["2023"]["weeks"]
        matchup_data = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["matchup_data"]
        assert matchup_data["opponent_manager"] == "Manager 2"
        assert matchup_data["result"] == "win"
        assert matchup_data["points_for"] == 120.5
        assert matchup_data["points_against"] == 100.0

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_tie(self, mock_season_state, mock_fetch, processor):
        """Test processing a tie matchup."""
        mock_season_state.return_value = "regular_season"
        mock_fetch.return_value = ([
            {
                "matchup_id": 1,
                "roster_id": 1,
                "points": 100.0,
                "players": []
            },
            {
                "matchup_id": 1,
                "roster_id": 2,
                "points": 100.0,
                "players": []
            }
        ], 200)

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids={},
            playoff_week_start=15
        )

        processor.scrub_matchup_data("2023", "1")

        matchup_data = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["matchup_data"]
        assert matchup_data["result"] == "tie"

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_updates_aggregates(self, mock_season_state, mock_fetch, processor):
        """Test that matchup data updates aggregate stats."""
        mock_season_state.return_value = "regular_season"
        mock_fetch.return_value = ([
            {"matchup_id": 1, "roster_id": 1, "points": 120.5, "players": []},
            {"matchup_id": 1, "roster_id": 2, "points": 100.0, "players": []}
        ], 200)

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids={},
            playoff_week_start=15
        )

        processor.scrub_matchup_data("2023", "1")

        # Check yearly summary updated
        yearly_summary = processor._cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]
        assert yearly_summary["overall"]["wins"]["total"] == 1
        assert yearly_summary["regular_season"]["wins"]["total"] == 1
        assert yearly_summary["overall"]["points_for"]["total"] == 120.5

        # Check all-time summary updated
        all_time_summary = processor._cache["Manager 1"]["summary"]["matchup_data"]
        assert all_time_summary["overall"]["wins"]["total"] == 1
        assert all_time_summary["regular_season"]["wins"]["total"] == 1


class TestScrubPlayoffData:
    """Test scrub_playoff_data method."""

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    def test_scrub_playoff_data_adds_appearances(self, mock_fetch, processor):
        """Test that scrub_playoff_data adds playoff appearances."""
        mock_fetch.return_value = ({
            "bracket": [
                {"r": 1, "m": 1},  # Round 1, matchup 1
                {"r": 1, "m": 2}   # Round 1, matchup 2
            ]
        }, 200)

        processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids={"round_roster_ids": [1, 2]},
            playoff_week_start=15
        )

        processor.scrub_playoff_data()

        # Check that playoff appearances were added
        assert "2023" in processor._cache["Manager 1"]["summary"]["overall_data"]["playoff_appearances"]
        assert "2023" in processor._cache["Manager 2"]["summary"]["overall_data"]["playoff_appearances"]

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    def test_scrub_playoff_data_skips_duplicates(self, mock_fetch, processor):
        """Test that duplicate playoff appearances are not added."""
        # Pre-populate with existing playoff appearance
        processor._cache["Manager 1"]["summary"]["overall_data"]["playoff_appearances"].append("2023")

        mock_fetch.return_value = ({
            "bracket": [{"r": 1, "m": 1}]
        }, 200)

        processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={1: "Manager 1"},
            playoff_roster_ids={"round_roster_ids": [1]},
            playoff_week_start=15
        )

        processor.scrub_playoff_data()

        # Should still only have one appearance
        appearances = processor._cache["Manager 1"]["summary"]["overall_data"]["playoff_appearances"]
        assert appearances.count("2023") == 1


class TestCacheModification:
    """Test that processor correctly modifies cache."""

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_processor_modifies_cache_in_place(self, mock_season_state, mock_fetch, sample_cache):
        """Test that processor modifies the cache that was passed in."""
        mock_season_state.return_value = "regular_season"
        mock_fetch.return_value = ([
            {"matchup_id": 1, "roster_id": 1, "points": 120.5, "players": []},
            {"matchup_id": 1, "roster_id": 2, "points": 100.0, "players": []}
        ], 200)

        original_cache = sample_cache
        processor = MatchupProcessor(cache=sample_cache, playoff_week_start=15)

        processor.set_session_state(
            year="2023",
            week="1",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2"},
            playoff_roster_ids={},
            playoff_week_start=15
        )

        processor.scrub_matchup_data("2023", "1")

        # Verify cache was modified (same object reference)
        assert processor._cache is original_cache
        assert original_cache["Manager 1"]["summary"]["matchup_data"]["overall"]["wins"]["total"] == 1
