"""
Pytest fixtures for backend tests.

Provides reusable test data, mocks, and fixtures for all test modules.
"""
import json
import pytest
import tempfile
import os
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# CRITICAL: Patch save_cache, load_cache, AND load_or_update_* functions at module import level
# to prevent cache file modifications. These patches must be applied BEFORE any service
# modules are imported, as they call load_or_update_* functions at import time.
# This prevents test execution from loading or modifying production cache files.
# We patch both the low-level cache functions and the high-level loader functions.
_save_cache_patcher = patch('patriot_center_backend.utils.cache_utils.save_cache', MagicMock())
_load_cache_patcher = patch('patriot_center_backend.utils.cache_utils.load_cache', MagicMock(return_value={}))

# Patch load_or_update_* functions that are called at module import time in service files
_load_or_update_starters_patcher = patch('patriot_center_backend.utils.starters_loader.load_or_update_starters_cache', MagicMock(return_value={}))
_load_or_update_replacement_patcher = patch('patriot_center_backend.utils.replacement_score_loader.load_or_update_replacement_score_cache', MagicMock(return_value={}))
_load_or_update_ffwar_patcher = patch('patriot_center_backend.utils.ffWAR_loader.load_or_update_ffWAR_cache', MagicMock(return_value={}))

# Start the patchers immediately at module import time
_save_cache_patcher.start()
_load_cache_patcher.start()
_load_or_update_starters_patcher.start()
_load_or_update_replacement_patcher.start()
_load_or_update_ffwar_patcher.start()

# Register cleanup to stop patchers when pytest exits
def pytest_unconfigure():
    """Stop cache patchers when pytest session ends."""
    _save_cache_patcher.stop()
    _load_cache_patcher.stop()
    _load_or_update_starters_patcher.stop()
    _load_or_update_replacement_patcher.stop()
    _load_or_update_ffwar_patcher.stop()


@pytest.fixture
def use_real_save_cache():
    """
    Temporarily unpatch save_cache for tests that need to test the real function.

    Use this fixture in tests that specifically test save_cache functionality.
    """
    # Stop the global patcher temporarily
    _save_cache_patcher.stop()

    yield

    # Restart the patcher after the test
    _save_cache_patcher.start()


@pytest.fixture
def use_real_load_cache():
    """
    Temporarily unpatch load_cache for tests that need to test the real function.

    Use this fixture in tests that specifically test load_cache functionality.
    """
    # Stop the global patcher temporarily
    _load_cache_patcher.stop()

    yield

    # Restart the patcher after the test
    _load_cache_patcher.start()


@pytest.fixture
def use_real_load_or_update_starters():
    """
    Temporarily unpatch load_or_update_starters_cache for tests that need to test the real function.

    Use this fixture in tests that specifically test load_or_update_starters_cache functionality.
    """
    _load_or_update_starters_patcher.stop()
    yield
    _load_or_update_starters_patcher.start()


@pytest.fixture
def use_real_load_or_update_replacement():
    """
    Temporarily unpatch load_or_update_replacement_score_cache for tests that need to test the real function.

    Use this fixture in tests that specifically test load_or_update_replacement_score_cache functionality.
    """
    _load_or_update_replacement_patcher.stop()
    yield
    _load_or_update_replacement_patcher.start()


@pytest.fixture
def use_real_load_or_update_ffwar():
    """
    Temporarily unpatch load_or_update_ffWAR_cache for tests that need to test the real function.

    Use this fixture in tests that specifically test load_or_update_ffWAR_cache functionality.
    """
    _load_or_update_ffwar_patcher.stop()
    yield
    _load_or_update_ffwar_patcher.start()


@pytest.fixture
def use_real_cache_for_integration_tests():
    """
    Temporarily unpatch ALL cache functions for integration tests that need real cache data.

    Use this fixture for integration tests that validate against actual cache data,
    such as valid_options integration tests.
    """
    # Stop all the patchers
    _load_cache_patcher.stop()
    _load_or_update_starters_patcher.stop()
    _load_or_update_replacement_patcher.stop()
    _load_or_update_ffwar_patcher.stop()

    yield

    # Restart all the patchers
    _load_cache_patcher.start()
    _load_or_update_starters_patcher.start()
    _load_or_update_replacement_patcher.start()
    _load_or_update_ffwar_patcher.start()


