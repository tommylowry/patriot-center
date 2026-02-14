"""Unit tests for aggregation_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.aggregation_exporter import (
    get_aggregated_managers,
    get_aggregated_players,
    get_player_manager_aggregation,
)

MODULE_PATH = "patriot_center_backend.exporters.aggregation_exporter"


class TestGetAggregatedPlayers:
    """Test get_aggregated_players method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_starters_from_cache`: `mock_get_starters`
        - `get_ffwar_from_cache`: `mock_get_ffwar`
        - `slugify`: `mock_slugify`
        - `get_team`: `mock_get_team`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_starters_from_cache"
            ) as mock_get_starters,
            patch(f"{MODULE_PATH}.get_ffwar_from_cache") as mock_get_ffwar,
            patch(f"{MODULE_PATH}.slugify") as mock_slugify,
            patch(f"{MODULE_PATH}.get_team") as mock_get_team,
        ):
            self.mock_get_starters = mock_get_starters
            self.mock_get_starters.return_value = {}

            self.mock_get_ffwar = mock_get_ffwar
            self.mock_get_ffwar.return_value = 0.0

            self.mock_slugify = mock_slugify
            self.mock_slugify.side_effect = (
                lambda name: name.lower().replace(" ", "-")
            )

            self.mock_get_team = mock_get_team
            self.mock_get_team.return_value = "WAS"

            yield

    def test_get_aggregated_players_empty(self):
        """Test aggregation with empty starters cache."""
        result = get_aggregated_players(manager="Tommy")

        assert result == {}

    def test_get_aggregated_players_single_week(self):
        """Test aggregation for a single week."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 25.5,
                            "position": "QB",
                        },
                        "Total_Points": 120.0,
                    }
                }
            }
        }
        self.mock_get_ffwar.return_value = 1.5

        result = get_aggregated_players(manager="Tommy")

        assert "Jayden Daniels" in result
        assert result["Jayden Daniels"]["total_points"] == 25.5
        assert result["Jayden Daniels"]["num_games_started"] == 1
        assert result["Jayden Daniels"]["ffWAR"] == 1.5
        assert result["Jayden Daniels"]["position"] == "QB"
        assert result["Jayden Daniels"]["team"] == "WAS"

    def test_get_aggregated_players_multiple_weeks(self):
        """Test aggregation across multiple weeks accumulates totals."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 20.0,
                            "position": "QB",
                        },
                    }
                },
                "2": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 30.0,
                            "position": "QB",
                        },
                    }
                },
            }
        }
        self.mock_get_ffwar.return_value = 1.0

        result = get_aggregated_players(manager="Tommy")

        assert result["Jayden Daniels"]["total_points"] == 50.0
        assert result["Jayden Daniels"]["num_games_started"] == 2
        assert result["Jayden Daniels"]["ffWAR"] == 2.0

    def test_get_aggregated_players_skips_total_points_key(self):
        """Test that the Total_Points key is skipped."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Total_Points": 120.0,
                        "Jayden Daniels": {
                            "points": 25.5,
                            "position": "QB",
                        },
                    }
                }
            }
        }

        result = get_aggregated_players(manager="Tommy")

        assert "Total_Points" not in result
        assert "Jayden Daniels" in result

    def test_get_aggregated_players_with_placement(self):
        """Test aggregation includes playoff placement data."""
        self.mock_get_starters.return_value = {
            "2023": {
                "17": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 30.0,
                            "position": "QB",
                            "placement": 1,
                        },
                    }
                }
            }
        }

        result = get_aggregated_players(manager="Tommy")

        assert "playoff_placement" in result["Jayden Daniels"]
        assert result["Jayden Daniels"]["playoff_placement"] == {
            "Tommy": {"2023": 1}
        }

    def test_get_aggregated_players_passes_filters(self):
        """Test that season and week filters are passed through."""
        get_aggregated_players(manager="Tommy", season=2023, week=5)

        self.mock_get_starters.assert_called_once_with(
            manager="Tommy", season=2023, week=5
        )


class TestGetAggregatedManagers:
    """Test get_aggregated_managers method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_starters_from_cache`: `mock_get_starters`
        - `get_ffwar_from_cache`: `mock_get_ffwar`
        - `slugify`: `mock_slugify`
        - `get_team`: `mock_get_team`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_starters_from_cache"
            ) as mock_get_starters,
            patch(f"{MODULE_PATH}.get_ffwar_from_cache") as mock_get_ffwar,
            patch(f"{MODULE_PATH}.slugify") as mock_slugify,
            patch(f"{MODULE_PATH}.get_team") as mock_get_team,
        ):
            self.mock_get_starters = mock_get_starters
            self.mock_get_starters.return_value = {}

            self.mock_get_ffwar = mock_get_ffwar
            self.mock_get_ffwar.return_value = 0.0

            self.mock_slugify = mock_slugify
            self.mock_slugify.side_effect = (
                lambda name: name.lower().replace(" ", "-")
            )

            self.mock_get_team = mock_get_team
            self.mock_get_team.return_value = "WAS"

            yield

    def test_get_aggregated_managers_empty(self):
        """Test aggregation with empty starters cache."""
        result = get_aggregated_managers(player="Jayden Daniels")

        assert result == {}

    def test_get_aggregated_managers_single_manager(self):
        """Test aggregation for a player on one manager's team."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 25.5,
                            "position": "QB",
                        },
                    }
                }
            }
        }
        self.mock_get_ffwar.return_value = 1.5

        result = get_aggregated_managers(player="Jayden Daniels")

        assert "Tommy" in result
        assert result["Tommy"]["total_points"] == 25.5
        assert result["Tommy"]["num_games_started"] == 1
        assert result["Tommy"]["player"] == "Jayden Daniels"

    def test_get_aggregated_managers_multiple_managers(self):
        """Test aggregation when player was on multiple managers' teams."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Jayden Daniels": {
                            "points": 25.0,
                            "position": "QB",
                        },
                    },
                    "Benz": {
                        "Jayden Daniels": {
                            "points": 20.0,
                            "position": "QB",
                        },
                    },
                }
            }
        }

        result = get_aggregated_managers(player="Jayden Daniels")

        assert "Tommy" in result
        assert "Benz" in result

    def test_get_aggregated_managers_player_not_found(self):
        """Test aggregation when player is not in any manager's roster."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Brian Robinson": {
                            "points": 15.0,
                            "position": "RB",
                        },
                    }
                }
            }
        }

        result = get_aggregated_managers(player="Jayden Daniels")

        assert result == {}

    def test_get_aggregated_managers_passes_filters(self):
        """Test that season and week filters are passed through."""
        get_aggregated_managers(player="Jayden Daniels", season=2023, week=5)

        self.mock_get_starters.assert_called_once_with(season=2023, week=5)


class TestGetPlayerManagerAggregation:
    """Test get_player_manager_aggregation method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_starters_from_cache`: `mock_get_starters`
        - `get_ffwar_from_cache`: `mock_get_ffwar`
        - `slugify`: `mock_slugify`
        - `get_team`: `mock_get_team`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_starters_from_cache"
            ) as mock_get_starters,
            patch(f"{MODULE_PATH}.get_ffwar_from_cache") as mock_get_ffwar,
            patch(f"{MODULE_PATH}.slugify") as mock_slugify,
            patch(f"{MODULE_PATH}.get_team") as mock_get_team,
        ):
            self.mock_get_starters = mock_get_starters
            self.mock_get_starters.return_value = {
                "2023": {
                    "1": {
                        "Tommy": {
                            "Jayden Daniels": {
                                "points": 25.5,
                                "position": "QB",
                            },
                        },
                    }
                }
            }

            self.mock_get_ffwar = mock_get_ffwar
            self.mock_get_ffwar.return_value = 1.5

            self.mock_slugify = mock_slugify
            self.mock_slugify.side_effect = (
                lambda name: name.lower().replace(" ", "-")
            )

            self.mock_get_team = mock_get_team
            self.mock_get_team.return_value = "WAS"

            yield

    def test_get_player_manager_aggregation_found(self):
        """Test getting aggregation for existing player-manager pair."""
        result = get_player_manager_aggregation("Jayden Daniels", "Tommy")

        assert "Tommy" in result
        assert result["Tommy"]["total_points"] == 25.5

    def test_get_player_manager_aggregation_not_found(self):
        """Test getting aggregation for non-existent pair."""
        result = get_player_manager_aggregation("Jayden Daniels", "Benz")

        assert result == {}

    def test_get_player_manager_aggregation_with_season(self):
        """Test aggregation with season filter."""
        result = get_player_manager_aggregation(
            "Jayden Daniels", "Tommy", season="2023"
        )

        assert "Tommy" in result

    def test_get_player_manager_aggregation_with_season_and_week(self):
        """Test aggregation with season and week filters."""
        result = get_player_manager_aggregation(
            "Jayden Daniels", "Tommy", season="2023", week="1"
        )

        assert "Tommy" in result

    def test_get_player_manager_aggregation_player_not_on_roster(self):
        """Test aggregation when player not on any roster."""
        self.mock_get_starters.return_value = {
            "2023": {
                "1": {
                    "Tommy": {
                        "Brian Robinson": {
                            "points": 15.0,
                            "position": "RB",
                        },
                    },
                }
            }
        }

        result = get_player_manager_aggregation("Jayden Daniels", "Tommy")

        assert result == {}
