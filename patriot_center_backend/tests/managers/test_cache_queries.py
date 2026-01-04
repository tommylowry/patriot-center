"""
Unit tests for cache_queries module.

Tests all cache query functions with both good and bad scenarios.
All functions are read-only and should not modify the cache.
"""
import pytest
from unittest.mock import patch
from copy import deepcopy
from patriot_center_backend.managers.cache_queries import (
    get_matchup_details_from_cache,
    get_transaction_details_from_cache,
    get_overall_data_details_from_cache,
    get_ranking_details_from_cache,
    get_head_to_head_details_from_cache,
    get_head_to_head_overall_from_cache,
    get_trade_history_between_two_managers,
    get_manager_awards_from_cache,
    get_manager_score_awards_from_cache
)


# Test fixture: Sample cache structure
@pytest.fixture
def sample_cache():
    """Create a sample cache for testing."""
    return {
        "Manager 1": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 10, "opponents": {"Manager 2": 7, "Manager 3": 3}},
                        "losses": {"total": 5, "opponents": {"Manager 2": 3, "Manager 3": 2}},
                        "ties": {"total": 1, "opponents": {"Manager 2": 1}},
                        "points_for": {"total": 1500.50, "opponents": {"Manager 2": 1000.00, "Manager 3": 500.50}},
                        "points_against": {"total": 1400.25, "opponents": {"Manager 2": 900.00, "Manager 3": 500.25}}
                    },
                    "regular_season": {
                        "wins": {"total": 8, "opponents": {}},
                        "losses": {"total": 4, "opponents": {}},
                        "ties": {"total": 1, "opponents": {}},
                        "points_for": {"total": 1300.00, "opponents": {}},
                        "points_against": {"total": 1200.00, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 2, "opponents": {}},
                        "losses": {"total": 1, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 200.50, "opponents": {}},
                        "points_against": {"total": 200.25, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 5,
                        "trade_partners": {"Manager 2": 3, "Manager 3": 2},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 10, "players": {}},
                    "drops": {"total": 10, "players": {}}
                },
                "overall_data": {
                    "placement": {"2023": 1, "2022": 3},
                    "playoff_appearances": ["2023", "2022"]
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 6, "opponents": {}},
                                "losses": {"total": 2, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 800.00, "opponents": {}},
                                "points_against": {"total": 700.00, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 5, "opponents": {}},
                                "losses": {"total": 2, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 700.00, "opponents": {}},
                                "points_against": {"total": 600.00, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 1, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 100.00, "opponents": {}},
                                "points_against": {"total": 100.00, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {
                                "total": 2,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {}
                            },
                            "adds": {"total": 5, "players": {}},
                            "drops": {"total": 5, "players": {}}
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Manager 2",
                                "result": "win",
                                "points_for": 120.5,
                                "points_against": 100.0
                            }
                        }
                    }
                }
            }
        },
        "Manager 2": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 5, "opponents": {"Manager 1": 3}},
                        "losses": {"total": 10, "opponents": {"Manager 1": 7}},
                        "ties": {"total": 1, "opponents": {"Manager 1": 1}},
                        "points_for": {"total": 1400.25, "opponents": {"Manager 1": 900.00}},
                        "points_against": {"total": 1500.50, "opponents": {"Manager 1": 1000.00}}
                    },
                    "regular_season": {
                        "wins": {"total": 4, "opponents": {}},
                        "losses": {"total": 8, "opponents": {}},
                        "ties": {"total": 1, "opponents": {}},
                        "points_for": {"total": 1200.00, "opponents": {}},
                        "points_against": {"total": 1300.00, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 1, "opponents": {}},
                        "losses": {"total": 2, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 200.25, "opponents": {}},
                        "points_against": {"total": 200.50, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 3,
                        "trade_partners": {"Manager 1": 3},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 8, "players": {}},
                    "drops": {"total": 8, "players": {}}
                },
                "overall_data": {
                    "placement": {"2023": 5, "2022": 7},
                    "playoff_appearances": ["2023", "2022"]
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 2, "opponents": {}},
                                "losses": {"total": 6, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 700.00, "opponents": {}},
                                "points_against": {"total": 800.00, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 2, "opponents": {}},
                                "losses": {"total": 5, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 600.00, "opponents": {}},
                                "points_against": {"total": 700.00, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 1, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 100.00, "opponents": {}},
                                "points_against": {"total": 100.00, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {
                                "total": 1,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {}
                            },
                            "adds": {"total": 3, "players": {}},
                            "drops": {"total": 3, "players": {}}
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Manager 1",
                                "result": "loss",
                                "points_for": 100.0,
                                "points_against": 120.5
                            }
                        }
                    }
                }
            }
        },
        "Manager 3": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 2,
                        "trade_partners": {"Manager 1": 2},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 0, "players": {}},
                    "drops": {"total": 0, "players": {}}
                },
                "overall_data": {
                    "placement": {},
                    "playoff_appearances": []
                }
            },
            "years": {}
        }
    }


