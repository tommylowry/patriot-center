"""
Unit tests for data_exporter module.

Tests the DataExporter class which provides public API for manager data.
All tests mock underlying cache_queries functions.
"""
from unittest.mock import patch

import pytest


@pytest.fixture
def sample_manager_cache():
    """Create a sample cache for testing."""
    return {
        "Manager 1": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 10},
                        "losses": {"total": 5},
                        "ties": {"total": 1}
                    }
                },
                "transactions": {
                    "trades": {"total": 5},
                    "adds": {"total": 10},
                    "drops": {"total": 10}
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
                            "overall": {"wins": {"total": 1, "opponents": {}}}
                        },
                        "transactions": {
                            "trades": {"total": 1}
                        }
                    },
                    "weeks": {}
                },
                "2022": {"summary": {}, "weeks": {}}
            }
        },
        "Manager 2": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 5},
                        "losses": {"total": 10},
                        "ties": {"total": 1}
                    }
                },
                "transactions": {
                    "trades": {"total": 3},
                    "adds": {"total": 8},
                    "drops": {"total": 8}
                },
                "overall_data": {
                    "placement": {"2023": 5},
                    "playoff_appearances": ["2023"]
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {"wins": {"total": 1, "opponents": {}}}
                        },
                        "transactions": {
                            "trades": {"total": 1}
                        }
                    },
                    "weeks": {}
                }
            }
        }
    }


@pytest.fixture
def transaction_ids_cache():
    """Create a sample transaction ids cache."""
    return {}


@pytest.fixture
def valid_options_cache():
    """Create a sample valid options cache."""
    return {
        "2025": {
            "managers": ["Manager 1", "Manager 2"]
        }
    }


@pytest.fixture(autouse=True)
def patch_caches(sample_manager_cache, transaction_ids_cache, valid_options_cache):
    with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
         patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
         patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
        yield


@pytest.fixture
def data_exporter():
    """Create DataExporter instance with sample caches."""
    from patriot_center_backend.managers.data_exporter import DataExporter
    return DataExporter()


class TestDataExporterInit:
    """Test DataExporter initialization."""

    def test_init_creates_empty_image_cache(self):
        """Test that __init__ creates empty image URL cache."""
        from patriot_center_backend.managers.data_exporter import DataExporter
        exporter = DataExporter()

        assert exporter._image_urls == {}


class TestGetManagersList:
    """Test get_managers_list method."""

    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_active_managers_only(self, mock_image_url, mock_ranking, data_exporter):
        """Test getting only active managers."""
        mock_image_url.return_value = "http://example.com/manager.jpg"
        mock_ranking.return_value = {
            "values": {
                "win_percentage": 60.0,
                "average_points_for": 100.0,
                "average_points_against": 90.0,
                "average_points_differential": 10.0,
                "trades": 5,
                "playoffs": 2
            },
            "ranks": {
                "win_percentage": 1,
                "average_points_for": 1,
                "average_points_against": 2,
                "average_points_differential": 1,
                "trades": 1,
                "playoffs": 1,
                "is_active_manager": True,
                "worst": 10
            }
        }
        
        result = data_exporter.get_managers_list(active_only=True)

        assert "managers" in result
        assert len(result["managers"]) == 2
        assert all("name" in m for m in result["managers"])
        assert all("image_url" in m for m in result["managers"])

    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_all_managers(self, mock_image_url, mock_ranking, data_exporter):
        """Test getting all managers including inactive."""
        mock_image_url.return_value = "http://example.com/manager.jpg"
        mock_ranking.return_value = {
            "values": {
                "win_percentage": 60.0,
                "average_points_for": 100.0,
                "average_points_against": 90.0,
                "average_points_differential": 10.0,
                "trades": 5,
                "playoffs": 2
            },
            "ranks": {
                "win_percentage": 1,
                "average_points_for": 1,
                "average_points_against": 2,
                "average_points_differential": 1,
                "trades": 1,
                "playoffs": 1,
                "is_active_manager": True,
                "worst": 10
            }
        }

        result = data_exporter.get_managers_list(active_only=False)

        assert "managers" in result
        # Should get all managers from cache keys
        assert len(result["managers"]) == 2

    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_managers_list_sorted_by_weight(self, mock_image_url, mock_ranking, data_exporter):
        """Test that managers are sorted by weight (best first)."""
        mock_image_url.return_value = "http://example.com/manager.jpg"

        def ranking_side_effect(manager, manager_summary_usage, active_only):
            # Manager 1 should have better stats
            if manager == "Manager 1":
                return {
                    "values": {
                        "win_percentage": 62.5,
                        "average_points_for": 100.0,
                        "average_points_against": 90.0,
                        "average_points_differential": 10.0,
                        "trades": 5,
                        "playoffs": 2
                    },
                    "ranks": {
                        "win_percentage": 1, "average_points_for": 1,
                        "average_points_against": 2, "average_points_differential": 1,
                        "trades": 1, "playoffs": 1,
                        "is_active_manager": True, "worst": 10
                    }
                }
            else:
                return {
                    "values": {
                        "win_percentage": 31.2,
                        "average_points_for": 90.0,
                        "average_points_against": 100.0,
                        "average_points_differential": -10.0,
                        "trades": 3,
                        "playoffs": 1
                    },
                    "ranks": {
                        "win_percentage": 2, "average_points_for": 2,
                        "average_points_against": 1, "average_points_differential": 2,
                        "trades": 2, "playoffs": 2,
                        "is_active_manager": True, "worst": 10
                    }
                }

        mock_ranking.side_effect = ranking_side_effect

        result = data_exporter.get_managers_list(active_only=True)

        # Manager 1 should be first (better record)
        assert result["managers"][0]["name"] == "Manager 1"


