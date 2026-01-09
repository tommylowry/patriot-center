"""
Unit tests for validators module.

Tests all validation functions with both good and bad scenarios.
"""
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.validators import (
    ValidationError,
    validate_caching_preconditions,
    validate_transaction,
)


@pytest.fixture
def mock_manager_cache():
    """Create a sample manager cache for testing."""
    return {"Manager 1": {}, "Manager 2": {}}


class TestValidateCachingPreconditions:
    """Test validate_caching_preconditions function."""

    def test_valid_preconditions(self):
        """Test with valid preconditions - should not raise."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        year = "2023"
        week = "1"

        # Should not raise any exception
        validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_empty_roster_ids(self):
        """Test with empty roster IDs - should raise ValidationError."""
        weekly_roster_ids = {}
        year = "2023"
        week = "1"

        with pytest.raises(ValidationError, match="No roster IDs cached"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_odd_number_of_rosters(self):
        """Test with odd number of rosters - should raise ValidationError."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2", 3: "Manager 3"}
        year = "2023"
        week = "1"

        with pytest.raises(ValidationError, match="Odd number of roster IDs"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_missing_year(self):
        """Test with missing year - should raise ValidationError."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        year = None
        week = "1"

        with pytest.raises(ValidationError, match="Year not set"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_empty_year_string(self):
        """Test with empty year string - should raise ValidationError."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        year = ""
        week = "1"

        with pytest.raises(ValidationError, match="Year not set"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_missing_week(self):
        """Test with missing week - should raise ValidationError."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        year = "2023"
        week = None

        with pytest.raises(ValidationError, match="Week not set"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_empty_week_string(self):
        """Test with empty week string - should raise ValidationError."""
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}
        year = "2023"
        week = ""

        with pytest.raises(ValidationError, match="Week not set"):
            validate_caching_preconditions(weekly_roster_ids, year, week)

    def test_large_even_number_of_rosters(self):
        """Test with large even number of rosters - should pass."""
        weekly_roster_ids = {i: f"Manager {i}" for i in range(1, 13)}  # 12 teams
        year = "2023"
        week = "1"

        # Should not raise any exception
        validate_caching_preconditions(weekly_roster_ids, year, week)


class TestValidateMatchupData:
    """Test validate_matchup_data function."""

    def test_valid_matchup_data_win(self, mock_manager_cache):
        """Test with valid win matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert result == ""

    def test_valid_matchup_data_loss(self, mock_manager_cache):
        """Test with valid loss matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 100.0,
            "points_against": 120.5
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert result == ""

    def test_valid_matchup_data_tie(self, mock_manager_cache):
        """Test with valid tie matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "tie",
            "points_for": 115.5,
            "points_against": 115.5
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert result == ""

    def test_empty_matchup_data(self, mock_manager_cache):
        """Test with empty matchup data - should return 'Empty'."""
        matchup_data = {}
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert result == "Empty"

    def test_none_matchup_data(self, mock_manager_cache):
        """Test with None matchup data - should return 'Empty'."""
        matchup_data = None
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert result == "Empty"

    def test_missing_opponent_manager(self, mock_manager_cache):
        """Test with missing opponent_manager - should return warning."""
        matchup_data = {
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "no opponent_data" in result

    def test_empty_opponent_manager(self, mock_manager_cache):
        """Test with empty opponent_manager - should return warning."""
        matchup_data = {
            "opponent_manager": "",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "no opponent_data" in result

    def test_invalid_opponent_manager(self, mock_manager_cache):
        """Test with opponent not in cache - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 999",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid manager" in result
        assert "Manager 999" in result

    def test_zero_points_for(self, mock_manager_cache):
        """Test with zero points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 0.0,
            "points_against": 100.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid points_for" in result

    def test_negative_points_for(self, mock_manager_cache):
        """Test with negative points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": -10.0,
            "points_against": 100.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid points_for" in result

    def test_zero_points_against(self, mock_manager_cache):
        """Test with zero points_against - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": 0.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid points_against" in result

    def test_negative_points_against(self, mock_manager_cache):
        """Test with negative points_against - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": -10.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid points_against" in result

    def test_missing_result(self, mock_manager_cache):
        """Test with missing result - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "no result" in result

    def test_empty_result(self, mock_manager_cache):
        """Test with empty result - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "",
            "points_for": 120.5,
            "points_against": 100.0
        }

        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "no result" in result

    def test_invalid_result(self, mock_manager_cache):
        """Test with invalid result value - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "victory",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "invalid result" in result
        assert "victory" in result

    def test_win_with_lower_points(self, mock_manager_cache):
        """Test win result with lower points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": 120.5
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "result is win but points_against" in result

    def test_loss_with_higher_points(self, mock_manager_cache):
        """Test loss result with higher points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "result is loss but points_for" in result

    def test_tie_with_unequal_points(self, mock_manager_cache):
        """Test tie result with unequal points - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "tie",
            "points_for": 120.5,
            "points_against": 100.0
        }
        
        with patch('patriot_center_backend.managers.validators.MANAGER_CACHE', mock_manager_cache):
            from patriot_center_backend.managers.validators import validate_matchup_data

            result = validate_matchup_data(matchup_data)
        
        assert "result is tie but points_for" in result


class TestValidateTransaction:
    """Test validate_transaction function."""

    def test_valid_trade_transaction(self):
        """Test with valid trade transaction - should return True."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is True

    def test_valid_add_or_drop_transaction(self):
        """Test with valid add_or_drop transaction - should return True."""
        transaction = {
            "status": "complete",
            "type": "waiver"
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "add_or_drop", weekly_roster_ids)
        assert result is True

    def test_failed_transaction(self):
        """Test with failed transaction - should return False."""
        transaction = {
            "status": "failed",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_incomplete_transaction(self):
        """Test with incomplete transaction - should return False."""
        transaction = {
            "status": "pending",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_invalid_transaction_type(self):
        """Test with invalid transaction type - should return False."""
        transaction = {
            "status": "complete",
            "type": "unknown"
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "unknown", weekly_roster_ids)
        assert result is False

    def test_trade_missing_transaction_id(self):
        """Test trade without transaction_id - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_missing_roster_ids(self):
        """Test trade without roster_ids - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_single_roster(self):
        """Test trade with only one roster - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1],
            "adds": {"player1": 1},
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_missing_adds(self):
        """Test trade without adds - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "drops": {"player2": 2}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_missing_drops(self):
        """Test trade without drops - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_no_relevant_rosters(self):
        """Test trade with no rosters relevant to caching session - should return False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [3, 4],
            "adds": {"player1": 3},
            "drops": {"player2": 4}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_trade_partially_relevant_rosters(self):
        """Test trade with one relevant roster - should return True."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 4],
            "adds": {"player1": 1},
            "drops": {"player2": 4}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is True

    def test_multi_team_trade(self):
        """Test trade with more than 2 teams - should return True if valid."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2, 3],
            "adds": {"player1": 1, "player2": 2},
            "drops": {"player3": 2, "player4": 3}
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2", 3: "Manager 3"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is True
