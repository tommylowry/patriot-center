"""Unit tests for data_exporter module."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.data_exporter import DataExporter


@pytest.fixture
def mock_manager_cache() -> dict[str, Any]:
    """Create a sample cache for testing.

    Returns:
        Sample manager cache
    """
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
def mock_valid_options_cache() -> dict[str, Any]:
    """Create a sample valid options cache.

    Returns:
        Sample valid options cache
    """
    return {
        "2025": {
            "managers": ["Manager 1", "Manager 2"]
        }
    }


@pytest.fixture
def mock_data_exporter() -> DataExporter:
    """Create a mock data_exporter object.

    Returns:
        Mock DataExporter object
    """
    return DataExporter()


class TestDataExporterInit:
    """Test DataExporter initialization."""

    def test_init_creates_empty_image_cache(self):
        """Test that __init__ creates empty image URL cache."""
        exporter = DataExporter()

        assert exporter._image_urls == {}


class TestGetManagersList:
    """Test get_managers_list method."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_manager_cache: dict[str, Any],
        mock_valid_options_cache: dict[str, Any]
    ):
        """Setup common mocks for all tests.

        Args:
            mock_manager_cache (dict[str, Any]): Sample manager cache
            mock_valid_options_cache (dict[str, Any]): Sample valid
                options cache

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,

            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_valid_options_cache'
            ) as mock_get_valid_options_cache,

            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_ranking_details_from_cache'
            ) as mock_get_ranking_details,

            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_current_manager_image_url'
            ) as mock_get_current_mgr_url,

            patch(
                'patriot_center_backend.managers.data_exporter'
                '.LEAGUE_IDS',
                {2025: "mock_league_id"}
            ),
        ):

            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_valid_options_cache = mock_valid_options_cache
            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            self.mock_get_ranking_details = mock_get_ranking_details
            self.mock_get_ranking_details.return_value = {}

            self.mock_get_current_mgr_url = mock_get_current_mgr_url
            self.mock_get_current_mgr_url.return_value = (
                "http://example.com/manager.jpg"
            )

            yield

    def test_get_active_managers_only(self, mock_data_exporter: DataExporter):
        """Test getting only active managers.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_ranking_details.return_value = {
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

        result = mock_data_exporter.get_managers_list(active_only=True)

        assert "managers" in result
        assert len(result["managers"]) == 2
        assert all("name" in m for m in result["managers"])
        assert all("image_url" in m for m in result["managers"])

    def test_get_all_managers(self, mock_data_exporter: DataExporter):
        """Test getting all managers including inactive.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_ranking_details.return_value = {
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

        result = mock_data_exporter.get_managers_list(active_only=False)

        assert "managers" in result
        # Should get all managers from cache keys
        assert len(result["managers"]) == 2

    def test_get_managers_list_immutable(
        self, mock_data_exporter: DataExporter
    ):
        """Test that get_managers_list doesn't modify cache.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_ranking_details.return_value = {
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

        original = deepcopy(self.mock_manager_cache)

        mock_data_exporter.get_managers_list(active_only=True)

        assert self.mock_manager_cache == original


    def test_managers_list_sorted_by_weight(
        self, mock_data_exporter: DataExporter
    ):
        """Test that managers are sorted by weight (best first).

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
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
                        "win_percentage": 2,
                        "average_points_for": 2,
                        "average_points_against": 1,
                        "average_points_differential": 2,
                        "trades": 2,
                        "playoffs": 2,
                        "is_active_manager": True,
                        "worst": 10
                    }
                }

        self.mock_get_ranking_details.side_effect = ranking_side_effect

        result = mock_data_exporter.get_managers_list(active_only=True)

        # Manager 1 should be first (better record)
        assert result["managers"][0]["name"] == "Manager 1"


class TestGetManagerSummary:
    """Test get_manager_summary method."""


    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        Args:
            mock_manager_cache (dict[str, Any]): Mock manager cache

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_current_manager_image_url'
            ) as mock_get_current_mgr_url,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_matchup_details_from_cache'
            ) as mock_get_matchup,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_transaction_details_from_cache'
            ) as mock_get_trans,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_overall_data_details_from_cache',
            ) as mock_get_overall,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_ranking_details_from_cache',
            ) as mock_ranking,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_head_to_head_details_from_cache',
            ) as mock_get_h2h,
        ):

            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_get_current_mgr_url = mock_get_current_mgr_url
            self.mock_get_current_mgr_url.return_value = (
                "http://example.com/manager.jpg"
            )

            self.mock_get_matchup = mock_get_matchup
            self.mock_get_matchup.return_value = {}

            self.mock_get_trans = mock_get_trans
            self.mock_get_trans.return_value = {}

            self.mock_get_overall = mock_get_overall
            self.mock_get_overall.return_value = {}

            self.mock_ranking = mock_ranking
            self.mock_ranking.return_value = {}

            self.mock_get_h2h = mock_get_h2h
            self.mock_get_h2h.return_value = {}

            yield

    def test_get_manager_summary_all_time(
        self, mock_data_exporter: DataExporter
    ):
        """Test getting manager summary for all-time stats.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_current_mgr_url.return_value = (
            "http://example.com/manager.jpg"
        )
        self.mock_get_matchup.return_value = {"overall": {"wins": 10}}
        self.mock_get_trans.return_value = {"trades": {"total": 5}}
        self.mock_get_overall.return_value = {
            "placements": [],
            "playoff_appearances": 2
        }
        self.mock_ranking.return_value = {"ranks": {}, "values": {}}
        self.mock_get_h2h.return_value = {}

        result = mock_data_exporter.get_manager_summary("Manager 1")

        assert result["manager_name"] == "Manager 1"
        assert "image_url" in result
        assert "matchup_data" in result
        assert "transactions" in result
        assert "overall_data" in result
        assert "rankings" in result
        assert "head_to_head" in result

    def test_get_manager_summary_single_year(
        self, mock_data_exporter: DataExporter
    ):
        """Test getting manager summary for specific year.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_current_mgr_url.return_value = (
            "http://example.com/manager.jpg"
        )
        self.mock_get_matchup.return_value = {"overall": {"wins": 6}}
        self.mock_get_trans.return_value = {"trades": {"total": 2}}
        self.mock_get_overall.return_value = {
            "placements": [],
            "playoff_appearances": 1
        }
        self.mock_ranking.return_value = {"ranks": {}, "values": {}}
        self.mock_get_h2h.return_value = {}

        result = mock_data_exporter.get_manager_summary(
            "Manager 1", year="2023"
        )

        assert result["manager_name"] == "Manager 1"

        # Verify year was passed to underlying functions
        self.mock_get_matchup.assert_called_once()
        assert self.mock_get_matchup.call_args[1]["year"] == "2023"


class TestGetHeadToHead:
    """Test get_head_to_head method."""


    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        Args:
            mock_manager_cache (dict[str, Any]): Mock manager cache

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_current_manager_image_url'
            ) as mock_get_current_mgr_url,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_head_to_head_overall_from_cache'
            ) as mock_get_h2h,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_trade_history_between_two_managers'
            ) as mock_get_trade_history,
        ):

            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_get_current_mgr_url = mock_get_current_mgr_url
            self.mock_get_current_mgr_url.return_value = (
                "http://example.com/manager.jpg"
            )

            self.mock_get_h2h = mock_get_h2h
            self.mock_get_h2h.return_value = {}

            self.mock_get_trade_history = mock_get_trade_history
            self.mock_get_trade_history.return_value = []

            yield

    def test_get_h2h_all_time(self, mock_data_exporter: DataExporter):
        """Test getting H2H stats for all-time.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_current_mgr_url.side_effect = (
            lambda m,
            *args: f"http://example.com/{m}.jpg"
        )

        self.mock_get_h2h.side_effect = (
            lambda *args,
            list_all_matchups=False,
            **kwargs: (

                # if list_all_matchups is passed as a keyword argument (kwarg)
                {"manager_1_wins": 7, "manager_2_wins": 3, "ties": 1}
                if list_all_matchups

                # if list_all_matchups is NOT passed as a keyword argument
                else {"wins": 7, "losses": 3}
            )
        )

        result = mock_data_exporter.get_head_to_head("Manager 1", "Manager 2")

        assert result["manager_1"]["name"] == "Manager 1"
        assert result["manager_2"]["name"] == "Manager 2"
        assert "overall" in result
        assert "matchup_history" in result
        assert "trades_between" in result

    def test_get_h2h_single_year(self, mock_data_exporter: DataExporter):
        """Test getting H2H stats for specific year.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_current_mgr_url.side_effect = (
            lambda m,
            *args: f"http://example.com/{m}.jpg"
        )

        self.mock_get_h2h.side_effect = (
            lambda *args,
            list_all_matchups=False,
            **kwargs: (
                {"manager_1_wins": 2, "manager_2_wins": 1, "ties": 0}
                if list_all_matchups
                else {"wins": 2, "losses": 1}
            )
        )

        mock_data_exporter.get_head_to_head(
            "Manager 1", "Manager 2", year="2023"
        )

        # Verify year was passed
        assert self.mock_get_h2h.call_args[1]["year"] == "2023"


class TestGetManagerTransactions:
    """Test get_manager_transactions method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        Args:
            mock_manager_cache (dict[str, Any]): Mock manager cache

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_transaction_ids_cache'
            ) as mock_get_trans_ids,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_image_url'
            ) as mock_get_image_url,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_trade_card'
            ) as mock_get_trade_card,
        ):

            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_trans_ids_cache = {}
            self.mock_get_trans_ids = mock_get_trans_ids
            self.mock_get_trans_ids.return_value = self.mock_trans_ids_cache

            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.return_value = {
                "name": "item", "image_url": "http://example.com/item.jpg"
            }

            self.mock_get_trade_card = mock_get_trade_card
            self.mock_get_trade_card.return_value = {}

            yield

    def test_get_transactions_all_time(self, mock_data_exporter: DataExporter):
        """Test getting all-time transaction details.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_image_url.return_value = {
            "name": "Manager 1", "image_url": "http://example.com/manager1.jpg"
        }

        result = mock_data_exporter.get_manager_transactions("Manager 1")

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result
        assert isinstance(result["transactions"], list)

    def test_get_transactions_single_year(
        self, mock_data_exporter: DataExporter
    ):
        """Test getting transaction details for specific year.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_image_url.return_value = {
            "name": "Manager 1", "image_url": "http://example.com/manager1.jpg"
        }

        result = mock_data_exporter.get_manager_transactions(
            "Manager 1", year="2023"
        )

        assert "name" in result
        assert "total_count" in result
        assert "transactions" in result

    def test_get_transactions_with_trades(
        self, mock_data_exporter: DataExporter
    ):
        """Test get_manager_transactions processes trade transactions.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        # Setup cache with trade transaction IDs
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "trades": {
                        "transaction_ids": ["trade1", "trade2"]
                    }
                }
            }
        }
        self.mock_get_image_url.return_value = {
            "name": "Manager 1", "image_url": "http://example.com/manager1.jpg"
        }
        self.mock_get_trade_card.return_value = {
            "year": "2023",
            "week": "1",
            "managers_involved": ["Manager 1", "Manager 2"]
        }

        result = mock_data_exporter.get_manager_transactions(
            "Manager 1", year="2023"
        )

        # Should have processed 2 trades
        assert result["total_count"] == 2
        trades = [t for t in result["transactions"] if t["type"] == "trade"]
        assert len(trades) == 2

    def test_get_transactions_with_adds(self, mock_data_exporter: DataExporter):
        """Test get_manager_transactions processes add transactions.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        # Setup cache with add transaction
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {
                        "transaction_ids": ["add1"]
                    }
                }
            }
        }
        self.mock_trans_ids_cache["add1"] = {
            "types": ["add"],
            "add": "Player A",
            "faab_spent": 50
        }
        self.mock_get_image_url.return_value = {
            "name": "Player A", "image_url": "http://example.com/player.jpg"
        }

        result = mock_data_exporter.get_manager_transactions(
            "Manager 1", year="2023"
        )

        # Should have 1 add transaction
        adds = [t for t in result["transactions"] if t["type"] == "add"]
        assert len(adds) == 1
        assert adds[0]["faab_spent"] == 50

    def test_get_transactions_with_drops(
        self, mock_data_exporter: DataExporter
    ):
        """Test get_manager_transactions processes drop transactions.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        # Setup cache with drop transaction
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "drops": {
                        "transaction_ids": ["drop1"]
                    }
                }
            }
        }
        self.mock_trans_ids_cache["drop1"] = {
            "types": ["drop"],
            "drop": "Player B"
        }
        self.mock_get_image_url.return_value = {
            "name": "Player B", "image_url": "http://example.com/player.jpg"
        }

        result = mock_data_exporter.get_manager_transactions(
            "Manager 1", year="2023"
        )

        # Should have 1 drop transaction
        drops = [t for t in result["transactions"] if t["type"] == "drop"]
        assert len(drops) == 1
        assert drops[0]["player"]["name"] == "Player B"

    def test_get_transactions_with_add_and_drop(
        self, mock_data_exporter: DataExporter
    ):
        """Test get_manager_transactions processes add_and_drop transactions.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        # Setup cache with add_and_drop transaction
        self.mock_manager_cache["Manager 1"]["years"]["2023"]["weeks"] = {
            "1": {
                "transactions": {
                    "adds": {
                        "transaction_ids": ["add_drop1"]
                    }
                }
            }
        }
        self.mock_trans_ids_cache["add_drop1"] = {
            "types": ["add", "drop"],
            "add": "Player A",
            "drop": "Player B",
            "faab_spent": 30
        }
        def image_url_side_effect(player, *args, **kwargs):
            if player == "Player A":
                return {
                    "name": "Player A",
                    "image_url": "http://example.com/playerA.jpg"
                }
            elif player == "Player B":
                return {
                    "name": "Player B",
                    "image_url": "http://example.com/playerB.jpg"
                }
            else:
                return {
                    "name": "Manager 1",
                    "image_url": "http://example.com/manager1.jpg"
                }
        self.mock_get_image_url.side_effect = image_url_side_effect

        result = mock_data_exporter.get_manager_transactions(
            "Manager 1", year="2023"
        )

        # Should have 1 add_and_drop transaction
        add_drops = (
            [t for t in result["transactions"] if t["type"] == "add_and_drop"]
        )
        assert len(add_drops) == 1
        assert add_drops[0]["added_player"]["name"] == "Player A"
        assert add_drops[0]["dropped_player"]["name"] == "Player B"
        assert add_drops[0]["faab_spent"] == 30