class TestGetManagerSummary:
    """Test get_manager_summary method."""

    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_overall_data_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_transaction_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_matchup_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_manager_summary_all_time(self, mock_image, mock_matchup, mock_trans,
                                          mock_overall, mock_ranking, mock_awards,
                                          mock_score_awards, mock_h2h, data_exporter):
        """Test getting manager summary for all-time stats."""
        mock_image.return_value = "http://example.com/manager.jpg"
        mock_matchup.return_value = {"overall": {"wins": 10}}
        mock_trans.return_value = {"trades": {"total": 5}}
        mock_overall.return_value = {"placements": [], "playoff_appearances": 2}
        mock_ranking.return_value = {"ranks": {}, "values": {}}
        mock_awards.return_value = {}
        mock_score_awards.return_value = {}
        mock_h2h.return_value = {}

        result = data_exporter.get_manager_summary("Manager 1")

        assert result["manager_name"] == "Manager 1"
        assert "image_url" in result
        assert "matchup_data" in result
        assert "transactions" in result
        assert "overall_data" in result
        assert "rankings" in result
        assert "head_to_head" in result

    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_overall_data_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_transaction_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_matchup_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_manager_summary_single_year(self, mock_image, mock_matchup, mock_trans,
                                             mock_overall, mock_ranking, mock_awards,
                                             mock_score_awards, mock_h2h, data_exporter):
        """Test getting manager summary for specific year."""
        mock_image.return_value = "http://example.com/manager.jpg"
        mock_matchup.return_value = {"overall": {"wins": 6}}
        mock_trans.return_value = {"trades": {"total": 2}}
        mock_overall.return_value = {"placements": [], "playoff_appearances": 1}
        mock_ranking.return_value = {"ranks": {}, "values": {}}
        mock_awards.return_value = {}
        mock_score_awards.return_value = {}
        mock_h2h.return_value = {}

        result = data_exporter.get_manager_summary("Manager 1", year="2023")

        assert result["manager_name"] == "Manager 1"
        # Verify year was passed to underlying functions
        mock_matchup.assert_called_once()
        assert mock_matchup.call_args[1]["year"] == "2023"


