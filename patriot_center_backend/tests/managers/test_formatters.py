"""
Unit tests for formatters module.

Tests formatting functions with both good and bad scenarios.
"""
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.formatters import get_season_state


class TestGetSeasonState:
    """Test get_season_state function."""

    @patch('patriot_center_backend.managers.formatters.fetch_sleeper_data')
    def test_regular_season(self, mock_fetch):
        """Test regular season detection."""
        week = "5"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        mock_fetch.assert_not_called()

    @patch('patriot_center_backend.managers.formatters.fetch_sleeper_data')
    def test_playoffs(self, mock_fetch):
        """Test playoff detection."""
        week = "15"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"
        mock_fetch.assert_not_called()

    @patch('patriot_center_backend.managers.formatters.fetch_sleeper_data')
    def test_playoffs_late_week(self, mock_fetch):
        """Test playoff detection in late weeks."""
        week = "17"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"

    @patch('patriot_center_backend.managers.formatters.fetch_sleeper_data')
    @patch('patriot_center_backend.managers.formatters.LEAGUE_IDS', {2023: "league123"})
    def test_fetch_playoff_week_from_api(self, mock_fetch):
        """Test fetching playoff_week_start from API when not provided."""
        mock_fetch.return_value = {
            "settings": {
                "playoff_week_start": 15
            }
        }

        week = "10"
        year = "2023"
        playoff_week_start = None

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        mock_fetch.assert_called_once_with("league/league123")

    def test_missing_week_raises_error(self):
        """Test that missing week raises ValueError."""
        week = None
        year = "2023"
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_empty_week_raises_error(self):
        """Test that empty week raises ValueError."""
        week = ""
        year = "2023"
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_missing_year_raises_error(self):
        """Test that missing year raises ValueError."""
        week = "5"
        year = None
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_empty_year_raises_error(self):
        """Test that empty year raises ValueError."""
        week = "5"
        year = ""
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    @patch('patriot_center_backend.managers.formatters.fetch_sleeper_data')
    def test_boundary_week_before_playoffs(self, mock_fetch):
        """Test week just before playoffs."""
        week = "14"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"


