"""Test formatting functions with both good and bad scenarios."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.formatters import (
    draft_pick_decipher,
    extract_dict_data,
    get_matchup_card,
    get_season_state,
    get_top_3_scorers_from_matchup_data,
    get_trade_card,
)


@pytest.fixture(autouse=True)
def globals_setup():
    """Setup common mocks for all tests.

    The mocks are set up to return a pre-defined
    set of values when accessed.
    - `LEAGUE_IDS`: `{2023: "league123"}`

    Yields:
        None
    """
    with patch(
        "patriot_center_backend.managers.formatters.LEAGUE_IDS",
        {2023: "league123"},
    ):
        yield


class TestGetSeasonState:
    """Test get_season_state function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.managers.formatters.fetch_sleeper_data"
        ) as mock_fetch_sleeper:
            self.mock_fetch_sleeper = mock_fetch_sleeper

            yield

    def test_regular_season(self):
        """Test regular season detection."""
        week = "5"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        self.mock_fetch_sleeper.assert_not_called()

    def test_playoffs(self):
        """Test playoff detection."""
        week = "15"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"
        self.mock_fetch_sleeper.assert_not_called()

    def test_playoffs_late_week(self):
        """Test playoff detection in late weeks."""
        week = "17"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "playoffs"

    def test_fetch_playoff_week_from_api(self):
        """Test fetching playoff_week_start from API when not provided."""
        self.mock_fetch_sleeper.return_value = {
            "settings": {"playoff_week_start": 15}
        }

        week = "10"
        year = "2023"
        playoff_week_start = None

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"
        self.mock_fetch_sleeper.assert_called_once_with("league/league123")

    def test_missing_week_raises_error(self):
        """Test that missing week raises ValueError."""
        week = None
        year = "2023"
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)  # type: ignore

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
            get_season_state(week, year, playoff_week_start)  # type: ignore

    def test_empty_year_raises_error(self):
        """Test that empty year raises ValueError."""
        week = "5"
        year = ""
        playoff_week_start = 15

        with pytest.raises(ValueError, match="Week or Year not set"):
            get_season_state(week, year, playoff_week_start)

    def test_boundary_week_before_playoffs(self):
        """Test week just before playoffs."""
        week = "14"
        year = "2023"
        playoff_week_start = 15

        result = get_season_state(week, year, playoff_week_start)

        assert result == "regular_season"