class TestGetMatchupDetailsFromCache:
    """Test get_matchup_details_from_cache function."""

    def test_all_time_stats(self, sample_cache):
        """Test getting all-time matchup stats."""
        result = get_matchup_details_from_cache(sample_cache, "Manager 1")

        assert result["overall"]["wins"] == 10
        assert result["overall"]["losses"] == 5
        assert result["overall"]["ties"] == 1
        assert result["overall"]["win_percentage"] == 62.5  # 10/(10+5+1) * 100 = 62.5%
        assert "average_points_for" in result["overall"]
        assert "average_points_against" in result["overall"]

    def test_single_season_stats(self, sample_cache):
        """Test getting stats for a specific season."""
        result = get_matchup_details_from_cache(sample_cache, "Manager 1", year="2023")

        assert result["overall"]["wins"] == 6
        assert result["overall"]["losses"] == 2
        assert result["overall"]["ties"] == 0

    def test_manager_with_no_playoffs(self, sample_cache):
        """Test manager who never made playoffs."""
        result = get_matchup_details_from_cache(sample_cache, "Manager 3")

        assert result["playoffs"]["wins"] == 0
        assert result["playoffs"]["losses"] == 0
        assert result["playoffs"]["win_percentage"] == 0.0
        assert result["playoffs"]["average_points_for"] == 0.0

    def test_win_percentage_calculation(self, sample_cache):
        """Test win percentage is calculated correctly."""
        result = get_matchup_details_from_cache(sample_cache, "Manager 2")

        # 5 wins out of 16 games (5+10+1) = 31.25%
        assert result["overall"]["win_percentage"] == 31.2  # Rounded to 1 decimal

    def test_zero_matchups_no_division_by_zero(self, sample_cache):
        """Test that zero matchups doesn't cause division by zero."""
        result = get_matchup_details_from_cache(sample_cache, "Manager 3")

        assert result["overall"]["win_percentage"] == 0.0
        assert result["overall"]["average_points_for"] == 0.0


class TestGetTransactionDetailsFromCache:
    """Test get_transaction_details_from_cache function."""

    @patch('patriot_center_backend.managers.cache_queries.extract_dict_data')
    def test_all_time_transactions(self, mock_extract, sample_cache):
        """Test getting all-time transaction stats."""
        mock_extract.return_value = []

        result = get_transaction_details_from_cache(
            sample_cache, None, "Manager 1", {}, {}, {}
        )

        assert result["trades"]["total"] == 5
        assert result["adds"]["total"] == 10
        assert result["drops"]["total"] == 10

    @patch('patriot_center_backend.managers.cache_queries.extract_dict_data')
    def test_single_season_transactions(self, mock_extract, sample_cache):
        """Test getting stats for specific season."""
        mock_extract.return_value = []

        result = get_transaction_details_from_cache(
            sample_cache, "2023", "Manager 1", {}, {}, {}
        )

        assert result["trades"]["total"] == 2
        assert result["adds"]["total"] == 5
        assert result["drops"]["total"] == 5


class TestGetOverallDataDetailsFromCache:
    """Test get_overall_data_details_from_cache function."""

    def test_all_time_overall_data(self, sample_cache):
        """Test getting all-time overall data."""
        result = get_overall_data_details_from_cache(sample_cache, "all_time", "Manager 1")

        assert len(result["placements"]) == 2
        years = [p["year"] for p in result["placements"]]
        assert "2023" in years
        assert "2022" in years
        placement_2023 = next(p for p in result["placements"] if p["year"] == "2023")
        assert placement_2023["placement"] == 1
        assert result["playoff_appearances"] == 2

    def test_single_season_overall_data(self, sample_cache):
        """Test getting single season overall data."""
        result = get_overall_data_details_from_cache(sample_cache, "2023", "Manager 1")

        assert len(result["placements"]) == 2  # Still returns all-time data
        placement_2023 = next(p for p in result["placements"] if p["year"] == "2023")
        assert placement_2023["placement"] == 1

    def test_manager_with_no_playoff_appearances(self, sample_cache):
        """Test manager with no playoff appearances."""
        result = get_overall_data_details_from_cache(sample_cache, "all_time", "Manager 3")

        assert result["playoff_appearances"] == 0
        assert result["placements"] == []