class TestGetTop3ScorersFromMatchupData:
    """Test get_top_3_scorers_from_matchup_data function."""

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_valid_matchup_data(self, mock_get_image_url):
        """Test with valid matchup data and starters."""
        # Return a NEW dict each time to avoid mutation issues
        mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg"
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        players_cache = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"},
            "Player C": {"player_id": "3"},
            "Player D": {"player_id": "4"},
            "Player E": {"player_id": "5"},
            "Player F": {"player_id": "6"}
        }

        player_ids = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"},
            "3": {"first_name": "Player", "last_name": "C"},
            "4": {"first_name": "Player", "last_name": "D"},
            "5": {"first_name": "Player", "last_name": "E"},
            "6": {"first_name": "Player", "last_name": "F"}
        }

        image_urls = {}

        starters_cache = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Player B": {"points": 18.0, "position": "RB"},
                        "Player C": {"points": 12.5, "position": "WR"},
                        "Total_Points": 56.0
                    },
                    "Manager 2": {
                        "Player D": {"points": 30.0, "position": "QB"},
                        "Player E": {"points": 15.0, "position": "RB"},
                        "Player F": {"points": 10.0, "position": "WR"},
                        "Total_Points": 55.0
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', players_cache), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', player_ids), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', starters_cache):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, image_urls)

        assert len(result["manager_1_top_3_scorers"]) == 3
        assert len(result["manager_2_top_3_scorers"]) == 3
        assert result["manager_1_top_3_scorers"][0]["score"] == 25.5
        assert result["manager_1_lowest_scorer"]["score"] == 12.5
        assert result["manager_2_top_3_scorers"][0]["score"] == 30.0
        assert result["manager_2_lowest_scorer"]["score"] == 10.0

    def test_missing_year_in_matchup_data(self):
        """Test with missing year in matchup_data."""
        matchup_data = {"week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', {}):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        assert result["manager_1_top_3_scorers"] == []
        assert result["manager_2_top_3_scorers"] == []
        assert result["manager_1_lowest_scorer"] == []
        assert result["manager_2_lowest_scorer"] == []

    def test_missing_week_in_matchup_data(self):
        """Test with missing week in matchup_data."""
        matchup_data = {"year": "2023"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', {}):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        assert result["manager_1_top_3_scorers"] == []
        assert result["manager_2_top_3_scorers"] == []

    def test_missing_manager_1_starters(self):
        """Test with manager_1 missing from starters_cache."""
        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        starters_cache = {
            "2023": {
                "1": {
                    "Manager 2": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Total_Points": 25.5
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', starters_cache):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        assert result["manager_1_top_3_scorers"] == []
        assert result["manager_2_top_3_scorers"] == []

    def test_missing_manager_2_starters(self):
        """Test with manager_2 missing from starters_cache."""
        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        starters_cache = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Total_Points": 25.5
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', {}), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', starters_cache):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        assert result["manager_1_top_3_scorers"] == []
        assert result["manager_2_top_3_scorers"] == []

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_fewer_than_3_players(self, mock_get_image_url):
        """Test with fewer than 3 starters."""
        # Return a NEW dict each time to avoid mutation issues
        mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg"
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        players_cache = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"}
        }

        player_ids = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"}
        }

        starters_cache = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Player B": {"points": 18.0, "position": "RB"},
                        "Total_Points": 43.5
                    },
                    "Manager 2": {
                        "Player A": {"points": 20.0, "position": "QB"},
                        "Total_Points": 20.0
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', players_cache), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', player_ids), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', starters_cache):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        # Should return only 2 players for manager_1
        assert len(result["manager_1_top_3_scorers"]) == 2
        # Should return only 1 player for manager_2
        assert len(result["manager_2_top_3_scorers"]) == 1

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_insertion_sort_ordering(self, mock_get_image_url):
        """Test that top scorers are properly sorted."""
        # Return a NEW dict each time to avoid mutation issues
        mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg"
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        players_cache = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"},
            "Player C": {"player_id": "3"},
            "Player D": {"player_id": "4"},
            "Player E": {"player_id": "5"}
        }

        player_ids = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"},
            "3": {"first_name": "Player", "last_name": "C"},
            "4": {"first_name": "Player", "last_name": "D"},
            "5": {"first_name": "Player", "last_name": "E"}
        }

        starters_cache = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 10.0, "position": "WR"},  # 4th
                        "Player B": {"points": 25.0, "position": "QB"},  # 1st
                        "Player C": {"points": 15.0, "position": "RB"},  # 3rd
                        "Player D": {"points": 20.0, "position": "TE"},  # 2nd
                        "Player E": {"points": 5.0, "position": "K"},    # 5th (lowest)
                        "Total_Points": 75.0
                    },
                    "Manager 2": {
                        "Player A": {"points": 20.0, "position": "QB"},
                        "Total_Points": 20.0
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.PLAYERS_CACHE', players_cache), \
             patch('patriot_center_backend.managers.formatters.PLAYER_IDS_CACHE', player_ids), \
             patch('patriot_center_backend.managers.formatters.STARTERS_CACHE', starters_cache):
            from patriot_center_backend.managers.formatters import (
                get_top_3_scorers_from_matchup_data,
            )
            result = get_top_3_scorers_from_matchup_data(matchup_data, manager_1, manager_2, {})

        # Verify top 3 are in descending order
        assert result["manager_1_top_3_scorers"][0]["score"] == 25.0  # Player B
        assert result["manager_1_top_3_scorers"][1]["score"] == 20.0  # Player D
        assert result["manager_1_top_3_scorers"][2]["score"] == 15.0  # Player C

        # Verify lowest scorer
        assert result["manager_1_lowest_scorer"]["score"] == 5.0  # Player E


class TestGetMatchupCard:
    """Test get_matchup_card function."""

    @patch('patriot_center_backend.managers.formatters.get_top_3_scorers_from_matchup_data')
    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_valid_matchup_card_win(self, mock_get_image_url, mock_get_top_3):
        """Test generating matchup card for a win."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"
        mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {}
        }

        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 120.5,
                                    "points_against": 100.0
                                }
                            }
                        }
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result["year"] == "2023"
        assert result["week"] == "1"
        assert result["manager_1_score"] == 120.5
        assert result["manager_2_score"] == 100.0
        assert result["winner"] == "Manager 1"

    @patch('patriot_center_backend.managers.formatters.get_top_3_scorers_from_matchup_data')
    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_valid_matchup_card_loss(self, mock_get_image_url, mock_get_top_3):
        """Test generating matchup card for a loss."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"
        mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {}
        }

        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 100.0,
                                    "points_against": 120.5
                                }
                            }
                        }
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result["winner"] == "Manager 2"

    @patch('patriot_center_backend.managers.formatters.get_top_3_scorers_from_matchup_data')
    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_valid_matchup_card_tie(self, mock_get_image_url, mock_get_top_3):
        """Test generating matchup card for a tie."""
        mock_get_image_url.return_value = "http://example.com/image.jpg"
        mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {}
        }

        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 110.5,
                                    "points_against": 110.5
                                }
                            }
                        }
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result["winner"] == "Tie"

    def test_missing_matchup_data(self):
        """Test with missing matchup data."""
        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {}
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result == {}

    def test_zero_points_for(self):
        """Test with zero points_for (incomplete data)."""
        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 0.0,
                                    "points_against": 100.0
                                }
                            }
                        }
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result == {}

    def test_zero_points_against(self):
        """Test with zero points_against (incomplete data)."""
        manager_cache = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 100.0,
                                    "points_against": 0.0
                                }
                            }
                        }
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.MANAGER_CACHE', manager_cache):
            from patriot_center_backend.managers.formatters import get_matchup_card
            result = get_matchup_card("Manager 1", "Manager 2", "2023", "1", {})

        assert result == {}


