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


class TestAddMatchupDetailsToCache:
    """Test _add_matchup_details_to_cache method - unit tests calling function directly."""

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_updates_weekly_cache(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache updates weekly matchup data."""
        mock_season_state.return_value = "regular_season"
        processor._year = "2023"
        processor._week = "1"
        processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
            "result": "win"
        }

        processor._add_matchup_details_to_cache(matchup_data)

        # Assert weekly cache was updated
        weekly_data = processor._cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["matchup_data"]
        assert weekly_data["opponent_manager"] == "Manager 2"
        assert weekly_data["points_for"] == 120.5
        assert weekly_data["points_against"] == 100.0
        assert weekly_data["result"] == "win"

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_updates_yearly_summary(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache updates yearly summary stats."""
        mock_season_state.return_value = "regular_season"
        processor._year = "2023"
        processor._week = "1"
        processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
            "result": "win"
        }

        processor._add_matchup_details_to_cache(matchup_data)

        # Assert yearly overall summary was updated
        yearly_overall = processor._cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]["overall"]
        assert yearly_overall["wins"]["total"] == 1
        assert yearly_overall["wins"]["opponents"]["Manager 2"] == 1
        assert yearly_overall["points_for"]["total"] == 120.5
        assert yearly_overall["points_for"]["opponents"]["Manager 2"] == 120.5
        assert yearly_overall["total_matchups"]["total"] == 1

        # Assert yearly season-state summary was updated
        yearly_season = processor._cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]["regular_season"]
        assert yearly_season["wins"]["total"] == 1
        assert yearly_season["points_for"]["total"] == 120.5

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_updates_top_level_summary(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache updates top-level summary stats."""
        mock_season_state.return_value = "playoffs"
        processor._year = "2023"
        processor._week = "15"
        processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 150.0,
            "points_against": 145.5,
            "result": "win"
        }

        processor._add_matchup_details_to_cache(matchup_data)

        # Assert top-level overall summary was updated
        top_overall = processor._cache["Manager 1"]["summary"]["matchup_data"]["overall"]
        assert top_overall["wins"]["total"] == 1
        assert top_overall["points_for"]["total"] == 150.0

        # Assert top-level playoff summary was updated
        top_playoffs = processor._cache["Manager 1"]["summary"]["matchup_data"]["playoffs"]
        assert top_playoffs["wins"]["total"] == 1
        assert top_playoffs["points_for"]["total"] == 150.0

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_handles_loss(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache correctly handles a loss."""
        mock_season_state.return_value = "regular_season"
        processor._year = "2023"
        processor._week = "1"
        processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 90.0,
            "points_against": 110.5,
            "result": "loss"
        }

        processor._add_matchup_details_to_cache(matchup_data)

        # Assert loss was recorded
        yearly_overall = processor._cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]["overall"]
        assert yearly_overall["losses"]["total"] == 1
        assert yearly_overall["losses"]["opponents"]["Manager 2"] == 1
        assert yearly_overall["wins"]["total"] == 0

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_handles_tie(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache correctly handles a tie."""
        mock_season_state.return_value = "regular_season"
        processor._year = "2023"
        processor._week = "1"
        processor._playoff_week_start = 15

        matchup_data = {
            "manager": "Manager 1",
            "opponent_manager": "Manager 2",
            "points_for": 100.0,
            "points_against": 100.0,
            "result": "tie"
        }

        processor._add_matchup_details_to_cache(matchup_data)

        # Assert tie was recorded
        yearly_overall = processor._cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]["overall"]
        assert yearly_overall["ties"]["total"] == 1
        assert yearly_overall["ties"]["opponents"]["Manager 2"] == 1

    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_add_matchup_details_raises_on_invalid_data(self, mock_season_state, processor):
        """Test _add_matchup_details_to_cache raises on invalid matchup data."""
        mock_season_state.return_value = "regular_season"
        processor._year = "2023"
        processor._week = "1"
        processor._playoff_week_start = 15

        # Missing opponent_manager
        invalid_matchup = {
            "manager": "Manager 1",
            "points_for": 100.0,
            "points_against": 100.0,
            "result": "win"
        }

        with pytest.raises(ValueError, match="Invalid matchup data"):
            processor._add_matchup_details_to_cache(invalid_matchup)


class TestScrubMatchupData:
    """Test scrub_matchup_data method."""

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_regular_season_win(self, mock_season_state, mock_fetch, processor):
        """Test scrub_matchup_data processes regular season matchup and calls cache update."""
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

        with patch.object(processor, '_add_matchup_details_to_cache') as mock_add:
            processor.scrub_matchup_data("2023", "1")

            # Should call _add_matchup_details_to_cache twice (once for each manager)
            assert mock_add.call_count == 2

            # Check that Manager 1's call has correct data
            manager_1_call = [call for call in mock_add.call_args_list
                             if call[0][0]["manager"] == "Manager 1"][0]
            assert manager_1_call[0][0]["opponent_manager"] == "Manager 2"
            assert manager_1_call[0][0]["result"] == "win"
            assert manager_1_call[0][0]["points_for"] == 120.5
            assert manager_1_call[0][0]["points_against"] == 100.0

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_tie(self, mock_season_state, mock_fetch, processor):
        """Test scrub_matchup_data correctly determines tie result."""
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

        with patch.object(processor, '_add_matchup_details_to_cache') as mock_add:
            processor.scrub_matchup_data("2023", "1")

            # Both managers should have tie result
            assert mock_add.call_count == 2
            for call in mock_add.call_args_list:
                assert call[0][0]["result"] == "tie"
                assert call[0][0]["points_for"] == 100.0
                assert call[0][0]["points_against"] == 100.0

    @patch('patriot_center_backend.managers.matchup_processor.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.matchup_processor.get_season_state')
    def test_scrub_matchup_data_filters_playoff_teams(self, mock_season_state, mock_fetch, processor):
        """Test scrub_matchup_data filters out non-playoff teams during playoffs."""
        mock_season_state.return_value = "playoffs"
        mock_fetch.return_value = ([
            {"matchup_id": 1, "roster_id": 1, "points": 120.5, "players": []},  # In playoffs
            {"matchup_id": 1, "roster_id": 2, "points": 100.0, "players": []},  # In playoffs
            {"matchup_id": 2, "roster_id": 3, "points": 90.0, "players": []},   # Not in playoffs
            {"matchup_id": 2, "roster_id": 4, "points": 85.0, "players": []}    # Not in playoffs
        ], 200)

        processor.set_session_state(
            year="2023",
            week="15",
            weekly_roster_ids={1: "Manager 1", 2: "Manager 2", 3: "Manager 3", 4: "Manager 4"},
            playoff_roster_ids={"round_roster_ids": [1, 2]},  # Only rosters 1 and 2 in playoffs
            playoff_week_start=15
        )

        with patch.object(processor, '_add_matchup_details_to_cache') as mock_add:
            processor.scrub_matchup_data("2023", "15")

            # Should only process matchup 1 (playoff teams), not matchup 2
            assert mock_add.call_count == 2
            # Verify it was called for Manager 1 and Manager 2, not Manager 3 or 4
            managers_called = [call[0][0]["manager"] for call in mock_add.call_args_list]
            assert "Manager 1" in managers_called
            assert "Manager 2" in managers_called
            assert "Manager 3" not in managers_called
            assert "Manager 4" not in managers_called


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
