"""
Unit tests for cache_queries module.

Tests all cache query functions with both good and bad scenarios.
All functions are read-only and should not modify the cache.
"""
import pytest
from unittest.mock import patch
from copy import deepcopy


# Test fixture: Sample cache structure
@pytest.fixture
def sample_manager_cache():
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


@pytest.fixture
def valid_options_cache():
    """Create a sample valid options cache."""
    return {
        "2025": {
            "managers": ["Manager 1", "Manager 2", "Manager 3"]
        }
    }


@pytest.fixture
def transaction_ids_cache():
    """Create a sample transaction IDs cache."""
    return {
        "trade1": {
            "year": "2023",
            "week": "5",
            "managers_involved": ["Manager 1", "Manager 2"],
            "trade_details": {}
        }
    }

class TestAwardQueries:
    """Test award_queries submodule."""

    # =========================================
    # ===== get_manager_awards_from_cache =====
    # =========================================

    def test_manager_awards(self, sample_manager_cache):
        """Test getting manager awards."""
        with patch('patriot_center_backend.managers.cache_queries.award_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.award_queries import get_manager_awards_from_cache
            result = get_manager_awards_from_cache("Manager 1", {})

        # Should include various award categories
        assert "first_place" in result
        assert "second_place" in result
        assert "third_place" in result
        assert "playoff_appearances" in result
        assert result["first_place"] == 1  # From placement 2023
        assert result["playoff_appearances"] == 2

    # ===============================================
    # ===== get_manager_score_awards_from_cache =====
    # ===============================================

    def test_score_awards(self, sample_manager_cache):
        """Test getting scoring-related awards."""
        with patch('patriot_center_backend.managers.cache_queries.award_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.award_queries import get_manager_score_awards_from_cache
            result = get_manager_score_awards_from_cache("Manager 1", {})

        # Should include score-based awards
        assert isinstance(result, dict)
        assert "highest_weekly_score" in result
        assert "lowest_weekly_score" in result
        assert "biggest_blowout_win" in result
        assert "biggest_blowout_loss" in result


class TestHeadToHeadQueries:
    """Test head_to_head_queries submodule."""

    # ===============================================
    # ===== get_head_to_head_details_from_cache =====
    # ===============================================

    def test_get_h2h_details(self, sample_manager_cache):
        """Test getting head-to-head details."""
        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_details_from_cache
            result = get_head_to_head_details_from_cache("Manager 1", {}, year=None, opponent="Manager 2")

        # Should return single opponent dict
        assert isinstance(result, dict)
        assert "opponent" in result
        assert "wins" in result
        assert result["wins"] == 7
    
    # ===== get_head_to_head_overall_from_cache =====

    def test_h2h_overall_stats(self, sample_manager_cache):
        """Test comprehensive H2H stats calculation."""
        cache_copy = deepcopy(sample_manager_cache)

        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', cache_copy):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_overall_from_cache
            result = get_head_to_head_overall_from_cache("Manager 1", "Manager 2", {})

        # Check for manager-specific win keys
        assert "manager_1_wins" in result
        assert "manager_2_wins" in result
        assert "ties" in result

    def test_h2h_no_matchups(self, sample_manager_cache):
        """Test H2H when managers never played."""
        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_overall_from_cache
            result = get_head_to_head_overall_from_cache("Manager 1", "Manager 3", {})

        # Should handle gracefully even with no matchups
        assert result is not None
        assert isinstance(result, dict)
    
    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.get_matchup_card')
    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.validate_matchup_data')
    def test_h2h_list_all_matchups(self, mock_validator, mock_matchup_card, sample_manager_cache):
        """Test H2H with list_all_matchups=True returns matchup history."""
        # Setup weeks data with matchups
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
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

        mock_validator.return_value = ""
        mock_matchup_card.return_value = {"year": "2023", "week": "1"}

        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_overall_from_cache
            result = get_head_to_head_overall_from_cache(
                "Manager 1", "Manager 2", {},
                list_all_matchups=True
            )

        # Should return a list of matchup cards
        assert isinstance(result, list)
        assert len(result) == 2

    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.get_matchup_card')
    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.get_head_to_head_details_from_cache')
    def test_h2h_with_specific_year(self, mock_h2h_details, mock_matchup_card, sample_manager_cache):
        """Test H2H stats filtered to specific year."""
        # Setup weeks data
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
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
        sample_manager_cache["Manager 1"]["years"]["2023"]["summary"]["matchup_data"]["overall"]["points_for"]["opponents"]["Manager 2"] = 120.5
        sample_manager_cache["Manager 2"] = deepcopy(sample_manager_cache["Manager 1"])
        sample_manager_cache["Manager 2"]["years"]["2023"]["summary"]["matchup_data"]["overall"]["points_for"]["opponents"] = {"Manager 1": 100.0}

        mock_h2h_details.return_value = {"wins": 1, "losses": 0, "ties": 0}
        mock_matchup_card.return_value = {"year": "2023", "week": "1"}

        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_overall_from_cache
            result = get_head_to_head_overall_from_cache(
                "Manager 1", "Manager 2", {},
                year="2023"
            )

        # Should return dict with stats
        assert isinstance(result, dict)
        assert "manager_1_wins" in result

    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.get_matchup_card')
    @patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.get_head_to_head_details_from_cache')
    def test_h2h_manager2_wins(self, mock_h2h_details, mock_matchup_card, sample_manager_cache):
        """Test H2H when manager2 wins (result='loss' for manager1)."""
        # Setup weeks data where Manager 2 wins
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
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

        sample_manager_cache["Manager 2"] = deepcopy(sample_manager_cache["Manager 1"])

        mock_h2h_details.return_value = {"wins": 0, "losses": 2, "ties": 0}
        mock_matchup_card.return_value = {"year": "2023", "week": "1", "margin": 20.0}

        with patch('patriot_center_backend.managers.cache_queries.head_to_head_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.head_to_head_queries import get_head_to_head_overall_from_cache
            result = get_head_to_head_overall_from_cache("Manager 1", "Manager 2", {})

        # Should process manager2's wins correctly
        assert isinstance(result, dict)
        assert "manager_2_wins" in result


class TestMatchupQueries:
    """Test matchup_queries submodule."""

    # ==========================================
    # ===== get_matchup_details_from_cache =====
    # ==========================================

    def test_all_time_stats(self, sample_manager_cache):
        """Test getting all-time matchup stats."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            result = get_matchup_details_from_cache("Manager 1")

        assert result["overall"]["wins"] == 10
        assert result["overall"]["losses"] == 5
        assert result["overall"]["ties"] == 1
        assert result["overall"]["win_percentage"] == 62.5  # 10/(10+5+1) * 100 = 62.5%
        assert "average_points_for" in result["overall"]
        assert "average_points_against" in result["overall"]

    def test_single_season_stats(self, sample_manager_cache):
        """Test getting stats for a specific season."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            result = get_matchup_details_from_cache("Manager 1", year="2023")

        assert result["overall"]["wins"] == 6
        assert result["overall"]["losses"] == 2
        assert result["overall"]["ties"] == 0

    def test_manager_with_no_playoffs(self, sample_manager_cache):
        """Test manager who never made playoffs."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            result = get_matchup_details_from_cache("Manager 3")

        assert result["playoffs"]["wins"] == 0
        assert result["playoffs"]["losses"] == 0
        assert result["playoffs"]["win_percentage"] == 0.0
        assert result["playoffs"]["average_points_for"] == 0.0

    def test_win_percentage_calculation(self, sample_manager_cache):
        """Test win percentage is calculated correctly."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            result = get_matchup_details_from_cache("Manager 2")

        # 5 wins out of 16 games (5+10+1) = 31.25%
        assert result["overall"]["win_percentage"] == 31.2  # Rounded to 1 decimal

    def test_zero_matchups_no_division_by_zero(self, sample_manager_cache):
        """Test that zero matchups doesn't cause division by zero."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            result = get_matchup_details_from_cache("Manager 3")

        assert result["overall"]["win_percentage"] == 0.0
        assert result["overall"]["average_points_for"] == 0.0
    
    def test_get_matchup_details_immutable(self, sample_manager_cache):
        """Test that function doesn't modify cache."""
        original = deepcopy(sample_manager_cache)

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_matchup_details_from_cache
            get_matchup_details_from_cache("Manager 1")

        assert sample_manager_cache == original

    # ===============================================
    # ===== get_overall_data_details_from_cache =====
    # ===============================================

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_all_time_overall_data(self, mock_get_matchup_card, sample_manager_cache):
        """Test getting all-time overall data."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        # Add week 17 data for 2023 and 2022 to sample_manager_cache for opponent lookup
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", {})

        assert len(result["placements"]) == 2
        years = [p["year"] for p in result["placements"]]
        assert "2023" in years
        assert "2022" in years
        placement_2023 = next(p for p in result["placements"] if p["year"] == "2023")
        assert placement_2023["placement"] == 1
        assert placement_2023["matchup_card"] == {"mock": "matchup_card"}
        assert result["playoff_appearances"] == 2

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_single_season_overall_data(self, mock_get_matchup_card, sample_manager_cache):
        """Test getting single season overall data."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("2023", "Manager 1", {})

        assert len(result["placements"]) == 2  # Still returns all-time data
        placement_2023 = next(p for p in result["placements"] if p["year"] == "2023")
        assert placement_2023["placement"] == 1

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_manager_with_no_playoff_appearances(self, mock_get_matchup_card, sample_manager_cache):
        """Test manager with no playoff appearances."""
        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 3", {})

        assert result["playoff_appearances"] == 0
        assert result["placements"] == []
        mock_get_matchup_card.assert_not_called()

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_week_selection_for_year_2020_and_earlier(self, mock_get_matchup_card, sample_manager_cache):
        """Test that week 16 is used for years 2020 and earlier."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        # Add placement for 2020
        sample_manager_cache["Manager 1"]["summary"]["overall_data"]["placement"]["2020"] = 2
        sample_manager_cache["Manager 1"]["years"]["2020"] = {
            "weeks": {"16": {"matchup_data": {"opponent_manager": "Manager 2"}}}
        }
        # Also add week 17 data for other years
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", {})

        # Find the call for 2020 - should use week '16'
        calls = mock_get_matchup_card.call_args_list
        call_for_2020 = [c for c in calls if c[0][2] == "2020"]
        assert len(call_for_2020) == 1
        assert call_for_2020[0][0][3] == "16"  # week parameter should be '16'

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_week_selection_for_year_after_2020(self, mock_get_matchup_card, sample_manager_cache):
        """Test that week 17 is used for years after 2020."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", {})

        # All calls should use week '17' since both years are after 2020
        for call in mock_get_matchup_card.call_args_list:
            assert call[0][3] == "17"  # week parameter should be '17'

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_missing_opponent_skips_matchup_card(self, mock_get_matchup_card, sample_manager_cache, capsys):
        """Test that missing opponent results in warning and empty matchup_card."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        # Don't add week 17 data for 2022 - opponent will be missing
        sample_manager_cache["Manager 1"]["years"]["2022"] = {"weeks": {}}
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", {})

        # Verify warning was printed for missing opponent
        captured = capsys.readouterr()
        assert "WARNING: unable to retreive opponent" in captured.out
        assert "year 2022" in captured.out

        # Verify get_matchup_card was NOT called for 2022 (missing opponent)
        calls = mock_get_matchup_card.call_args_list
        call_years = [c[0][2] for c in calls]
        assert "2022" not in call_years
        assert "2023" in call_years  # 2023 should still be called

        # Verify the placement for 2022 has empty matchup_card
        placement_2022 = next(p for p in result["placements"] if p["year"] == "2022")
        assert placement_2022["matchup_card"] == {}

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_matchup_card_included_in_each_placement(self, mock_get_matchup_card, sample_manager_cache):
        """Test that matchup_card is included in each placement item."""
        mock_get_matchup_card.side_effect = [
            {"card": "2023_card"},
            {"card": "2022_card"}
        ]

        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", {})

        for placement in result["placements"]:
            assert "matchup_card" in placement

    @patch('patriot_center_backend.managers.cache_queries.matchup_queries.get_matchup_card')
    def test_passes_correct_params_to_get_matchup_card(self, mock_get_matchup_card, sample_manager_cache):
        """Test that all parameters are passed to get_matchup_card."""
        mock_get_matchup_card.return_value = {"mock": "matchup_card"}

        image_urls = {"url": "http://example.com"}

        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["17"] = {
            "matchup_data": {"opponent_manager": "Manager 2"}
        }
        sample_manager_cache["Manager 1"]["years"]["2022"] = {
            "weeks": {"17": {"matchup_data": {"opponent_manager": "Manager 3"}}}
        }

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            result = get_overall_data_details_from_cache("all_time", "Manager 1", image_urls)

        # Verify get_matchup_card was called with the correct parameters
        call_args = mock_get_matchup_card.call_args_list[0][0]
        assert call_args[0] == "Manager 1"   # manager
        # call_args[1] is opponent
        # call_args[2] is year
        # call_args[3] is week
        assert call_args[4] == image_urls
    
    def test_get_overall_data_immutable(self, sample_manager_cache):
        """Test that function doesn't modify cache."""
        original = deepcopy(sample_manager_cache)

        with patch('patriot_center_backend.managers.cache_queries.matchup_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.matchup_queries import get_overall_data_details_from_cache
            get_overall_data_details_from_cache("all_time", "Manager 1", {})

        assert sample_manager_cache == original


class TestRankingQueries:
    """Test ranking_queries submodule."""

    # ==========================================
    # ===== get_ranking_details_from_cache =====
    # ==========================================
    
    def test_get_rankings(self, sample_manager_cache, valid_options_cache):
        """Test getting ranking details."""
        with patch('patriot_center_backend.managers.cache_queries.ranking_queries.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.cache_queries.ranking_queries.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.cache_queries.ranking_queries import get_ranking_details_from_cache
            result = get_ranking_details_from_cache("Manager 1")

        # Should return dictionary with rankings
        assert isinstance(result, dict)
        assert "is_active_manager" in result
        assert "worst" in result
        assert result["worst"] == 3  # Total number of managers


class TestTransactionQueries:
    """Test transaction_queries submodule."""

    # ==================================================
    # ===== get_trade_history_between_two_managers =====
    # ==================================================

    @patch('patriot_center_backend.managers.cache_queries.transaction_queries.get_trade_card')
    def test_trade_history(self, mock_trade_card, sample_manager_cache, transaction_ids_cache):
        """Test getting trade history between managers."""
        mock_trade_card.return_value = {
            "year": "2023",
            "week": "5",
            "managers_involved": ["Manager 1", "Manager 2"]
        }

        # Add transaction_ids to the cache
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"]["1"]["transactions"] = {
            "trades": {"transaction_ids": ["trade1"]}
        }

        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.cache_queries.transaction_queries.TRANSACTION_IDS_CACHE', transaction_ids_cache):
            from patriot_center_backend.managers.cache_queries.transaction_queries import get_trade_history_between_two_managers
            result = get_trade_history_between_two_managers("Manager 1", "Manager 2", {})

        assert isinstance(result, list)
    
    # ==============================================
    # ===== get_transaction_details_from_cache =====
    # ==============================================

    @patch('patriot_center_backend.managers.cache_queries.transaction_queries.extract_dict_data')
    def test_all_time_transactions(self, mock_extract, sample_manager_cache):
        """Test getting all-time transaction stats."""
        mock_extract.return_value = []

        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.transaction_queries import get_transaction_details_from_cache
            result = get_transaction_details_from_cache(None, "Manager 1", {})

        assert result["trades"]["total"] == 5
        assert result["adds"]["total"] == 10
        assert result["drops"]["total"] == 10

    @patch('patriot_center_backend.managers.cache_queries.transaction_queries.extract_dict_data')
    def test_single_season_transactions(self, mock_extract, sample_manager_cache):
        """Test getting stats for specific season."""
        mock_extract.return_value = []

        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.transaction_queries import get_transaction_details_from_cache
            result = get_transaction_details_from_cache("2023", "Manager 1", {})

        assert result["trades"]["total"] == 2
        assert result["adds"]["total"] == 5
        assert result["drops"]["total"] == 5

    @patch('patriot_center_backend.managers.cache_queries.transaction_queries.extract_dict_data')
    def test_transactions_with_faab_data(self, mock_extract, sample_manager_cache):
        """Test getting transaction stats when FAAB data exists."""
        # Setup cache with FAAB data
        sample_manager_cache["Manager 1"]["summary"]["transactions"]["faab"] = {
            "total_lost_or_gained": -150,
            "players": {
                "Player A": {"num_bids_won": 2, "total_faab_spent": 100},
                "Player B": {"num_bids_won": 1, "total_faab_spent": 50}
            },
            "traded_away": {
                "total": 25,
                "trade_partners": {"Manager 2": 25}
            },
            "acquired_from": {
                "total": 30,
                "trade_partners": {"Manager 2": 30}
            }
        }

        mock_extract.return_value = []

        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.transaction_queries import get_transaction_details_from_cache
            result = get_transaction_details_from_cache(None, "Manager 1", {})

        # Assert FAAB summary was created
        assert "faab" in result
        assert result["faab"]["total_spent"] == 150  # abs(-150)
        assert result["faab"]["faab_traded"]["sent"] == 25
        assert result["faab"]["faab_traded"]["received"] == 30
        assert result["faab"]["faab_traded"]["net"] == 5  # 30 - 25
    
    @patch('patriot_center_backend.managers.cache_queries.transaction_queries.extract_dict_data')
    def test_get_transaction_details_immutable(self, mock_extract, sample_manager_cache):
        """Test that function doesn't modify cache."""
        mock_extract.return_value = []
        original = deepcopy(sample_manager_cache)

        with patch('patriot_center_backend.managers.cache_queries.transaction_queries.MANAGER_CACHE', sample_manager_cache):
            from patriot_center_backend.managers.cache_queries.transaction_queries import get_transaction_details_from_cache
            get_transaction_details_from_cache(None, "Manager 1", {})

        assert sample_manager_cache == original