class TestGetHeadToHead:
    """Test get_head_to_head method."""

    @patch('patriot_center_backend.managers.data_exporter.get_trade_history_between_two_managers')
    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_overall_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_h2h_all_time(self, mock_image, mock_h2h_details, mock_h2h_overall,
                              mock_trades, data_exporter):
        """Test getting H2H stats for all-time."""
        mock_image.side_effect = lambda m, *args: f"http://example.com/{m}.jpg"
        mock_h2h_details.return_value = {"wins": 7, "losses": 3}
        mock_h2h_overall.return_value = {
            "manager_1_wins": 7,
            "manager_2_wins": 3,
            "ties": 1
        }
        mock_trades.return_value = []

        result = data_exporter.get_head_to_head("Manager 1", "Manager 2")

        assert result["manager_1"]["name"] == "Manager 1"
        assert result["manager_2"]["name"] == "Manager 2"
        assert "overall" in result
        assert "matchup_history" in result
        assert "trades_between" in result

    @patch('patriot_center_backend.managers.data_exporter.get_trade_history_between_two_managers')
    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_overall_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_head_to_head_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_h2h_single_year(self, mock_image, mock_h2h_details, mock_h2h_overall,
                                 mock_trades, data_exporter):
        """Test getting H2H stats for specific year."""
        mock_image.side_effect = lambda m, *args: f"http://example.com/{m}.jpg"
        mock_h2h_details.return_value = {"wins": 2, "losses": 1}
        mock_h2h_overall.return_value = {
            "manager_1_wins": 2,
            "manager_2_wins": 1,
            "ties": 0
        }
        mock_trades.return_value = []

        result = data_exporter.get_head_to_head("Manager 1", "Manager 2", year="2023")

        # Verify year was passed
        assert mock_h2h_overall.call_args[1]["year"] == "2023"


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_all_time(self, mock_image_url, data_exporter):
        """Test getting all-time transaction details."""
        mock_image_url.return_value = {"name": "Manager 1", "image_url": "http://example.com/manager1.jpg"}

        result = data_exporter.get_manager_transactions("Manager 1")

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result
        assert isinstance(result["transactions"], list)

    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_single_year(self, mock_image_url, data_exporter):
        """Test getting transaction details for specific year."""
        mock_image_url.return_value = {"name": "Manager 1", "image_url": "http://example.com/manager1.jpg"}

        result = data_exporter.get_manager_transactions("Manager 1", year="2023")

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result

    @patch('patriot_center_backend.managers.data_exporter.get_trade_card')
    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_with_trades(self, mock_image_url, mock_trade_card,
                                          sample_manager_cache, transaction_ids_cache,
                                          valid_options_cache):
        """Test get_manager_transactions processes trade transactions."""
        # Setup cache with trade transaction IDs
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "trades": {
                        "transaction_ids": ["trade1", "trade2"]
                    }
                }
            }
        }

        mock_image_url.return_value = {"name": "Manager 1", "image_url": "http://example.com/manager1.jpg"}
        mock_trade_card.return_value = {
            "year": "2023",
            "week": "1",
            "managers_involved": ["Manager 1", "Manager 2"]
        }

        with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
             patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.data_exporter import DataExporter
            get_trans_w_trades_exporter = DataExporter()
            result = get_trans_w_trades_exporter.get_manager_transactions("Manager 1", year="2023")

        # Should have processed 2 trades
        assert result["total_count"] == 2
        trades = [t for t in result["transactions"] if t["type"] == "trade"]
        assert len(trades) == 2

    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_with_adds(self, mock_image_url, sample_manager_cache,
                                        transaction_ids_cache, valid_options_cache):
        """Test get_manager_transactions processes add transactions."""
        # Setup cache with add transaction
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {
                        "transaction_ids": ["add1"]
                    }
                }
            }
        }

        transaction_ids_cache["add1"] = {
            "types": ["add"],
            "add": "Player A",
            "faab_spent": 50
        }

        mock_image_url.return_value = {"name": "Player A", "image_url": "http://example.com/player.jpg"}

        with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
             patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.data_exporter import DataExporter
            get_trans_w_adds_exporter = DataExporter()
            result = get_trans_w_adds_exporter.get_manager_transactions("Manager 1", year="2023")

        # Should have 1 add transaction
        adds = [t for t in result["transactions"] if t["type"] == "add"]
        assert len(adds) == 1
        assert adds[0]["faab_spent"] == 50

    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_with_drops(self, mock_image_url, sample_manager_cache,
                                         transaction_ids_cache, valid_options_cache):
        """Test get_manager_transactions processes drop transactions."""
        # Setup cache with drop transaction
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "drops": {
                        "transaction_ids": ["drop1"]
                    }
                }
            }
        }

        transaction_ids_cache["drop1"] = {
            "types": ["drop"],
            "drop": "Player B"
        }

        mock_image_url.return_value = {"name": "Player B", "image_url": "http://example.com/player.jpg"}

        with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
             patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.data_exporter import DataExporter
            get_trans_w_drops_exporter = DataExporter()
            result = get_trans_w_drops_exporter.get_manager_transactions("Manager 1", year="2023")

        # Should have 1 drop transaction
        drops = [t for t in result["transactions"] if t["type"] == "drop"]
        assert len(drops) == 1
        assert drops[0]["player"]["name"] == "Player B"

    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_transactions_with_add_and_drop(self, mock_image_url, sample_manager_cache,
                                                transaction_ids_cache, valid_options_cache):
        """Test get_manager_transactions processes add_and_drop transactions."""
        # Setup cache with add_and_drop transaction
        sample_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {
                        "transaction_ids": ["add_drop1"]
                    }
                }
            }
        }

        transaction_ids_cache["add_drop1"] = {
            "types": ["add", "drop"],
            "add": "Player A",
            "drop": "Player B",
            "faab_spent": 30
        }

        def image_url_side_effect(player, *args, **kwargs):
            if player == "Player A":
                return {"name": "Player A", "image_url": "http://example.com/playerA.jpg"}
            elif player == "Player B":
                return {"name": "Player B", "image_url": "http://example.com/playerB.jpg"}
            else:
                return {"name": "Manager 1", "image_url": "http://example.com/manager1.jpg"}

        mock_image_url.side_effect = image_url_side_effect

        with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
             patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.data_exporter import DataExporter
            get_trans_w_adds_and_drop_exporter = DataExporter()
            result = get_trans_w_adds_and_drop_exporter.get_manager_transactions("Manager 1", year="2023")

        # Should have 1 add_and_drop transaction
        add_drops = [t for t in result["transactions"] if t["type"] == "add_and_drop"]
        assert len(add_drops) == 1
        assert add_drops[0]["added_player"]["name"] == "Player A"
        assert add_drops[0]["dropped_player"]["name"] == "Player B"
        assert add_drops[0]["faab_spent"] == 30


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    @patch('patriot_center_backend.managers.data_exporter.get_image_url')
    def test_get_awards(self, mock_image_url, mock_current_manager_url, mock_awards, mock_score_awards, data_exporter):
        """Test getting manager awards."""
        mock_image_url.return_value = "https://sleepercdn.com/avatars/acb123"
        mock_current_manager_url.return_value = {
            "image_url": "https://sleepercdn.com/avatars/abc123",
            "name": "Manager 1"
        }
        mock_awards.return_value = {
            "first_place": 1,
            "second_place": 0,
            "third_place": 1,
            "playoff_appearances": 2
        }
        mock_score_awards.return_value = {
            "highest_weekly_score": {},
            "lowest_weekly_score": {},
            "biggest_blowout_win": {},
            "biggest_blowout_loss": {}
        }

        result = data_exporter.get_manager_awards("Manager 1")

        # Should have the correct structure
        assert "manager" in result
        assert "image_url" in result
        assert "awards" in result
        # Awards should be combined
        assert "first_place" in result["awards"]
        assert "highest_weekly_score" in result["awards"]
        assert mock_awards.called
        assert mock_score_awards.called