class TestGetTop3ScorersFromMatchupData:
    """Test get_top_3_scorers_from_matchup_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `get_image_url`: `mock_get_image_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.formatters"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
            patch(
                "patriot_center_backend.managers.formatters"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.managers.formatters"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.managers.data_exporter.get_image_url"
            ) as mock_get_image_url,
        ):
            self.mock_get_player_ids = mock_get_player_ids
            self.mock_get_player_ids.return_value = {}

            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = {}

            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = {}

            self.mock_get_image_url = mock_get_image_url

            yield

    def test_valid_matchup_data(self):
        """Test with valid matchup data and starters."""
        self.mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg",
        }
        self.mock_get_players_cache.return_value = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"},
            "Player C": {"player_id": "3"},
            "Player D": {"player_id": "4"},
            "Player E": {"player_id": "5"},
            "Player F": {"player_id": "6"},
        }
        self.mock_get_player_ids.return_value = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"},
            "3": {"first_name": "Player", "last_name": "C"},
            "4": {"first_name": "Player", "last_name": "D"},
            "5": {"first_name": "Player", "last_name": "E"},
            "6": {"first_name": "Player", "last_name": "F"},
        }
        self.mock_get_starters_cache.return_value = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Player B": {"points": 18.0, "position": "RB"},
                        "Player C": {"points": 12.5, "position": "WR"},
                        "Total_Points": 56.0,
                    },
                    "Manager 2": {
                        "Player D": {"points": 30.0, "position": "QB"},
                        "Player E": {"points": 15.0, "position": "RB"},
                        "Player F": {"points": 10.0, "position": "WR"},
                        "Total_Points": 55.0,
                    },
                }
            }
        }

        matchup_data: dict[str, Any] = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        assert len(matchup_data) == 6  # original data and the 4 new lists
        assert len(matchup_data["manager_1_top_3_scorers"]) == 3
        assert len(matchup_data["manager_2_top_3_scorers"]) == 3
        assert matchup_data["manager_1_top_3_scorers"][0]["score"] == 25.5
        assert matchup_data["manager_1_lowest_scorer"]["score"] == 12.5
        assert matchup_data["manager_2_top_3_scorers"][0]["score"] == 30.0
        assert matchup_data["manager_2_lowest_scorer"]["score"] == 10.0

    def test_missing_year_in_matchup_data(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test with missing year in matchup_data.

        Args:
            caplog: pytest fixture for capturing logs.
        """
        matchup_data = {"week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "matchup_data missing" in caplog.text

        assert matchup_data["manager_1_top_3_scorers"] == []
        assert matchup_data["manager_2_top_3_scorers"] == []
        assert matchup_data["manager_1_lowest_scorer"] == []
        assert matchup_data["manager_2_lowest_scorer"] == []

    def test_missing_week_in_matchup_data(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test with missing week in matchup_data.

        Args:
            caplog: pytest fixture for capturing logs.
        """
        matchup_data = {"year": "2023"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "matchup_data missing" in caplog.text

        assert matchup_data["manager_1_top_3_scorers"] == []
        assert matchup_data["manager_2_top_3_scorers"] == []

    def test_missing_manager_1_starters(self, caplog: pytest.LogCaptureFixture):
        """Test with manager_1 missing from starters_cache.

        Args:
            caplog: pytest fixture for capturing logs.
        """
        self.mock_get_starters_cache.return_value = {
            "2023": {
                "1": {
                    "Manager 2": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Total_Points": 25.5,
                    }
                }
            }
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "data missing" in caplog.text
        assert "week 1" in caplog.text
        assert "2023" in caplog.text

        assert matchup_data["manager_1_top_3_scorers"] == []
        assert matchup_data["manager_2_top_3_scorers"] == []

    def test_missing_manager_2_starters(self, caplog: pytest.LogCaptureFixture):
        """Test with manager_2 missing from starters_cache.

        Args:
            caplog: pytest fixture for capturing logs.
        """
        self.mock_get_starters_cache.return_value = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Total_Points": 25.5,
                    }
                }
            }
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "data missing" in caplog.text
        assert "week 1" in caplog.text
        assert "2023" in caplog.text

        assert matchup_data["manager_1_top_3_scorers"] == []
        assert matchup_data["manager_2_top_3_scorers"] == []

    def test_fewer_than_3_players(self):
        """Test with fewer than 3 starters."""
        self.mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg",
        }
        self.mock_get_players_cache.return_value = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"},
        }
        self.mock_get_player_ids.return_value = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"},
        }
        self.mock_get_starters_cache.return_value = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 25.5, "position": "QB"},
                        "Player B": {"points": 18.0, "position": "RB"},
                        "Total_Points": 43.5,
                    },
                    "Manager 2": {
                        "Player A": {"points": 20.0, "position": "QB"},
                        "Total_Points": 20.0,
                    },
                }
            }
        }

        matchup_data = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Should return only 2 players for manager_1
        assert len(matchup_data["manager_1_top_3_scorers"]) == 2
        # Should return only 1 player for manager_2
        assert len(matchup_data["manager_2_top_3_scorers"]) == 1

    def test_insertion_sort_ordering(self):
        """Test that top scorers are properly sorted."""
        self.mock_get_image_url.side_effect = lambda *args, **kwargs: {
            "name": "Player",
            "image_url": "http://example.com/image.jpg",
        }
        self.mock_get_players_cache.return_value = {
            "Player A": {"player_id": "1"},
            "Player B": {"player_id": "2"},
            "Player C": {"player_id": "3"},
            "Player D": {"player_id": "4"},
            "Player E": {"player_id": "5"},
        }
        self.mock_get_player_ids.return_value = {
            "1": {"first_name": "Player", "last_name": "A"},
            "2": {"first_name": "Player", "last_name": "B"},
            "3": {"first_name": "Player", "last_name": "C"},
            "4": {"first_name": "Player", "last_name": "D"},
            "5": {"first_name": "Player", "last_name": "E"},
        }
        self.mock_get_starters_cache.return_value = {
            "2023": {
                "1": {
                    "Manager 1": {
                        "Player A": {"points": 10.0, "position": "WR"},  # 4th
                        "Player B": {"points": 25.0, "position": "QB"},  # 1st
                        "Player C": {"points": 15.0, "position": "RB"},  # 3rd
                        "Player D": {"points": 20.0, "position": "TE"},  # 2nd
                        "Player E": {"points": 5.0, "position": "K"},  # 5th
                        "Total_Points": 75.0,
                    },
                    "Manager 2": {
                        "Player A": {"points": 20.0, "position": "QB"},
                        "Total_Points": 20.0,
                    },
                }
            }
        }

        matchup_data: dict[str, Any] = {"year": "2023", "week": "1"}
        manager_1 = "Manager 1"
        manager_2 = "Manager 2"

        get_top_3_scorers_from_matchup_data(
            matchup_data=matchup_data,
            manager_1=manager_1,
            manager_2=manager_2,
            image_urls={},
        )

        # Verify top 3 are in descending order
        # Player B (25.0), Player D (20.0), Player C (15.0)
        assert matchup_data["manager_1_top_3_scorers"][0]["score"] == 25.0
        assert matchup_data["manager_1_top_3_scorers"][1]["score"] == 20.0
        assert matchup_data["manager_1_top_3_scorers"][2]["score"] == 15.0

        # Verify lowest scorer
        # Player E (5.0)
        assert matchup_data["manager_1_lowest_scorer"]["score"] == 5.0


class TestGetMatchupCard:
    """Test get_matchup_card function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `get_top_3_scorers_from_matchup_data`: `mock_get_top_3`
        - `get_image_url`: `mock_get_image_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.formatters"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.managers.formatters"
                ".get_top_3_scorers_from_matchup_data"
            ) as mock_get_top_3,
            patch(
                "patriot_center_backend.managers.data_exporter.get_image_url"
            ) as mock_get_image_url,
        ):
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = {}

            self.mock_get_top_3 = mock_get_top_3
            self.mock_get_top_3.return_value = {}

            self.mock_get_image_url = mock_get_image_url

            yield

    def test_valid_matchup_card_win(self):
        """Test generating matchup card for a win."""
        self.mock_get_image_url.return_value = "http://example.com/image.jpg"
        self.mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {},
        }
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 120.5,
                                    "points_against": 100.0,
                                }
                            }
                        }
                    }
                }
            }
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        assert result["year"] == "2023"
        assert result["week"] == "1"
        assert result["manager_1_score"] == 120.5
        assert result["manager_2_score"] == 100.0
        assert result["winner"] == "Manager 1"

    def test_valid_matchup_card_loss(self):
        """Test generating matchup card for a loss."""
        self.mock_get_image_url.return_value = "http://example.com/image.jpg"
        self.mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {},
        }
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 100.0,
                                    "points_against": 120.5,
                                }
                            }
                        }
                    }
                }
            }
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        assert result["winner"] == "Manager 2"

    def test_valid_matchup_card_tie(self):
        """Test generating matchup card for a tie."""
        self.mock_get_image_url.return_value = "http://example.com/image.jpg"
        self.mock_get_top_3.return_value = {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": {},
            "manager_2_lowest_scorer": {},
        }
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 110.5,
                                    "points_against": 110.5,
                                }
                            }
                        }
                    }
                }
            }
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        assert result["winner"] == "Tie"

    def test_missing_matchup_data(self, caplog: pytest.LogCaptureFixture):
        """Test with missing matchup data.

        Args:
            caplog: pytest caplog
        """
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {"years": {"2023": {"weeks": {}}}}
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "Incomplete matchup" in caplog.text
        assert "week 1" in caplog.text
        assert "2023" in caplog.text

        assert result == {}

    def test_zero_points_for(self, caplog: pytest.LogCaptureFixture):
        """Test with zero points_for (incomplete data).

        Args:
            caplog: pytest capsys
        """
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 0.0,
                                    "points_against": 100.0,
                                }
                            }
                        }
                    }
                }
            }
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "Incomplete matchup" in caplog.text
        assert "week 1" in caplog.text
        assert "2023" in caplog.text

        assert result == {}

    def test_zero_points_against(self, caplog: pytest.LogCaptureFixture):
        """Test with zero points_against (incomplete data).

        Args:
            caplog: pytest capsys
        """
        self.mock_get_manager_cache.return_value = {
            "Manager 1": {
                "years": {
                    "2023": {
                        "weeks": {
                            "1": {
                                "matchup_data": {
                                    "points_for": 100.0,
                                    "points_against": 0.0,
                                }
                            }
                        }
                    }
                }
            }
        }

        result = get_matchup_card(
            manager_1="Manager 1",
            manager_2="Manager 2",
            year="2023",
            week="1",
            image_urls={},
        )

        # Verify warning was printed for missing data
        assert "Incomplete matchup" in caplog.text
        assert "week 1" in caplog.text
        assert "2023" in caplog.text

        assert result == {}


class TestGetTradeCard:
    """Test get_trade_card function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_trans_ids`
        - `get_image_url`: `mock_get_image_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.formatters"
                ".CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_trans_ids,
            patch(
                "patriot_center_backend.managers.data_exporter.get_image_url"
            ) as mock_get_image_url,
        ):
            self.mock_get_trans_ids = mock_get_trans_ids
            self.mock_get_trans_ids.return_value = {}

            self.mock_get_image_url = mock_get_image_url

            yield

    def test_simple_two_team_trade(self):
        """Test generating trade card for simple two-team trade."""
        self.mock_get_image_url.side_effect = [
            {"name": "Manager 1", "image_url": "http://example.com/m1.jpg"},
            {"name": "Manager 2", "image_url": "http://example.com/m2.jpg"},
            {"name": "Player A", "image_url": "http://example.com/pa.jpg"},
            {"name": "Player B", "image_url": "http://example.com/pb.jpg"},
        ]
        self.mock_get_trans_ids.return_value = {
            "trade123": {
                "year": "2023",
                "week": "5",
                "managers_involved": ["Manager 1", "Manager 2"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2",
                    },
                    "Player B": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 1",
                    },
                },
            }
        }

        transaction_id = "trade123"
        image_urls = {}

        result = get_trade_card(transaction_id, image_urls)

        assert result["year"] == "2023"
        assert result["week"] == "5"
        assert len(result["managers_involved"]) == 2
        assert len(result["manager_1_sent"]) == 1
        assert len(result["manager_1_received"]) == 1
        assert len(result["manager_2_sent"]) == 1
        assert len(result["manager_2_received"]) == 1
        assert result["transaction_id"] == "trade123"

    def test_three_team_trade(self):
        """Test generating trade card for three-team trade."""
        self.mock_get_image_url.return_value = {
            "name": "Test",
            "image_url": "http://example.com/test.jpg",
        }
        self.mock_get_trans_ids.return_value = {
            "trade456": {
                "year": "2023",
                "week": "8",
                "managers_involved": ["Manager 1", "Manager 2", "Manager 3"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2",
                    },
                    "Player B": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 3",
                    },
                    "Player C": {
                        "old_manager": "Manager 3",
                        "new_manager": "Manager 1",
                    },
                },
            }
        }

        transaction_id = "trade456"
        image_urls = {}

        result = get_trade_card(transaction_id, image_urls)

        assert len(result["managers_involved"]) == 3
        # Each manager sent and received one player
        assert "manager_1_sent" in result
        assert "manager_1_received" in result
        assert "manager_2_sent" in result
        assert "manager_2_received" in result
        assert "manager_3_sent" in result
        assert "manager_3_received" in result

    def test_uneven_trade(self):
        """Test trade where one manager sends multiple players."""
        self.mock_get_image_url.return_value = {
            "name": "Test",
            "image_url": "http://example.com/test.jpg",
        }
        self.mock_get_trans_ids.return_value = {
            "trade789": {
                "year": "2023",
                "week": "10",
                "managers_involved": ["Manager 1", "Manager 2"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2",
                    },
                    "Player B": {
                        "old_manager": "Manager 1",
                        "new_manager": "Manager 2",
                    },
                    "Player C": {
                        "old_manager": "Manager 2",
                        "new_manager": "Manager 1",
                    },
                },
            }
        }

        transaction_id = "trade789"
        image_urls = {}

        result = get_trade_card(transaction_id, image_urls)

        # Manager 1 sent 2, received 1
        assert len(result["manager_1_sent"]) == 2
        assert len(result["manager_1_received"]) == 1
        # Manager 2 sent 1, received 2
        assert len(result["manager_2_sent"]) == 1
        assert len(result["manager_2_received"]) == 2

    def test_manager_name_with_spaces(self):
        """Test handling manager names with spaces."""
        self.mock_get_image_url.return_value = {
            "name": "Test",
            "image_url": "http://example.com/test.jpg",
        }
        self.mock_get_trans_ids.return_value = {
            "trade999": {
                "year": "2023",
                "week": "3",
                "managers_involved": ["John Smith", "Jane Doe"],
                "trade_details": {
                    "Player A": {
                        "old_manager": "John Smith",
                        "new_manager": "Jane Doe",
                    }
                },
            }
        }

        transaction_id = "trade999"
        image_urls = {}

        result = get_trade_card(transaction_id, image_urls)

        # Should convert spaces to underscores and lowercase
        assert "john_smith_sent" in result
        assert "john_smith_received" in result
        assert "jane_doe_sent" in result
        assert "jane_doe_received" in result


class TestExtractDictData:
    """Test extract_dict_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_image_url`: `mock_get_image_url`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.data_exporter.get_image_url"
            ) as mock_get_image_url,
        ):
            self.mock_get_image_url = mock_get_image_url
            self.mock_get_image_url.return_value = (
                "http://example.com/image.jpg"
            )

            yield

    def test_top_3_simple_dict(self):
        """Test with simple dictionary (no nested totals)."""
        data = {"Player A": 10, "Player B": 8, "Player C": 6, "Player D": 4}
        image_urls = {}

        result = extract_dict_data(data, image_urls)

        assert len(result) == 3
        assert result[0]["name"] == "Player A"
        assert result[0]["count"] == 10
        assert result[1]["name"] == "Player B"
        assert result[1]["count"] == 8
        assert result[2]["name"] == "Player C"
        assert result[2]["count"] == 6

    def test_top_3_with_nested_totals(self):
        """Test with nested dictionary containing 'total' keys."""
        data = {
            "Player A": {"total": 10, "other": "data"},
            "Player B": {"total": 8, "other": "data"},
            "Player C": {"total": 6, "other": "data"},
            "Player D": {"total": 4, "other": "data"},
        }
        image_urls = {}

        result = extract_dict_data(data, image_urls)

        assert len(result) == 3
        assert result[0]["name"] == "Player A"
        assert result[0]["count"] == 10

    def test_no_cutoff(self):
        """Test with cutoff=0 to include all items."""
        data = {"Player A": 10, "Player B": 8, "Player C": 6, "Player D": 4}
        image_urls = {}

        result = extract_dict_data(data, image_urls, cutoff=0)

        assert len(result) == 4

    def test_ties_at_cutoff(self):
        """Test tie-breaking logic when items are tied at cutoff position."""
        data = {
            "Player A": 10,
            "Player B": 8,
            "Player C": 6,
            "Player D": 6,  # Tied with Player C
            "Player E": 6,  # Tied with Player C and D
            "Player F": 4,
        }
        image_urls = {}

        result = extract_dict_data(data, image_urls, cutoff=3)

        # Should include all tied items at position 3
        assert len(result) == 5  # A, B, C, D, E all included

    def test_custom_key_value_names(self):
        """Test with custom key_name and value_name."""
        data = {"Player A": 10, "Player B": 8}
        image_urls = {}

        result = extract_dict_data(
            data, image_urls, key_name="player_name", value_name="score"
        )

        assert result[0]["player_name"] == "Player A"
        assert result[0]["score"] == 10
        assert "name" not in result[0]
        assert "count" not in result[0]

    def test_fewer_than_cutoff_items(self):
        """Test with fewer items than cutoff."""
        data = {"Player A": 10, "Player B": 8}
        image_urls = {}

        result = extract_dict_data(data, image_urls, cutoff=5)

        assert len(result) == 2


