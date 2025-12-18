"""
Unit tests for manager_metadata_manager.py internal helper methods.
Tests all private helper methods used by the public get_ methods.
"""
import pytest
from unittest.mock import patch
import copy


@pytest.fixture
def mock_full_manager_cache():
    """Comprehensive manager cache data for testing helper methods."""
    return {
        "Tommy": {
            "summary": {
                "user_id": "user_123",
                "overall_data": {
                    "avatar_urls": {
                        "full_size": "https://sleepercdn.com/avatars/avatar_url",
                        "thumbnail": "https://sleepercdn.com/avatars/thumbs/avatar_url"
                    },
                    "placement": {
                        "2023": 2,
                        "2024": 1
                    },
                    "playoff_appearances": ["2023", "2024"]
                },
                "matchup_data": {
                    "overall": {
                        "points_for": {"total": 2500.0, "opponents": {"Mike": 250.0, "Owen": 300.0}},
                        "points_against": {"total": 2400.0, "opponents": {"Mike": 240.0, "Owen": 290.0}},
                        "total_matchups": {"total": 20, "opponents": {"Mike": 3, "Owen": 4}},
                        "wins": {"total": 12, "opponents": {"Mike": 2, "Owen": 3}},
                        "losses": {"total": 8, "opponents": {"Mike": 1, "Owen": 1}},
                        "ties": {"total": 0, "opponents": {}}
                    },
                    "regular_season": {
                        "points_for": {"total": 2100.0, "opponents": {}},
                        "points_against": {"total": 2000.0, "opponents": {}},
                        "total_matchups": {"total": 17, "opponents": {}},
                        "wins": {"total": 10, "opponents": {}},
                        "losses": {"total": 7, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}}
                    },
                    "playoffs": {
                        "points_for": {"total": 400.0, "opponents": {}},
                        "points_against": {"total": 400.0, "opponents": {}},
                        "total_matchups": {"total": 3, "opponents": {}},
                        "wins": {"total": 2, "opponents": {}},
                        "losses": {"total": 1, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 15,
                        "trade_partners": {"Mike": 5, "Owen": 7, "Soup": 3},
                        "trade_players_acquired": {
                            "Amon-Ra St. Brown": {
                                "total": 3,
                                "trade_partners": {"Mike": 2, "Owen": 1}
                            },
                            "Travis Kelce": {
                                "total": 2,
                                "trade_partners": {"Mike": 1, "Soup": 1}
                            }
                        },
                        "trade_players_sent": {
                            "Justin Jefferson": {
                                "total": 2,
                                "trade_partners": {"Owen": 2}
                            }
                        }
                    },
                    "adds": {
                        "total": 30,
                        "players": {
                            "Isaiah Likely": 2,
                            "Tank Dell": 3,
                            "Zay Flowers": 1
                        }
                    },
                    "drops": {
                        "total": 25,
                        "players": {
                            "Gus Edwards": 2,
                            "Antonio Gibson": 1
                        }
                    },
                    "faab": {
                        "total_lost_or_gained": -150,
                        "players": {
                            "Isaiah Likely": 46,
                            "Tank Dell": 25,
                            "Jordan Mason": 35
                        },
                        "traded_away": {
                            "total": 80,
                            "trade_partners": {"Mike": 50, "Owen": 30}
                        },
                        "acquired_from": {
                            "total": 60,
                            "trade_partners": {"Soup": 60}
                        }
                    }
                }
            },
            "years": {
                "2024": {
                    "roster_id": 1,
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "points_for": {"total": 1500.0, "opponents": {}},
                                "points_against": {"total": 1400.0, "opponents": {}},
                                "total_matchups": {"total": 14, "opponents": {}},
                                "wins": {"total": 8, "opponents": {}},
                                "losses": {"total": 6, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            },
                            "regular_season": {
                                "points_for": {"total": 1300.0, "opponents": {}},
                                "points_against": {"total": 1200.0, "opponents": {}},
                                "total_matchups": {"total": 13, "opponents": {}},
                                "wins": {"total": 7, "opponents": {}},
                                "losses": {"total": 6, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            },
                            "playoffs": {
                                "points_for": {"total": 200.0, "opponents": {}},
                                "points_against": {"total": 200.0, "opponents": {}},
                                "total_matchups": {"total": 1, "opponents": {}},
                                "wins": {"total": 1, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {
                                "total": 5,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {}
                            },
                            "adds": {"total": 10, "players": {}},
                            "drops": {"total": 8, "players": {}},
                            "faab": {
                                "total_lost_or_gained": -50,
                                "players": {},
                                "traded_away": {"total": 20, "trade_partners": {}},
                                "acquired_from": {"total": 10, "trade_partners": {}}
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Mike",
                                "points_for": 130.5,
                                "points_against": 115.3,
                                "result": "win"
                            },
                            "transactions": {
                                "trades": {
                                    "total": 1,
                                    "trade_partners": {"Mike": 1},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": ["tx456"]
                                },
                                "adds": {"total": 1, "players": {"Isaiah Likely": 1}, "transaction_ids": ["tx123"]},
                                "drops": {"total": 0, "players": {}, "transaction_ids": []}
                            }
                        },
                        "2": {
                            "matchup_data": {
                                "opponent_manager": "Owen",
                                "points_for": 110.0,
                                "points_against": 125.0,
                                "result": "loss"
                            },
                            "transactions": {
                                "trades": {"total": 0, "trade_partners": {}, "trade_players_acquired": {}, "trade_players_sent": {}, "transaction_ids": []},
                                "adds": {"total": 0, "players": {}, "transaction_ids": []},
                                "drops": {"total": 1, "players": {"Gus Edwards": 1}, "transaction_ids": ["tx789"]}
                            }
                        }
                    }
                }
            }
        },
        "Mike": {
            "summary": {
                "user_id": "user_456",
                "overall_data": {
                    "avatar_urls": {},
                    "placement": {},
                    "playoff_appearances": []
                },
                "matchup_data": {
                    "overall": {
                        "points_for": {"total": 2000.0, "opponents": {"Tommy": 240.0}},
                        "points_against": {"total": 2100.0, "opponents": {"Tommy": 250.0}},
                        "total_matchups": {"total": 20, "opponents": {"Tommy": 3}},
                        "wins": {"total": 8, "opponents": {"Tommy": 1}},
                        "losses": {"total": 12, "opponents": {"Tommy": 2}},
                        "ties": {"total": 0, "opponents": {}}
                    },
                    "regular_season": {
                        "points_for": {"total": 2000.0, "opponents": {}},
                        "points_against": {"total": 2100.0, "opponents": {}},
                        "total_matchups": {"total": 20, "opponents": {}},
                        "wins": {"total": 8, "opponents": {}},
                        "losses": {"total": 12, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}}
                    },
                    "playoffs": {
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}},
                        "total_matchups": {"total": 0, "opponents": {}},
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {"total": 5, "trade_partners": {"Tommy": 5}, "trade_players_acquired": {}, "trade_players_sent": {}},
                    "adds": {"total": 15, "players": {}},
                    "drops": {"total": 12, "players": {}},
                    "faab": {
                        "total_lost_or_gained": -100,
                        "players": {},
                        "traded_away": {"total": 0, "trade_partners": {}},
                        "acquired_from": {"total": 50, "trade_partners": {"Tommy": 50}}
                    }
                }
            },
            "years": {
                "2024": {
                    "roster_id": 2,
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "points_for": {"total": 1400.0, "opponents": {}},
                                "points_against": {"total": 1500.0, "opponents": {}},
                                "total_matchups": {"total": 14, "opponents": {}},
                                "wins": {"total": 6, "opponents": {}},
                                "losses": {"total": 8, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            },
                            "regular_season": {
                                "points_for": {"total": 1400.0, "opponents": {}},
                                "points_against": {"total": 1500.0, "opponents": {}},
                                "total_matchups": {"total": 14, "opponents": {}},
                                "wins": {"total": 6, "opponents": {}},
                                "losses": {"total": 8, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            },
                            "playoffs": {
                                "points_for": {"total": 0.0, "opponents": {}},
                                "points_against": {"total": 0.0, "opponents": {}},
                                "total_matchups": {"total": 0, "opponents": {}},
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {"total": 3, "trade_partners": {}, "trade_players_acquired": {}, "trade_players_sent": {}},
                            "adds": {"total": 8, "players": {}},
                            "drops": {"total": 6, "players": {}},
                            "faab": {
                                "total_lost_or_gained": -80,
                                "players": {},
                                "traded_away": {"total": 0, "trade_partners": {}},
                                "acquired_from": {"total": 30, "trade_partners": {}}
                            }
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Tommy",
                                "points_for": 115.3,
                                "points_against": 130.5,
                                "result": "loss"
                            },
                            "transactions": {
                                "trades": {
                                    "total": 1,
                                    "trade_partners": {"Tommy": 1},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": ["tx456"]
                                },
                                "adds": {"total": 0, "players": {}, "transaction_ids": []},
                                "drops": {"total": 0, "players": {}, "transaction_ids": []}
                            }
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_transaction_cache():
    """Sample transaction ID cache."""
    return {
        "tx123": {
            "year": "2024",
            "week": "1",
            "managers_involved": ["Tommy"],
            "types": ["add"],
            "players_involved": ["Isaiah Likely"],
            "add": "Isaiah Likely",
            "faab_spent": 46
        },
        "tx456": {
            "year": "2024",
            "week": "1",
            "managers_involved": ["Tommy", "Mike"],
            "types": ["trade"],
            "players_involved": ["Amon-Ra St. Brown", "Travis Kelce"],
            "trade_details": {
                "Amon-Ra St. Brown": {
                    "old_manager": "Mike",
                    "new_manager": "Tommy"
                },
                "Travis Kelce": {
                    "old_manager": "Tommy",
                    "new_manager": "Mike"
                }
            }
        },
        "tx789": {
            "year": "2024",
            "week": "2",
            "managers_involved": ["Tommy"],
            "types": ["drop"],
            "players_involved": ["Gus Edwards"],
            "drop": "Gus Edwards"
        }
    }


class TestGetMatchupDetailsFromCache:
    """Test _get_matchup_details_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_formatted_matchup_data_all_time(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns properly formatted matchup data for all-time stats."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        # Inject the cache data directly since these are internal methods
        manager._cache = mock_full_manager_cache

        result = manager._get_matchup_details_from_cache("Tommy")

        # Check structure
        assert "overall" in result
        assert "regular_season" in result
        assert "playoffs" in result

        # Check overall stats
        assert result["overall"]["record"] == "12-8-0"
        assert result["overall"]["win_percentage"] == 60.0
        assert result["overall"]["total_points_for"] == 2500.0
        assert result["overall"]["total_points_against"] == 2400.0
        assert result["overall"]["point_differential"] == 100.0

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_formatted_matchup_data_for_specific_year(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns properly formatted matchup data for specific year."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache

        result = manager._get_matchup_details_from_cache("Tommy", year="2024")

        # Should use yearly data
        assert result["overall"]["record"] == "8-6-0"
        assert result["overall"]["total_points_for"] == 1500.0

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_handles_no_playoff_appearances(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test handles managers with no playoff appearances correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache

        result = manager._get_matchup_details_from_cache("Mike")

        # Playoffs should have all zeros
        assert result["playoffs"]["record"] == "0-0-0"
        assert result["playoffs"]["win_percentage"] == 0.0
        assert result["playoffs"]["total_points_for"] == 0
        assert result["playoffs"]["average_points_for"] == 0.0


class TestGetTransactionDetailsFromCache:
    """Test _get_trasaction_details_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_formatted_transaction_summary(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns properly formatted transaction summary."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_trasaction_details_from_cache("Tommy")

        # Check structure
        assert "trades" in result
        assert "adds" in result
        assert "drops" in result
        assert "faab" in result

        # Check trades
        assert result["trades"]["total"] == 15
        assert len(result["trades"]["top_trade_partners"]) <= 3

        # Check FAAB
        assert result["faab"]["total_spent"] == 150
        assert result["faab"]["faab_traded"]["sent"] == 80
        assert result["faab"]["faab_traded"]["received"] == 60
        assert result["faab"]["faab_traded"]["net"] == -20


class TestGetOverallDataDetailsFromCache:
    """Test _get_overall_data_details_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_career_accomplishments(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns career accomplishments correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_overall_data_details_from_cache("Tommy")

        # Check playoff appearances
        assert result["playoff_appearances"] == 2

        # Check placements
        assert len(result["placements"]) == 2
        assert result["best_finish"] == 1
        assert result["championships"] == 1


class TestGetHeadToHeadDetailsFromCache:
    """Test _get_head_to_head_details_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_all_opponents_when_no_filter(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns all opponents when no opponent filter specified."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_head_to_head_details_from_cache("Tommy")

        # Should have multiple opponents
        assert "Mike" in result
        assert "Owen" in result
        assert result["Mike"]["wins"] == 2
        assert result["Mike"]["losses"] == 1

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_single_opponent_when_filtered(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns single opponent data when opponent filter specified."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_head_to_head_details_from_cache("Tommy", opponent="Mike")

        # Should be single opponent dict
        assert "wins" in result
        assert "losses" in result
        assert result["wins"] == 2
        assert result["losses"] == 1


class TestGetWeeklyTradeDetailsFromCache:
    """Test _get_weekly_trade_details_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_weekly_trade_details(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache, mock_transaction_cache):
        """Test returns trade details for a specific week."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        manager._transaction_id_cache = mock_transaction_cache

        result = manager._get_weekly_trade_details_from_cache("Tommy", "2024", "1")

        # Should have one trade
        assert len(result) == 1
        assert result[0]["partners"] == ["Mike"]
        assert "Amon-Ra St. Brown" in result[0]["acquired"]
        assert "Travis Kelce" in result[0]["sent"]


class TestGetTopThreeOfDict:
    """Test _get_top_three_of_dict utility helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_top_three_from_simple_dict(self, mock_load_cache, mock_load_player_ids):
        """Test returns top three entries from simple count dict."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        data = {
            "Player A": 10,
            "Player B": 5,
            "Player C": 8,
            "Player D": 3,
            "Player E": 7
        }

        result = manager._get_top_three_of_dict(copy.deepcopy(data))

        # Should return top 3
        assert len(result) == 3
        assert result[0]["name"] == "Player A"
        assert result[0]["count"] == 10
        assert result[1]["name"] == "Player C"
        assert result[1]["count"] == 8

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_handles_ties_for_third_place(self, mock_load_cache, mock_load_player_ids):
        """Test handles ties by including all tied entries."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        data = {
            "Player A": 10,
            "Player B": 8,
            "Player C": 5,
            "Player D": 5,
            "Player E": 3
        }

        result = manager._get_top_three_of_dict(copy.deepcopy(data))

        # Should include both Player C and D (tied for 3rd)
        assert len(result) == 4
        names = [r["name"] for r in result]
        assert "Player C" in names
        assert "Player D" in names

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_handles_dict_with_nested_total_values(self, mock_load_cache, mock_load_player_ids):
        """Test handles dict where values are dicts with 'total' key."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        data = {
            "Player A": {"total": 10},
            "Player B": {"total": 5},
            "Player C": {"total": 8}
        }

        result = manager._get_top_three_of_dict(copy.deepcopy(data))

        # Should extract total values and return top 3
        assert len(result) == 3
        assert result[0]["count"] == 10

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_handles_fewer_than_three_items(self, mock_load_cache, mock_load_player_ids):
        """Test handles dict with fewer than 3 entries."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        data = {
            "Player A": 10,
            "Player B": 5
        }

        result = manager._get_top_three_of_dict(copy.deepcopy(data))

        # Should return all 2 items
        assert len(result) == 2

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_uses_custom_key_name(self, mock_load_cache, mock_load_player_ids):
        """Test uses custom key name when specified."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        data = {
            "Player A": 100,
            "Player B": 50,
            "Player C": 75
        }

        result = manager._get_top_three_of_dict(copy.deepcopy(data), key_name="amount")

        # Should use 'amount' instead of 'count'
        assert result[0]["amount"] == 100
        assert "count" not in result[0]


class TestGetManagerAwardsFromCache:
    """Test _get_manager_awards_from_cache helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_calculates_placement_counts(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test calculates first/second/third place counts correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_manager_awards_from_cache("Tommy")

        assert result["first_place"] == 1
        assert result["second_place"] == 1
        assert result["third_place"] == 0

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_finds_most_trades_in_year(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test finds year with most trades."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_manager_awards_from_cache("Tommy")

        assert "most_trades_in_year" in result
        assert result["most_trades_in_year"]["count"] == 5
        assert result["most_trades_in_year"]["year"] == "2024"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_finds_biggest_faab_bid(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test finds biggest FAAB bid."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache
        result = manager._get_manager_awards_from_cache("Tommy")

        assert "biggest_faab_bid" in result
        assert result["biggest_faab_bid"]["player"] == "Isaiah Likely"
        assert result["biggest_faab_bid"]["amount"] == 46


class TestValidateMatchupData:
    """Test _validate_matchup_data helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_empty_string_for_valid_data(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test returns empty string when matchup data is valid."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache

        valid_matchup = {
            "opponent_manager": "Mike",
            "result": "win",
            "points_for": 120.5,
            "points_against": 115.3
        }

        result = manager._validate_matchup_data(valid_matchup)
        assert result == ""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_detects_missing_opponent(self, mock_load_cache, mock_load_player_ids):
        """Test detects missing opponent_manager."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        invalid_matchup = {
            "result": "win",
            "points_for": 120.5,
            "points_against": 115.3
        }

        result = manager._validate_matchup_data(invalid_matchup)
        assert "no opponent_data" in result

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_detects_mismatched_win_result(self, mock_load_cache, mock_load_player_ids, mock_full_manager_cache):
        """Test detects when result is win but points don't match."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_full_manager_cache

        invalid_matchup = {
            "opponent_manager": "Mike",
            "result": "win",
            "points_for": 100.0,
            "points_against": 120.0  # More than points_for, should be loss
        }

        result = manager._validate_matchup_data(invalid_matchup)
        assert "result is win but points_against" in result


class TestDraftPickDecipher:
    """Test _draft_pick_decipher helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_formats_draft_pick_correctly(self, mock_load_cache, mock_load_player_ids):
        """Test formats draft pick string correctly."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._weekly_roster_ids = {1: "Tommy", 2: "Mike"}

        draft_pick = {
            "season": "2025",
            "round": 3,
            "roster_id": 1
        }

        result = manager._draft_pick_decipher(draft_pick)
        assert result == "Tommy's 2025 Round 3 Draft Pick"


class TestGetSeasonState:
    """Test _get_season_state helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_regular_season_before_playoffs(self, mock_load_cache, mock_load_player_ids):
        """Test returns regular_season for weeks before playoffs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "10"
        manager._playoff_week_start = 15

        result = manager._get_season_state()
        assert result == "regular_season"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_playoffs_during_playoff_weeks(self, mock_load_cache, mock_load_player_ids):
        """Test returns playoffs for weeks during playoffs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "15"
        manager._playoff_week_start = 15

        result = manager._get_season_state()
        assert result == "playoffs"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_when_week_not_set(self, mock_load_cache, mock_load_player_ids):
        """Test raises error when week or year not set."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()

        with pytest.raises(ValueError, match="Week or Year not set"):
            manager._get_season_state()


class TestCachingPreconditionsMet:
    """Test _caching_preconditions_met helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_when_no_roster_ids(self, mock_load_cache, mock_load_player_ids):
        """Test raises error when no roster IDs cached."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"

        with pytest.raises(ValueError, match="No roster IDs cached"):
            manager._caching_preconditions_met()

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_odd_number_rosters(self, mock_load_cache, mock_load_player_ids):
        """Test raises error when odd number of roster IDs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._weekly_roster_ids = {1: "Tommy"}
        manager._year = "2024"
        manager._week = "1"

        with pytest.raises(ValueError, match="Odd number of roster IDs"):
            manager._caching_preconditions_met()

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_passes_when_all_conditions_met(self, mock_load_cache, mock_load_player_ids):
        """Test passes when all preconditions are met."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._weekly_roster_ids = {1: "Tommy", 2: "Mike"}
        manager._year = "2024"
        manager._week = "1"

        # Should not raise
        manager._caching_preconditions_met()


class TestClearWeeklyMetadata:
    """Test _clear_weekly_metadata helper method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_clears_week_and_year(self, mock_load_cache, mock_load_player_ids):
        """Test clears week and year metadata."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "1"
        manager._weekly_roster_ids = {1: "Tommy", 2: "Mike"}

        manager._clear_weekly_metadata()

        assert manager._year is None
        assert manager._week is None

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_clears_roster_ids_on_week_17(self, mock_load_cache, mock_load_player_ids):
        """Test clears roster IDs when clearing week 17 of 2024."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._year = "2024"
        manager._week = "17"
        manager._weekly_roster_ids = {1: "Tommy", 2: "Mike"}

        manager._clear_weekly_metadata()

        assert manager._weekly_roster_ids == {}