class TestGetRankingDetailsFromCache:
    """Test get_ranking_details_from_cache function."""

    def test_get_rankings(self, sample_cache):
        """Test getting ranking details."""
        valid_options = {
            "2025": {
                "managers": ["Manager 1", "Manager 2", "Manager 3"]
            }
        }

        result = get_ranking_details_from_cache(
            sample_cache, "Manager 1", valid_options
        )

        # Should return dictionary with rankings
        assert isinstance(result, dict)
        assert "is_active_manager" in result
        assert "worst" in result
        assert result["worst"] == 3  # Total number of managers


class TestGetHeadToHeadDetailsFromCache:
    """Test get_head_to_head_details_from_cache function."""

    def test_get_h2h_details(self, sample_cache):
        """Test getting head-to-head details."""
        result = get_head_to_head_details_from_cache(
            sample_cache, "Manager 1", {}, {}, {}, year=None, opponent="Manager 2"
        )

        # Should return single opponent dict
        assert isinstance(result, dict)
        assert "opponent" in result
        assert "wins" in result
        assert result["wins"] == 7


class TestGetHeadToHeadOverallFromCache:
    """Test get_head_to_head_overall_from_cache function."""

    def test_h2h_overall_stats(self, sample_cache):
        """Test comprehensive H2H stats calculation."""
        cache_copy = deepcopy(sample_cache)

        result = get_head_to_head_overall_from_cache(
            cache_copy, "Manager 1", "Manager 2",
            {}, {}, {}, {}
        )

        # Check for manager-specific win keys
        assert "manager_1_wins" in result
        assert "manager_2_wins" in result
        assert "ties" in result

    def test_h2h_no_matchups(self, sample_cache):
        """Test H2H when managers never played."""
        result = get_head_to_head_overall_from_cache(
            sample_cache, "Manager 1", "Manager 3",
            {}, {}, {}, {}
        )

        # Should handle gracefully even with no matchups
        assert result is not None
        assert isinstance(result, dict)


class TestGetTradeHistoryBetweenTwoManagers:
    """Test get_trade_history_between_two_managers function."""

    @patch('patriot_center_backend.managers.cache_queries.get_trade_card')
    def test_trade_history(self, mock_trade_card, sample_cache):
        """Test getting trade history between managers."""
        mock_trade_card.return_value = {
            "year": "2023",
            "week": "5",
            "managers_involved": ["Manager 1", "Manager 2"]
        }

        transaction_ids_cache = {
            "trade1": {
                "year": "2023",
                "week": "5",
                "managers_involved": ["Manager 1", "Manager 2"],
                "trade_details": {}
            }
        }

        result = get_trade_history_between_two_managers(
            sample_cache, "Manager 1", "Manager 2",
            transaction_ids_cache, "all_time", {}, {}, {}
        )

        assert isinstance(result, list)


class TestGetManagerAwardsFromCache:
    """Test get_manager_awards_from_cache function."""

    def test_manager_awards(self, sample_cache):
        """Test getting manager awards."""
        result = get_manager_awards_from_cache(
            sample_cache, "Manager 1", {}, {}, {}
        )

        # Should include various award categories
        assert "first_place" in result
        assert "second_place" in result
        assert "third_place" in result
        assert "playoff_appearances" in result
        assert result["first_place"] == 1  # From placement 2023
        assert result["playoff_appearances"] == 2


class TestGetManagerScoreAwardsFromCache:
    """Test get_manager_score_awards_from_cache function."""

    def test_score_awards(self, sample_cache):
        """Test getting scoring-related awards."""
        # Add starters cache for score awards
        starters_cache = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Total_Points": 120.5
                    }
                }
            }
        }

        result = get_manager_score_awards_from_cache(
            sample_cache, "Manager 1", {}, {}, {}, starters_cache
        )

        # Should include score-based awards
        assert isinstance(result, dict)
        assert "highest_weekly_score" in result
        assert "lowest_weekly_score" in result
        assert "biggest_blowout_win" in result
        assert "biggest_blowout_loss" in result


class TestCacheImmutability:
    """Test that cache query functions don't modify the cache."""

    def test_get_matchup_details_immutable(self, sample_cache):
        """Test that function doesn't modify cache."""
        original = deepcopy(sample_cache)

        get_matchup_details_from_cache(sample_cache, "Manager 1")

        assert sample_cache == original

    @patch('patriot_center_backend.managers.cache_queries.extract_dict_data')
    def test_get_transaction_details_immutable(self, mock_extract, sample_cache):
        """Test that function doesn't modify cache."""
        mock_extract.return_value = []
        original = deepcopy(sample_cache)

        get_transaction_details_from_cache(
            sample_cache, None, "Manager 1", {}, {}, {}
        )

        assert sample_cache == original

    def test_get_overall_data_immutable(self, sample_cache):
        """Test that function doesn't modify cache."""
        original = deepcopy(sample_cache)

        get_overall_data_details_from_cache(sample_cache, "all_time", "Manager 1")

        assert sample_cache == original