@pytest.fixture
def mock_player_ids():
    """Sample player IDs data for testing."""
    return {
        "7547": {
            "full_name": "Amon-Ra St. Brown",
            "age": 24,
            "years_exp": 3,
            "college": "USC",
            "team": "DET",
            "depth_chart_position": "1",
            "fantasy_positions": ["WR"],
            "position": "WR",
            "number": 14
        },
        "4866": {
            "full_name": "Travis Kelce",
            "age": 34,
            "years_exp": 11,
            "college": "Cincinnati",
            "team": "KC",
            "depth_chart_position": "1",
            "fantasy_positions": ["TE"],
            "position": "TE",
            "number": 87
        },
        "KC": {
            "full_name": "Kansas City Chiefs",
            "position": "DEF",
            "team": "KC",
            "fantasy_positions": ["DEF"]
        }
    }


@pytest.fixture
def mock_starters_cache():
    """Sample starters cache data."""
    return {
        "2024": {
            "1": {
                "Tommy": {
                    "Amon-Ra_St._Brown": {
                        "points": 18.5,
                        "position": "WR",
                        "player_id": "7547"
                    },
                    "Total_Points": 125.3
                },
                "Mike": {
                    "Travis_Kelce": {
                        "points": 12.3,
                        "position": "TE",
                        "player_id": "4866"
                    },
                    "Total_Points": 110.2
                }
            }
        },
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": "1"
    }


@pytest.fixture
def mock_replacement_scores():
    """Sample replacement score data with correct structure."""
    return {
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": 14,
        "2024": {
            "1": {
                "byes": 0,
                "2024_scoring": {
                    "QB": 15.2,
                    "RB": 8.5,
                    "WR": 7.3,
                    "TE": 5.1,
                    "K": 7.0,
                    "DEF": 5.5
                },
                "2025_scoring": {
                    "QB": 15.1,
                    "RB": 8.4,
                    "WR": 7.2,
                    "TE": 5.0,
                    "K": 6.9,
                    "DEF": 5.4
                }
            },
            "5": {
                "byes": 4,
                "2024_scoring": {
                    "QB": 14.8,
                    "RB": 8.0,
                    "WR": 6.8,
                    "TE": 4.7,
                    "K": 6.6,
                    "DEF": 5.1
                }
            }
        }
    }


@pytest.fixture
def mock_ffwar_cache():
    """Sample ffWAR cache data."""
    return {
        "2024": {
            "1": {
                "Amon-Ra_St._Brown": {
                    "ffWAR": 2.345,
                    "position": "WR"
                },
                "Travis_Kelce": {
                    "ffWAR": 1.234,
                    "position": "TE"
                }
            }
        },
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": "1"
    }


@pytest.fixture
def mock_sleeper_api_responses():
    """Common Sleeper API response structures."""
    return {
        "league": {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2024",
            "settings": {
                "playoff_week_start": 15
            }
        },
        "users": [
            {
                "user_id": "user1",
                "display_name": "Tommy",
                "metadata": {"team_name": "Team Tommy"}
            }
        ],
        "rosters": [
            {
                "roster_id": 1,
                "owner_id": "user1",
                "players": ["7547", "4866"]
            }
        ],
        "matchups": [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 18.5}
            }
        ]
    }


