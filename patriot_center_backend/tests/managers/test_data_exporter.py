"""
Unit tests for data_exporter module.

Tests the DataExporter class which provides public API for manager data.
All tests mock underlying cache_queries functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from patriot_center_backend.managers.data_exporter import DataExporter


@pytest.fixture
def sample_caches():
    """Create sample caches for testing."""
    cache = {
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

    transaction_ids_cache = {}
    players_cache = {}
    player_ids = {}
    valid_options_cache = {
        "2025": {
            "managers": ["Manager 1", "Manager 2"]
        }
    }
    starters_cache = {}

    return {
        "cache": cache,
        "transaction_ids_cache": transaction_ids_cache,
        "players_cache": players_cache,
        "player_ids": player_ids,
        "valid_options_cache": valid_options_cache,
        "starters_cache": starters_cache
    }


@pytest.fixture
def data_exporter(sample_caches):
    """Create DataExporter instance with sample caches."""
    return DataExporter(
        cache=sample_caches["cache"],
        transaction_ids_cache=sample_caches["transaction_ids_cache"],
        players_cache=sample_caches["players_cache"],
        valid_options_cache=sample_caches["valid_options_cache"],
        starters_cache=sample_caches["starters_cache"],
        player_ids=sample_caches["player_ids"]
    )


class TestDataExporterInit:
    """Test DataExporter initialization."""

    def test_init_stores_caches(self, sample_caches):
        """Test that __init__ stores all caches as instance variables."""
        exporter = DataExporter(
            cache=sample_caches["cache"],
            transaction_ids_cache=sample_caches["transaction_ids_cache"],
            players_cache=sample_caches["players_cache"],
            valid_options_cache=sample_caches["valid_options_cache"],
            starters_cache=sample_caches["starters_cache"],
            player_ids=sample_caches["player_ids"]
        )

        assert exporter._cache == sample_caches["cache"]
        assert exporter._transaction_ids_cache == sample_caches["transaction_ids_cache"]
        assert exporter._players_cache == sample_caches["players_cache"]
        assert exporter._player_ids == sample_caches["player_ids"]
        assert exporter._valid_options_cache == sample_caches["valid_options_cache"]
        assert exporter._starters_cache == sample_caches["starters_cache"]

    def test_init_creates_empty_image_cache(self, sample_caches):
        """Test that __init__ creates empty image URL cache."""
        exporter = DataExporter(
            cache=sample_caches["cache"],
            transaction_ids_cache=sample_caches["transaction_ids_cache"],
            players_cache=sample_caches["players_cache"],
            valid_options_cache=sample_caches["valid_options_cache"],
            starters_cache=sample_caches["starters_cache"],
            player_ids=sample_caches["player_ids"]
        )

        assert exporter._image_urls_cache == {}


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

        def ranking_side_effect(cache, manager, valid_options, manager_summary_usage, active_only):
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

    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_overall_data_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_transaction_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_matchup_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_manager_summary_all_time(self, mock_image, mock_matchup, mock_trans,
                                          mock_overall, mock_ranking, mock_awards,
                                          mock_score_awards, data_exporter):
        """Test getting manager summary for all-time stats."""
        mock_image.return_value = "http://example.com/manager.jpg"
        mock_matchup.return_value = {"overall": {"wins": 10}}
        mock_trans.return_value = {"trades": {"total": 5}}
        mock_overall.return_value = {"placements": [], "playoff_appearances": 2}
        mock_ranking.return_value = {"ranks": {}, "values": {}}
        mock_awards.return_value = {}
        mock_score_awards.return_value = {}

        result = data_exporter.get_manager_summary("Manager 1")

        assert result["manager_name"] == "Manager 1"
        assert "image_url" in result
        assert "matchup_data" in result
        assert "transactions" in result
        assert "overall_data" in result
        assert "rankings" in result
        assert "head_to_head" in result

    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_ranking_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_overall_data_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_transaction_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_matchup_details_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_current_manager_image_url')
    def test_get_manager_summary_single_year(self, mock_image, mock_matchup, mock_trans,
                                             mock_overall, mock_ranking, mock_awards,
                                             mock_score_awards, data_exporter):
        """Test getting manager summary for specific year."""
        mock_image.return_value = "http://example.com/manager.jpg"
        mock_matchup.return_value = {"overall": {"wins": 6}}
        mock_trans.return_value = {"trades": {"total": 2}}
        mock_overall.return_value = {"placements": [], "playoff_appearances": 1}
        mock_ranking.return_value = {"ranks": {}, "values": {}}
        mock_awards.return_value = {}
        mock_score_awards.return_value = {}

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


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    @patch('patriot_center_backend.managers.data_exporter.get_manager_score_awards_from_cache')
    @patch('patriot_center_backend.managers.data_exporter.get_manager_awards_from_cache')
    def test_get_awards(self, mock_awards, mock_score_awards, data_exporter):
        """Test getting manager awards."""
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
    def test_get_managers_list_immutable(self, mock_image, mock_ranking, sample_caches):
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

        original = deepcopy(sample_caches["cache"])

        exporter = DataExporter(
            cache=sample_caches["cache"],
            transaction_ids_cache=sample_caches["transaction_ids_cache"],
            players_cache=sample_caches["players_cache"],
            valid_options_cache=sample_caches["valid_options_cache"],
            starters_cache=sample_caches["starters_cache"],
            player_ids=sample_caches["player_ids"]
        )

        exporter.get_managers_list(active_only=True)

        assert sample_caches["cache"] == original