class TestDraftPickDecipher:
    """Test draft_pick_decipher function."""

    def test_valid_draft_pick(self):
        """Test with valid draft pick dictionary."""
        draft_pick_dict = {
            "season": "2023",
            "round": 3,
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2,
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's 2023 Round 3 Draft Pick"

    def test_first_round_pick(self):
        """Test with first round pick."""
        draft_pick_dict = {
            "season": "2024",
            "round": 1,
            "roster_id": 5,
            "previous_owner_id": 5,
            "owner_id": 3,
        }
        weekly_roster_ids = {3: "Manager 3", 5: "Manager 5"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 5's 2024 Round 1 Draft Pick"

    def test_unknown_roster_id(self):
        """Test with roster_id not in weekly_roster_ids."""
        draft_pick_dict = {
            "season": "2023",
            "round": 2,
            "roster_id": 999,
            "previous_owner_id": 1,
            "owner_id": 2,
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "unknown_manager's 2023 Round 2 Draft Pick"

    def test_missing_season(self):
        """Test with missing season - should use 'unknown_year'."""
        draft_pick_dict = {
            "round": 2,
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2,
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's unknown_year Round 2 Draft Pick"

    def test_missing_round(self):
        """Test with missing round - should use 'unknown_round'."""
        draft_pick_dict = {
            "season": "2023",
            "roster_id": 1,
            "previous_owner_id": 1,
            "owner_id": 2,
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "Manager 1's 2023 Round unknown_round Draft Pick"

    def test_missing_roster_id(self):
        """Test with missing roster_id - should use 'unknown_team'."""
        draft_pick_dict = {
            "season": "2023",
            "round": 2,
            "previous_owner_id": 1,
            "owner_id": 2,
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = draft_pick_decipher(draft_pick_dict, weekly_roster_ids)
        assert result == "unknown_manager's 2023 Round 2 Draft Pick"