@pytest.fixture
def temp_cache_file():
    """Create a temporary cache file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
        json.dump({}, f)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def flask_app():
    """Create a Flask app instance for testing."""
    # Import here to avoid circular imports
    from patriot_center_backend.app import app

    app.config['TESTING'] = True
    app.config['DEBUG'] = False

    yield app


@pytest.fixture
def flask_client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def mock_fetch_sleeper_data():
    """Mock the fetch_sleeper_data function."""
    with patch('patriot_center_backend.utils.sleeper_api_handler.fetch_sleeper_data') as mock:
        mock.return_value = ({"test": "data"}, 200)
        yield mock


@pytest.fixture
def mock_load_cache():
    """Mock the load_cache function."""
    with patch('patriot_center_backend.utils.cache_utils.load_cache') as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture
def mock_save_cache():
    """Mock the save_cache function."""
    with patch('patriot_center_backend.utils.cache_utils.save_cache') as mock:
        yield mock


@pytest.fixture
def mock_current_season_week():
    """Mock get_current_season_and_week to return fixed values."""
    with patch('patriot_center_backend.utils.cache_utils.get_current_season_and_week') as mock:
        mock.return_value = (2024, 14)
        yield mock


@pytest.fixture
def sample_aggregated_manager_data():
    """Sample aggregated manager data for testing."""
    return {
        "Tommy": {
            "total_points": 245.67,
            "num_games_started": 5,
            "ffWAR": 12.345,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        },
        "Mike": {
            "total_points": 123.45,
            "num_games_started": 3,
            "ffWAR": -2.145,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        }
    }


@pytest.fixture
def sample_aggregated_player_data():
    """Sample aggregated player data for testing."""
    return {
        "Amon-Ra_St._Brown": {
            "total_points": 245.67,
            "num_games_started": 12,
            "ffWAR": 24.567,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        },
        "Travis_Kelce": {
            "total_points": 189.34,
            "num_games_started": 10,
            "ffWAR": 15.234,
            "position": "TE",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/4866.jpg"
        }
    }

@pytest.fixture
def sample_defenses_in_sleeper_data():
    """Sample Sleeper data including all team defenses."""
    from patriot_center_backend.constants import TEAM_DEFENSE_NAMES

    # Start with some regular players
    data = {
        "7547": {
            "full_name": "Amon-Ra St. Brown",
            "first_name": "Amon-Ra",
            "last_name": "St. Brown",
            "team": "DET",
            "position": "WR"
        },
        "4866": {
            "full_name": "Travis Kelce",
            "first_name": "Travis",
            "last_name": "Kelce",
            "team": "KC",
            "position": "TE"
        },
        "1667": {
            "full_name": "Some Other Player",
            "first_name": "Some",
            "last_name": "Player",
            "team": "XYZ",
            "position": "RB"
        }
    }

    # Add all team defenses dynamically from TEAM_DEFENSE_NAMES
    for team_code, team_info in TEAM_DEFENSE_NAMES.items():
        data[team_code] = {
            "full_name": team_info["full_name"],
            "first_name": team_info["first_name"],
            "last_name": team_info["last_name"],
            "team": team_code,
            "position": "DEF"
        }

    return data


@pytest.fixture
def sample_players_list():
    """Sample player list data for testing /players/list endpoint."""
    return {
        "7547": {
            "full_name": "Amon-Ra St. Brown",
            "first_name": "Amon-Ra",
            "last_name": "St. Brown",
            "slug": "Amon-Ra_St._Brown",
            "position": "WR",
            "team": "DET"
        },
        "4866": {
            "full_name": "Travis Kelce",
            "first_name": "Travis",
            "last_name": "Kelce",
            "slug": "Travis_Kelce",
            "position": "TE",
            "team": "KC"
        },
        "KC": {
            "full_name": "Kansas City Chiefs",
            "first_name": "Kansas City",
            "last_name": "Chiefs",
            "slug": "Kansas_City_Chiefs",
            "position": "DEF",
            "team": "KC"
        },
        "WAS": {
            "full_name": "Washington Commanders",
            "first_name": "Washington",
            "last_name": "Commanders",
            "slug": "Washington_Commanders",
            "position": "DEF",
            "team": "WAS"
        }
    }


@pytest.fixture
def empty_players_list():
    """Empty players list for testing edge cases."""
    return {}


@pytest.fixture
def mock_fetch_players():
    """Mock the fetch_players service function."""
    with patch('patriot_center_backend.services.players.fetch_players') as mock:
        yield mock