class TestCacheImmutability:
    """Test that DataExporter doesn't modify caches."""

    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_managers_list_immutable(self, mock_image, mock_ranking, sample_manager_cache,
                                         transaction_ids_cache, valid_options_cache):
        """Test that get_managers_list doesn't modify cache."""
        from copy import deepcopy

        mock_image.return_value = "http://example.com/manager.jpg"
        mock_ranking.return_value = {
            "values": {"win_percentage": 60.0, "average_points_for": 100.0,
                      "average_points_against": 90.0, "average_points_differential": 10.0,
                      "trades": 5, "playoffs": 2},
            "ranks": {"win_percentage": 1, "average_points_for": 1,
                     "average_points_against": 2, "average_points_differential": 1,
                     "trades": 1, "playoffs": 1,
                     "is_active_manager": True, "worst": 10}
        }

        original = deepcopy(sample_manager_cache)

        with patch('patriot_center_backend.managers.data_exporter.MANAGER_CACHE', sample_manager_cache), \
             patch('patriot_center_backend.managers.data_exporter.TRANSACTION_IDS_CACHE', transaction_ids_cache), \
             patch('patriot_center_backend.managers.data_exporter.VALID_OPTIONS_CACHE', valid_options_cache):
            from patriot_center_backend.managers.data_exporter import DataExporter
            exporter = DataExporter()
            exporter.get_managers_list(active_only=True)

        assert sample_manager_cache == original
