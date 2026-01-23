"""Unit tests for validators module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.managers.validators import (
    ValidationError,
    validate_caching_preconditions,
    validate_matchup_data,
    validate_transaction,
)


@pytest.fixture
def mock_manager_cache():
    """Create a sample manager cache for testing.

    Returns:
        Sample manager cache
    """
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
        # 12 teams
        weekly_roster_ids = {i: f"Manager {i}" for i in range(1, 13)}
        year = "2023"
        week = "1"

        # Should not raise any exception
        validate_caching_preconditions(weekly_roster_ids, year, week)


class TestValidateMatchupData:
    """Test validate_matchup_data function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_cache):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`

        Args:
            mock_manager_cache: A mock manager cache.

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.managers.validators"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
        ):
            self.mock_manager_cache = mock_manager_cache
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache

            yield

    def test_valid_matchup_data_win(self):
        """Test with valid win matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert result == ""

    def test_valid_matchup_data_loss(self):
        """Test with valid loss matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 100.0,
            "points_against": 120.5,
        }

        result = validate_matchup_data(matchup_data)

        assert result == ""

    def test_valid_matchup_data_tie(self):
        """Test with valid tie matchup data - should return empty string."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "tie",
            "points_for": 115.5,
            "points_against": 115.5,
        }

        result = validate_matchup_data(matchup_data)

        assert result == ""

    def test_empty_matchup_data(self):
        """Test with empty matchup data - should return 'Empty'."""
        matchup_data = {}

        result = validate_matchup_data(matchup_data)

        assert result == "Empty"

    def test_none_matchup_data(self):
        """Test with None matchup data - should return 'Empty'."""
        matchup_data = None

        result = validate_matchup_data(matchup_data)

        assert result == "Empty"

    def test_missing_opponent_manager(self):
        """Test with missing opponent_manager - should return warning."""
        matchup_data = {
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "no opponent_data" in result

    def test_empty_opponent_manager(self):
        """Test with empty opponent_manager - should return warning."""
        matchup_data = {
            "opponent_manager": "",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "no opponent_data" in result

    def test_invalid_opponent_manager(self):
        """Test with opponent not in cache - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 999",
            "result": "win",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid manager" in result
        assert "Manager 999" in result

    def test_zero_points_for(self):
        """Test with zero points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 0.0,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid points_for" in result

    def test_negative_points_for(self):
        """Test with negative points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": -10.0,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid points_for" in result

    def test_zero_points_against(self):
        """Test with zero points_against - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": 0.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid points_against" in result

    def test_negative_points_against(self):
        """Test with negative points_against - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": -10.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid points_against" in result

    def test_missing_result(self):
        """Test with missing result - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "no result" in result

    def test_empty_result(self):
        """Test with empty result - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "no result" in result

    def test_invalid_result(self):
        """Test with invalid result value - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "victory",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "invalid result" in result
        assert "victory" in result

    def test_win_with_lower_points(self):
        """Test win result with lower points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "win",
            "points_for": 100.0,
            "points_against": 120.5,
        }

        result = validate_matchup_data(matchup_data)

        assert "result is win but points_against" in result

    def test_loss_with_higher_points(self):
        """Test loss result with higher points_for - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "loss",
            "points_for": 120.5,
            "points_against": 100.0,
        }

        result = validate_matchup_data(matchup_data)

        assert "result is loss but points_for" in result

    def test_tie_with_unequal_points(self):
        """Test tie result with unequal points - should return warning."""
        matchup_data = {
            "opponent_manager": "Manager 2",
            "result": "tie",
            "points_for": 120.5,
            "points_against": 100.0,
        }

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
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is True

    def test_valid_add_or_drop_transaction(self):
        """Test with valid add_or_drop transaction - should return True."""
        transaction = {"status": "complete", "type": "waiver"}
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(
            transaction, "add_or_drop", weekly_roster_ids
        )
        assert result is True

    def test_failed_transaction(self):
        """Test with failed transaction - should return False."""
        transaction = {
            "status": "failed",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is False

    def test_incomplete_transaction(self, caplog: pytest.LogCaptureFixture):
        """Test with incomplete transaction - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "pending",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "Unexpected transaction status" in caplog.text
        assert "pending" in caplog.text

        assert result is False

    def test_invalid_transaction_type(self, caplog: pytest.LogCaptureFixture):
        """Test with incomplete transaction type - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {"status": "complete", "type": "unknown"}
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "unknown", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "Unexpected transaction type" in caplog.text
        assert "unknown" in caplog.text

        assert result is False

    def test_trade_missing_transaction_id(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test trade without transaction_id - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "complete",
            "type": "trade",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "missing transaction_id" in caplog.text

        assert result is False

    def test_trade_missing_roster_ids(self, caplog: pytest.LogCaptureFixture):
        """Test trade without roster_ids - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "adds": {"player1": 1},
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "missing roster_ids" in caplog.text

        assert result is False

    def test_trade_single_roster(self, caplog: pytest.LogCaptureFixture):
        """Test trade with only one roster - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1],
            "adds": {"player1": 1},
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "missing roster_ids" in caplog.text

        assert result is False

    def test_trade_missing_adds(self, caplog: pytest.LogCaptureFixture):
        """Test trade without adds - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "drops": {"player2": 2},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "missing adds/drops" in caplog.text

        assert result is False

    def test_trade_missing_drops(self, caplog: pytest.LogCaptureFixture):
        """Test trade without drops - should return False.

        Args:
            caplog: pytest.LogCaptureFixture
        """
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [1, 2],
            "adds": {"player1": 1},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)

        # Verify warning was printed for incorrect data
        assert "missing adds/drops" in caplog.text

        assert result is False

    def test_trade_no_relevant_rosters(self):
        """Test trade with no rosters for caching session should be False."""
        transaction = {
            "status": "complete",
            "type": "trade",
            "transaction_id": "12345",
            "roster_ids": [3, 4],
            "adds": {"player1": 3},
            "drops": {"player2": 4},
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
            "drops": {"player2": 4},
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
            "drops": {"player3": 2, "player4": 3},
        }
        weekly_roster_ids = {1: "Manager 1", 2: "Manager 2", 3: "Manager 3"}

        result = validate_transaction(transaction, "trade", weekly_roster_ids)
        assert result is True