class TestGetManagerAwards:
    """Test get_manager_awards method."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        Args:
            mock_manager_cache (dict[str, Any]): Mock manager cache

        Yields:
            None
        """
        with (
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.CACHE_MANAGER.get_manager_cache'
            ) as mock_get_manager_cache,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_image_url'
            ) as mock_get_image_url,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_current_manager_image_url'
            ) as mock_get_current_mgr_url,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_manager_awards_from_cache'
            ) as mock_get_manager_awards,
            patch(
                'patriot_center_backend.managers.data_exporter'
                '.get_manager_score_awards_from_cache'
            ) as mock_get_manager_score_awards,
        ):

            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.return_value = (
                "https://sleepercdn.com/avatars/acb123"
            )

            self.mock_get_current_mgr_url = mock_get_current_mgr_url
            self.mock_get_current_mgr_url.return_value = (
                "https://sleepercdn.com/avatars/acb123"
            )

            self.mock_get_manager_awards = mock_get_manager_awards
            self.mock_get_manager_awards.return_value = {}

            self.mock_get_manager_score_awards = mock_get_manager_score_awards
            self.mock_get_manager_score_awards.return_value = {}

            yield

    def test_get_awards(self, mock_data_exporter: DataExporter):
        """Test getting manager awards.

        Args:
            mock_data_exporter (DataExporter): Mock DataExporter object
        """
        self.mock_get_image_url.return_value = (
            "https://sleepercdn.com/avatars/acb123"
        )
        self.mock_get_current_mgr_url.return_value = {
            "image_url": "https://sleepercdn.com/avatars/abc123",
            "name": "Manager 1"
        }
        self.mock_get_manager_awards.return_value = {
            "first_place": 1,
            "second_place": 0,
            "third_place": 1,
            "playoff_appearances": 2
        }
        self.mock_get_manager_score_awards.return_value = {
            "highest_weekly_score": {},
            "lowest_weekly_score": {},
            "biggest_blowout_win": {},
            "biggest_blowout_loss": {}
        }

        result = mock_data_exporter.get_manager_awards("Manager 1")

        # Should have the correct structure
        assert "manager" in result
        assert "image_url" in result
        assert "awards" in result
        # Awards should be combined
        assert "first_place" in result["awards"]
        assert "highest_weekly_score" in result["awards"]
        assert self.mock_get_manager_awards.called
        assert self.mock_get_manager_score_awards.called
