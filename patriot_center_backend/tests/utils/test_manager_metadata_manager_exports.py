"""
Unit tests for manager_metadata_manager.py public export methods (get_ methods).
Tests the 6 new public methods for exporting manager data.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal


@pytest.fixture
def mock_manager_cache():
    """Sample manager cache data for testing export methods."""
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
                        "2024": 1
                    },
                    "playoff_appearances": ["2024"]
                },
                "matchup_data": {
                    "overall": {
                        "points_for": {"total": 1500.0, "opponents": {"Mike": 150.0}},
                        "points_against": {"total": 1400.0, "opponents": {"Mike": 140.0}},
                        "total_matchups": {"total": 14, "opponents": {"Mike": 2}},
                        "wins": {"total": 8, "opponents": {"Mike": 1}},
                        "losses": {"total": 6, "opponents": {"Mike": 1}},
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
                        "total": 10,
                        "trade_partners": {"Mike": 3, "Owen": 5, "Soup": 2},
                        "trade_players_acquired": {
                            "Amon-Ra St. Brown": {
                                "total": 2,
                                "trade_partners": {"Mike": 1, "Owen": 1}
                            }
                        },
                        "trade_players_sent": {
                            "Travis Kelce": {
                                "total": 1,
                                "trade_partners": {"Mike": 1}
                            }
                        }
                    },
                    "adds": {
                        "total": 25,
                        "players": {
                            "Isaiah Likely": 1,
                            "Tank Dell": 2
                        }
                    },
                    "drops": {
                        "total": 20,
                        "players": {
                            "Gus Edwards": 1
                        }
                    },
                    "faab": {
                        "total_lost_or_gained": -100,
                        "players": {
                            "Isaiah Likely": 46,
                            "Tank Dell": 25
                        },
                        "traded_away": {
                            "total": 50,
                            "trade_partners": {"Mike": 30, "Owen": 20}
                        },
                        "acquired_from": {
                            "total": 30,
                            "trade_partners": {"Soup": 30}
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
                            "trades": {"total": 5, "trade_partners": {}, "trade_players_acquired": {}, "trade_players_sent": {}},
                            "adds": {"total": 10, "players": {}},
                            "drops": {"total": 8, "players": {}},
                            "faab": {"total_lost_or_gained": -50, "players": {"Isaiah Likely": 46}, "traded_away": {"total": 0, "trade_partners": {}}, "acquired_from": {"total": 0, "trade_partners": {}}}
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Mike",
                                "points_for": 120.5,
                                "points_against": 115.3,
                                "result": "win"
                            },
                            "transactions": {
                                "trades": {"total": 0, "trade_partners": {}, "trade_players_acquired": {}, "trade_players_sent": {}, "transaction_ids": []},
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
                                "trades": {"total": 1, "trade_partners": {"Mike": 1}, "trade_players_acquired": {}, "trade_players_sent": {}, "transaction_ids": ["tx456"]},
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
                    "avatar_urls": {
                        "full_size": "https://sleepercdn.com/avatars/mike_avatar",
                        "thumbnail": "https://sleepercdn.com/avatars/thumbs/mike_avatar"
                    },
                    "placement": {},
                    "playoff_appearances": []
                },
                "matchup_data": {
                    "overall": {
                        "points_for": {"total": 1400.0, "opponents": {"Tommy": 140.0}},
                        "points_against": {"total": 1500.0, "opponents": {"Tommy": 150.0}},
                        "total_matchups": {"total": 14, "opponents": {"Tommy": 2}},
                        "wins": {"total": 6, "opponents": {"Tommy": 1}},
                        "losses": {"total": 8, "opponents": {"Tommy": 1}},
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
                    "trades": {"total": 5, "trade_partners": {"Tommy": 3}, "trade_players_acquired": {}, "trade_players_sent": {}},
                    "adds": {"total": 15, "players": {}},
                    "drops": {"total": 12, "players": {}},
                    "faab": {"total_lost_or_gained": 0, "players": {}, "traded_away": {"total": 0, "trade_partners": {}}, "acquired_from": {"total": 0, "trade_partners": {}}}
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
                            "faab": {"total_lost_or_gained": 0, "players": {}, "traded_away": {"total": 0, "trade_partners": {}}, "acquired_from": {"total": 0, "trade_partners": {}}}
                        }
                    },
                    "weeks": {}
                }
            }
        }
    }


@pytest.fixture
def mock_transaction_id_cache():
    """Sample transaction ID cache for testing."""
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
            "week": "2",
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


class TestGetManagersList:
    """Test get_managers_list method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_list_of_all_managers(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test returns list of all managers with basic info."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]  # Empty initial load
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        # Inject the cache data directly
        manager._cache = mock_manager_cache

        result = manager.get_managers_list()

        assert "managers" in result
        assert len(result["managers"]) == 2

        # Check Tommy's data
        tommy = next(m for m in result["managers"] if m["name"] == "Tommy")
        assert tommy["overall_record"] == "8-6-0"
        assert tommy["total_trades"] == 10
        assert "2024" in tommy["years_active"]
        assert tommy["avatar_urls"]["full_size"] == "https://sleepercdn.com/avatars/avatar_url"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_empty_list_for_no_managers(self, mock_load_cache, mock_load_player_ids):
        """Test returns empty list when no managers in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]  # Empty caches
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        result = manager.get_managers_list()

        assert result == {"managers": []}


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_complete_summary_for_manager(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test returns complete summary data for a manager."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_manager_summary("Tommy")

        assert result["manager_name"] == "Tommy"
        assert result["user_id"] == "user_123"
        assert "matchup_data" in result
        assert "transactions" in result
        assert "overall_data" in result
        assert "head_to_head" in result

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_manager(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for manager not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Manager Unknown not found in cache"):
            manager.get_manager_summary("Unknown")

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_filters_by_year_when_provided(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test filters data by year when year parameter provided."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_manager_summary("Tommy", year="2024")

        # Should use yearly data instead of all-time
        assert result["manager_name"] == "Tommy"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_year(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for year not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Year 2099 not found"):
            manager.get_manager_summary("Tommy", year="2099")


class TestGetManagerYearlyData:
    """Test get_manager_yearly_data method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_yearly_data_with_weekly_scores(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test returns yearly data including weekly scores."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_manager_yearly_data("Tommy", "2024")

        assert result["manager_name"] == "Tommy"
        assert result["year"] == "2024"
        assert "matchup_data" in result
        assert "weekly_scores" in result["matchup_data"]["overall"]
        assert len(result["matchup_data"]["overall"]["weekly_scores"]) == 2  # weeks 1 and 2

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_includes_transactions_by_week(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test includes transaction data organized by week."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_manager_yearly_data("Tommy", "2024")

        assert "transactions" in result
        assert "by_week" in result["transactions"]["trades"]
        assert "by_week" in result["transactions"]["adds"]
        assert "by_week" in result["transactions"]["drops"]

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_manager_or_year(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for invalid manager or year."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Manager Unknown not found"):
            manager.get_manager_yearly_data("Unknown", "2024")

        with pytest.raises(ValueError, match="Year 2099 not found"):
            manager.get_manager_yearly_data("Tommy", "2099")


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_head_to_head_stats(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test returns head-to-head stats between two managers."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_head_to_head("Tommy", "Mike")

        assert "manager_1" in result
        assert "manager_2" in result
        assert result["manager_1"]["name"] == "Tommy"
        assert result["manager_2"]["name"] == "Mike"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_managers(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for managers not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Manager Unknown not found"):
            manager.get_head_to_head("Tommy", "Unknown")


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_all_transactions_by_default(self, mock_load_cache, mock_load_player_ids,
                                                mock_manager_cache, mock_transaction_id_cache):
        """Test returns all transaction types when no filter specified."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache
        manager._transaction_id_cache = mock_transaction_id_cache

        result = manager.get_manager_transactions("Tommy")

        assert result["manager_name"] == "Tommy"
        assert result["total_count"] >= 0
        assert "transactions" in result

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_filters_by_transaction_type(self, mock_load_cache, mock_load_player_ids,
                                        mock_manager_cache, mock_transaction_id_cache):
        """Test filters transactions by type when specified."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache
        manager._transaction_id_cache = mock_transaction_id_cache

        result = manager.get_manager_transactions("Tommy", transaction_type="trade")

        # All transactions should be trades
        for tx in result["transactions"]:
            assert tx["type"] == "trade"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_applies_pagination(self, mock_load_cache, mock_load_player_ids,
                                mock_manager_cache, mock_transaction_id_cache):
        """Test applies limit and offset for pagination."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache
        manager._transaction_id_cache = mock_transaction_id_cache

        result = manager.get_manager_transactions("Tommy", limit=1, offset=0)

        # Should return at most 1 transaction
        assert len(result["transactions"]) <= 1

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_manager(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for manager not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Manager Unknown not found"):
            manager.get_manager_transactions("Unknown")


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_returns_awards_and_achievements(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test returns awards and achievements for a manager."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        result = manager.get_manager_awards("Tommy")

        assert result["manager_name"] == "Tommy"
        assert "awards" in result
        assert "avatar_urls" in result

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_raises_error_for_invalid_manager(self, mock_load_cache, mock_load_player_ids, mock_manager_cache):
        """Test raises ValueError for manager not in cache."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_manager_cache

        with pytest.raises(ValueError, match="Manager Unknown not found"):
            manager.get_manager_awards("Unknown")