class TestGetTradeCard:
    """Test get_trade_card function."""

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_simple_two_team_trade(self, mock_get_image_url):
        """Test generating trade card for simple two-team trade."""
        mock_get_image_url.side_effect = [
            {"name": "Manager 1", "image_url": "http://example.com/m1.jpg"},
            {"name": "Manager 2", "image_url": "http://example.com/m2.jpg"},
            {"name": "Player A", "image_url": "http://example.com/pa.jpg"},
            {"name": "Player B", "image_url": "http://example.com/pb.jpg"}
        ]

        transaction_ids_cache = {
            "trade123": {
                "year": "2023",
                "week": "5",
                "managers_involved": ["Manager 1", "Manager 2"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2"
                    },
                    "Player B": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 1"
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.TRANSACTION_IDS_CACHE', transaction_ids_cache):
            from patriot_center_backend.managers.formatters import get_trade_card
            result = get_trade_card("trade123", {})

        assert result["year"] == "2023"
        assert result["week"] == "5"
        assert len(result["managers_involved"]) == 2
        assert len(result["manager_1_sent"]) == 1
        assert len(result["manager_1_received"]) == 1
        assert len(result["manager_2_sent"]) == 1
        assert len(result["manager_2_received"]) == 1
        assert result["transaction_id"] == "trade123"

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_three_team_trade(self, mock_get_image_url):
        """Test generating trade card for three-team trade."""
        mock_get_image_url.return_value = {"name": "Test", "image_url": "http://example.com/test.jpg"}

        transaction_ids_cache = {
            "trade456": {
                "year": "2023",
                "week": "8",
                "managers_involved": ["Manager 1", "Manager 2", "Manager 3"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2"
                    },
                    "Player B": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 3"
                    },
                    "Player C": {
                        "old_manager": "Manager 3",
                        "new_manager": "Manager 1"
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.TRANSACTION_IDS_CACHE', transaction_ids_cache):
            from patriot_center_backend.managers.formatters import get_trade_card
            result = get_trade_card("trade456", {})

        assert len(result["managers_involved"]) == 3
        # Each manager sent and received one player
        assert "manager_1_sent" in result
        assert "manager_1_received" in result
        assert "manager_2_sent" in result
        assert "manager_2_received" in result
        assert "manager_3_sent" in result
        assert "manager_3_received" in result

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_uneven_trade(self, mock_get_image_url):
        """Test trade where one manager sends multiple players."""
        mock_get_image_url.return_value = {"name": "Test", "image_url": "http://example.com/test.jpg"}

        transaction_ids_cache = {
            "trade789": {
                "year": "2023",
                "week": "10",
                "managers_involved": ["Manager 1", "Manager 2"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2"
                    },
                    "Player B": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2"
                    },
                    "Player C": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 1"
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.TRANSACTION_IDS_CACHE', transaction_ids_cache):
            from patriot_center_backend.managers.formatters import get_trade_card
            result = get_trade_card("trade789", {})

        # Manager 1 sent 2, received 1
        assert len(result["manager_1_sent"]) == 2
        assert len(result["manager_1_received"]) == 1
        # Manager 2 sent 1, received 2
        assert len(result["manager_2_sent"]) == 1
        assert len(result["manager_2_received"]) == 2

    @patch('patriot_center_backend.managers.formatters.get_image_url')
    def test_manager_name_with_spaces(self, mock_get_image_url):
        """Test handling manager names with spaces."""
        mock_get_image_url.return_value = {"name": "Test", "image_url": "http://example.com/test.jpg"}

        transaction_ids_cache = {
            "trade999": {
                "year": "2023",
                "week": "3",
                "managers_involved": ["John Smith", "Jane Doe"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "John Smith",
                        "new_manager": "Jane Doe"
                    }
                }
            }
        }

        with patch('patriot_center_backend.managers.formatters.TRANSACTION_IDS_CACHE', transaction_ids_cache):
            from patriot_center_backend.managers.formatters import get_trade_card
            result = get_trade_card("trade999", {})

        # Should convert spaces to underscores and lowercase
        assert "john_smith_sent" in result
        assert "john_smith_received" in result
        assert "jane_doe_sent" in result
        assert "jane_doe_received" in result
