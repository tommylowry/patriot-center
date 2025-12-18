"""
Unit tests for app.py - Flask routes and request handling.
"""
import pytest
from unittest.mock import patch, MagicMock
import json


class TestArgumentParsing:
    """Test the parse_arguments function with success and failure cases."""

    # === SUCCESS CASES ===

    def test_parse_no_arguments(self, flask_app):
        """Test parsing with no arguments returns all nulls."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments(None, None, None)
        assert result == (None, None, None)

    def test_parse_single_year(self, flask_app):
        """Test parsing a single valid year."""
        from patriot_center_backend.app import parse_arguments
        # 2024 should be in LEAGUE_IDS
        result = parse_arguments("2024", None, None)
        assert result == (2024, None, None)

    def test_parse_year_and_week(self, flask_app):
        """Test parsing year and week together."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("2024", "5", None)
        assert result == (2024, 5, None)

    def test_parse_year_and_manager(self, flask_app):
        """Test parsing year and manager (skip week)."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("2024", "Tommy", None)
        assert result == (2024, None, "Tommy")

    def test_parse_all_three_arguments(self, flask_app):
        """Test parsing all three arguments in order."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("2024", "Tommy", "5")
        assert result == (2024, 5, "Tommy")

    def test_parse_manager_only(self, flask_app):
        """Test parsing manager name only."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("Tommy", None, None)
        assert result == (None, None, "Tommy")

    def test_parse_year_and_manager_different_order(self, flask_app):
        """Test parsing works regardless of argument order."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("Tommy", "2024", None)
        assert result == (2024, None, "Tommy")

    def test_parse_week_boundary_min(self, flask_app):
        """Test week boundary at minimum (1)."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("2024", "1", None)
        assert result == (2024, 1, None)

    def test_parse_week_boundary_max(self, flask_app):
        """Test week boundary at maximum (17)."""
        from patriot_center_backend.app import parse_arguments
        result = parse_arguments("2024", "17", None)
        assert result == (2024, 17, None)

    # === FAILURE CASES ===

    def test_fail_week_without_year(self, flask_app):
        """Test that providing week without year raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Week provided without a corresponding year"):
            parse_arguments("5", None, None)

    def test_fail_week_without_year_with_manager(self, flask_app):
        """Test week without year fails even when manager is present."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Week provided without a corresponding year"):
            parse_arguments("Tommy", "5", None)

    def test_fail_multiple_years(self, flask_app):
        """Test that providing multiple years raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Multiple year arguments provided"):
            parse_arguments("2024", "2023", None)

    def test_fail_multiple_weeks(self, flask_app):
        """Test that providing multiple weeks raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Multiple week arguments provided"):
            parse_arguments("2024", "5", "10")

    def test_fail_multiple_managers(self, flask_app):
        """Test that providing multiple managers raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Multiple manager arguments provided"):
            parse_arguments("Tommy", "Cody", None)

    def test_fail_invalid_manager_name(self, flask_app):
        """Test that an unrecognized manager name raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Invalid argument provided: InvalidManager"):
            parse_arguments("InvalidManager", None, None)

    def test_fail_invalid_integer(self, flask_app):
        """Test that an integer not matching year or week range raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        # 99 is not a valid year and not in week range 1-17
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("99", None, None)

    def test_fail_week_too_high(self, flask_app):
        """Test that week > 17 raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("2024", "18", None)

    def test_fail_week_zero(self, flask_app):
        """Test that week 0 raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("2024", "0", None)

    def test_fail_invalid_year(self, flask_app):
        """Test that a year not in LEAGUE_IDS raises ValueError."""
        from patriot_center_backend.app import parse_arguments
        # Assuming 1999 is not in LEAGUE_IDS (pre-league)
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("1999", None, None)


class TestFlattenDict:
    """Test the _flatten_dict helper function."""

    def test_flatten_empty_dict(self, flask_app):
        """Test flattening an empty dict."""
        from patriot_center_backend.app import _flatten_dict
        result = _flatten_dict({})
        assert result == {}

    def test_flatten_flat_dict(self, flask_app):
        """Test flattening an already-flat dict."""
        from patriot_center_backend.app import _flatten_dict
        input_dict = {"a": 1, "b": 2, "c": 3}
        result = _flatten_dict(input_dict)
        assert result == input_dict

    def test_flatten_nested_dict(self, flask_app):
        """Test flattening a nested dict."""
        from patriot_center_backend.app import _flatten_dict
        input_dict = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        result = _flatten_dict(input_dict)
        assert result == {"level1.level2.level3": "value"}

    def test_flatten_mixed_dict(self, flask_app):
        """Test flattening a dict with mixed flat and nested keys."""
        from patriot_center_backend.app import _flatten_dict
        input_dict = {
            "flat": 1,
            "nested": {
                "key": 2
            }
        }
        result = _flatten_dict(input_dict)
        assert result == {
            "flat": 1,
            "nested.key": 2
        }

    def test_flatten_custom_separator(self, flask_app):
        """Test flattening with a custom separator."""
        from patriot_center_backend.app import _flatten_dict
        input_dict = {
            "a": {
                "b": "value"
            }
        }
        result = _flatten_dict(input_dict, sep="_")
        assert result == {"a_b": "value"}

    def test_flatten_none_input(self, flask_app):
        """Test that None input returns empty dict."""
        from patriot_center_backend.app import _flatten_dict
        result = _flatten_dict(None)
        assert result == {}

    def test_flatten_non_dict_input(self, flask_app):
        """Test that non-dict input returns empty dict."""
        from patriot_center_backend.app import _flatten_dict
        result = _flatten_dict("not a dict")
        assert result == {}


class TestToRecords:
    """Test the _to_records helper function."""

    def test_to_records_empty_dict(self, flask_app):
        """Test converting empty dict to records."""
        from patriot_center_backend.app import _to_records
        result = _to_records({})
        assert result == []

    def test_to_records_flat_dict(self, flask_app):
        """Test converting flat dict to records."""
        from patriot_center_backend.app import _to_records
        input_data = {
            "player1": {"points": 10},
            "player2": {"points": 20}
        }
        result = _to_records(input_data)
        assert len(result) == 2
        assert {"key": "player1", "points": 10} in result
        assert {"key": "player2", "points": 20} in result

    def test_to_records_custom_key_name(self, flask_app):
        """Test converting with custom key name."""
        from patriot_center_backend.app import _to_records
        input_data = {
            "player1": {"points": 10}
        }
        result = _to_records(input_data, key_name="player")
        assert result[0] == {"player": "player1", "points": 10}

    def test_to_records_nested_values(self, flask_app):
        """Test converting dict with nested values."""
        from patriot_center_backend.app import _to_records
        input_data = {
            "player1": {
                "stats": {
                    "points": 10
                }
            }
        }
        result = _to_records(input_data)
        # Should flatten nested stats
        assert "key" in result[0]
        assert result[0]["key"] == "player1"
        assert "stats.points" in result[0]
        assert result[0]["stats.points"] == 10

    def test_to_records_list_input(self, flask_app):
        """Test converting a list to records."""
        from patriot_center_backend.app import _to_records
        input_data = [{"points": 10}, {"points": 20}]
        result = _to_records(input_data)
        assert len(result) == 2
        assert {"points": 10} in result
        assert {"points": 20} in result

    def test_to_records_scalar_value(self, flask_app):
        """Test converting a scalar value."""
        from patriot_center_backend.app import _to_records
        result = _to_records(42)
        assert result == [{"value": 42}]


class TestFlaskRoutes:
    """Test Flask API endpoint routes."""

    def test_index_route(self, flask_client):
        """Test the root index route."""
        response = flask_client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "service" in data
        assert data["service"] == "Patriot Center Backend"
        assert "endpoints" in data

    def test_ping_route(self, flask_client):
        """Test the ping health check."""
        response = flask_client.get('/ping')
        assert response.status_code == 200
        assert b"pong" in response.data

    def test_health_route(self, flask_client):
        """Test the health check endpoint."""
        response = flask_client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    @patch('patriot_center_backend.services.managers.fetch_starters')
    def test_get_starters_no_params(self, mock_fetch, flask_client):
        """Test getting starters with no parameters."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters')
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(manager=None, season=None, week=None)

    @patch('patriot_center_backend.services.managers.fetch_starters')
    def test_get_starters_with_year(self, mock_fetch, flask_client):
        """Test getting starters filtered by year."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters/2024')
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(manager=None, season=2024, week=None)

    @patch('patriot_center_backend.services.managers.fetch_starters')
    def test_get_starters_json_format(self, mock_fetch, flask_client):
        """Test getting starters in JSON format."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters?format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return raw JSON, not flattened
        assert isinstance(data, dict)

    @patch('patriot_center_backend.services.aggregated_data.fetch_aggregated_players')
    def test_get_aggregated_players(self, mock_fetch, flask_client, sample_aggregated_player_data):
        """Test the aggregated players endpoint."""
        mock_fetch.return_value = sample_aggregated_player_data

        response = flask_client.get('/get_aggregated_players/2024/Tommy')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)  # Should be converted to records

    @patch('patriot_center_backend.services.aggregated_data.fetch_aggregated_managers')
    def test_get_aggregated_managers(self, mock_fetch, flask_client, sample_aggregated_manager_data):
        """Test the aggregated managers endpoint."""
        mock_fetch.return_value = sample_aggregated_manager_data

        response = flask_client.get('/get_aggregated_managers/Amon-Ra_St._Brown')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    @patch('patriot_center_backend.services.aggregated_data.fetch_aggregated_managers')
    def test_get_aggregated_managers_with_filters(self, mock_fetch, flask_client, sample_aggregated_manager_data):
        """Test aggregated managers with year and week filters."""
        mock_fetch.return_value = sample_aggregated_manager_data

        response = flask_client.get('/get_aggregated_managers/Josh_Allen/2024/5')
        assert response.status_code == 200
        # Should pass underscored name as is, parse year and week
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[1]['player'] == "Josh Allen"  # Underscores converted to spaces
        assert call_args[1]['season'] == 2024
        assert call_args[1]['week'] == 5

    def test_get_aggregated_managers_invalid_params(self, flask_client):
        """Test that invalid parameters return 400 error."""
        response = flask_client.get('/get_aggregated_managers/Player/5')  # Week without year
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_cors_headers(self, flask_client):
        """Test that CORS headers are set."""
        response = flask_client.get('/')
        # Flask-CORS should add these headers
        assert 'Access-Control-Allow-Origin' in response.headers


class TestErrorHandling:
    """Test error handling in the Flask app."""

    def test_invalid_route(self, flask_client):
        """Test accessing an invalid route returns 404."""
        response = flask_client.get('/invalid_route_12345')
        assert response.status_code == 404


class TestListPlayersEndpoint:
    """Test /players/list endpoint functionality."""

    def test_list_players_returns_success(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that /players/list returns 200 status code."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list')
        assert response.status_code == 200

    def test_list_players_default_format_returns_list(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that default format returns a list of records."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list')
        data = json.loads(response.data)

        assert isinstance(data, list)
        assert len(data) > 0
        # Verify records format with 'name' key
        if len(data) > 0:
            assert 'name' in data[0]

    def test_list_players_json_format(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that format=json returns raw dictionary."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list?format=json')
        data = json.loads(response.data)

        assert isinstance(data, dict)
        # Should return the raw player dict with IDs as keys
        assert '7547' in data or len(data) == 0

    def test_list_players_empty_cache(self, flask_client, mock_fetch_players, empty_players_list):
        """Test that empty player cache returns empty list."""
        mock_fetch_players.return_value = empty_players_list
        response = flask_client.get('/players/list')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_players_calls_fetch_players_service(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that endpoint calls the fetch_players service."""
        mock_fetch_players.return_value = sample_players_list
        flask_client.get('/players/list')

        # Verify the service was called
        mock_fetch_players.assert_called_once()

    def test_list_players_uses_to_records_with_name_key(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that _to_records is called with key_name='name'."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list')
        data = json.loads(response.data)

        # Verify each record has 'name' field (from key_name parameter)
        if len(data) > 0:
            first_record = data[0]
            assert 'name' in first_record
            # Name should be the player ID (key from dict)
            assert first_record['name'] in sample_players_list.keys()

    def test_list_players_cors_headers(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that CORS headers are set for /players/list."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list')

        assert 'Access-Control-Allow-Origin' in response.headers

    def test_list_players_content_type_json(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that response content type is JSON."""
        mock_fetch_players.return_value = sample_players_list
        response = flask_client.get('/players/list')

        assert 'application/json' in response.content_type


class TestPlayersService:
    """Test services/players.py fetch_players function."""

    @patch('patriot_center_backend.services.players.load_cache')
    def test_fetch_players_calls_load_cache(self, mock_load_cache, sample_players_list):
        """Test that fetch_players calls load_cache with correct parameters."""
        from patriot_center_backend.services.players import fetch_players
        from patriot_center_backend.constants import PLAYERS_CACHE_FILE

        mock_load_cache.return_value = sample_players_list
        result = fetch_players()

        # Verify load_cache was called with correct file and players_cache flag
        mock_load_cache.assert_called_once_with(PLAYERS_CACHE_FILE, initialize_with_last_updated_info=False)

    @patch('patriot_center_backend.services.players.load_cache')
    def test_fetch_players_returns_dict(self, mock_load_cache, sample_players_list):
        """Test that fetch_players returns a dictionary."""
        from patriot_center_backend.services.players import fetch_players

        mock_load_cache.return_value = sample_players_list
        result = fetch_players()

        assert isinstance(result, dict)
        assert result == sample_players_list

    @patch('patriot_center_backend.services.players.load_cache')
    def test_fetch_players_returns_empty_dict_on_missing_cache(self, mock_load_cache):
        """Test that fetch_players returns empty dict when cache is missing."""
        from patriot_center_backend.services.players import fetch_players

        mock_load_cache.return_value = {}
        result = fetch_players()

        assert isinstance(result, dict)
        assert len(result) == 0

    @patch('patriot_center_backend.services.players.load_cache')
    def test_fetch_players_uses_players_cache_file(self, mock_load_cache, sample_players_list):
        """Test that fetch_players uses the PLAYERS_CACHE_FILE constant."""
        from patriot_center_backend.services.players import fetch_players
        from patriot_center_backend.constants import PLAYERS_CACHE_FILE

        mock_load_cache.return_value = sample_players_list
        fetch_players()

        call_args = mock_load_cache.call_args
        assert call_args[0][0] == PLAYERS_CACHE_FILE


class TestPlayersIntegration:
    """Test integration between endpoint and service layer."""

    def test_endpoint_to_service_integration(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that endpoint properly integrates with service layer."""
        mock_fetch_players.return_value = sample_players_list

        response = flask_client.get('/players/list')
        data = json.loads(response.data)

        # Verify service was called
        mock_fetch_players.assert_called_once()

        # Verify data was transformed and returned
        assert response.status_code == 200
        assert isinstance(data, list)

    def test_service_data_transforms_correctly(self, flask_client, mock_fetch_players):
        """Test that service output is correctly transformed for response."""
        # Create test data with nested structure
        test_data = {
            "123": {
                "full_name": "Test Player",
                "slug": "Test_Player",
                "position": "WR"
            }
        }
        mock_fetch_players.return_value = test_data

        response = flask_client.get('/players/list')
        data = json.loads(response.data)

        # Verify transformation happened
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == '123'
        assert data[0]['full_name'] == 'Test Player'

    def test_json_format_bypasses_transformation(self, flask_client, mock_fetch_players, sample_players_list):
        """Test that format=json returns raw data without transformation."""
        mock_fetch_players.return_value = sample_players_list

        response = flask_client.get('/players/list?format=json')
        data = json.loads(response.data)

        # Should return raw dict, not transformed to list
        assert isinstance(data, dict)
        assert data == sample_players_list


class TestValidOptionsEndpoint:
    """Test /valid_options endpoint functionality."""

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_no_params(self, mock_service_class, flask_client):
        """Test /valid_options with no parameters returns all options."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2021", "2022", "2023", "2024"],
            "weeks": ["1", "2", "3", "4", "5"],
            "positions": ["QB", "RB", "WR"],
            "managers": ["Cody", "Mike", "Tommy"]
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify all keys present
        assert "years" in data
        assert "weeks" in data
        assert "positions" in data
        assert "managers" in data

        # Verify lists are present
        assert data["years"] == ["2021", "2022", "2023", "2024"]
        assert data["weeks"] == ["1", "2", "3", "4", "5"]
        assert data["managers"] == ["Cody", "Mike", "Tommy"]
        assert data["positions"] == ["QB", "RB", "WR"]

        # Verify service was instantiated with no filters
        mock_service_class.assert_called_once_with(None, None, None, None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_with_year(self, mock_service_class, flask_client):
        """Test /valid_options filtered by year."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2024"],
            "weeks": ["1", "2", "3"],
            "positions": ["QB", "RB"],
            "managers": ["Tommy"]
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options/2024')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["years"] == ["2024"]
        assert data["weeks"] == ["1", "2", "3"]

        # Verify service was instantiated with year
        mock_service_class.assert_called_once_with("2024", None, None, None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_with_year_and_week(self, mock_service_class, flask_client):
        """Test /valid_options filtered by year and week."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2024"],
            "weeks": ["5"],
            "positions": ["QB", "WR"],
            "managers": ["Mike", "Tommy"]
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options/2024/5')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["years"] == ["2024"]
        assert data["weeks"] == ["5"]
        assert data["managers"] == ["Mike", "Tommy"]

        # Verify service was instantiated with year and week
        mock_service_class.assert_called_once_with("2024", "5", None, None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_with_all_three_args(self, mock_service_class, flask_client):
        """Test /valid_options with year, week, and manager."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2024"],
            "weeks": ["5"],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options/2024/Tommy/5')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["positions"] == ["QB"]

        # Verify service was instantiated with 3 args
        mock_service_class.assert_called_once_with("2024", "Tommy", "5", None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_with_manager_only(self, mock_service_class, flask_client):
        """Test /valid_options filtered by manager only."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2023", "2024"],
            "weeks": ["1", "2", "3", "4", "5"],
            "positions": ["QB", "RB", "WR"],
            "managers": ["Tommy"]
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options/Tommy')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["managers"] == ["Tommy"]
        assert data["years"] == ["2023", "2024"]

        mock_service_class.assert_called_once_with("Tommy", None, None, None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_with_player_name(self, mock_service_class, flask_client):
        """Test /valid_options with player name (URL encoded)."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2024"],
            "weeks": ["1", "2"],
            "positions": ["QB"],
            "managers": ["Tommy"]
        }
        mock_service_class.return_value = mock_instance

        # Player name with spaces encoded as underscores
        response = flask_client.get('/valid_options/Josh_Allen')
        assert response.status_code == 200

        mock_service_class.assert_called_once_with("Josh_Allen", None, None, None)

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_returns_empty_lists_when_no_matches(self, mock_service_class, flask_client):
        """Test /valid_options returns empty lists when no data matches."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": [],
            "weeks": [],
            "positions": [],
            "managers": []
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options/2019/99')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["years"] == []
        assert data["weeks"] == []
        assert data["positions"] == []
        assert data["managers"] == []

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_preserves_non_list_values(self, mock_service_class, flask_client):
        """Test that non-list values in response are preserved."""
        mock_instance = MagicMock()
        mock_instance.get_valid_options.return_value = {
            "years": ["2024"],
            "weeks": ["1"],
            "positions": ["QB"],
            "managers": ["Tommy"],
            "metadata": {"count": 5}  # Non-list value
        }
        mock_service_class.return_value = mock_instance

        response = flask_client.get('/valid_options')
        data = json.loads(response.data)

        # Verify data is present
        assert data["years"] == ["2024"]

        # Non-list values should be preserved
        assert data["metadata"] == {"count": 5}

    def test_valid_options_cors_headers(self, flask_client):
        """Test that CORS headers are set for /valid_options."""
        response = flask_client.get('/valid_options')
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_valid_options_content_type(self, flask_client):
        """Test that response content type is JSON."""
        response = flask_client.get('/valid_options')
        assert 'application/json' in response.content_type

    @patch('patriot_center_backend.services.valid_options.ValidOptionsService')
    def test_valid_options_error_handling(self, mock_service_class, flask_client):
        """Test that ValueError from ValidOptionsService returns 400."""
        mock_service_class.side_effect = ValueError("Week filter cannot be applied without a Year filter.")

        response = flask_client.get('/valid_options/5')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Week filter cannot be applied without a Year filter" in data["error"]


class TestPlayerManagerAggregationEndpoint:
    """Test /get_player_manager_aggregation endpoint functionality."""

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_basic(self, mock_fetch, flask_client):
        """Test basic player-manager aggregation endpoint."""
        mock_fetch.return_value = {
            "Tommy": {
                "total_points": 45.5,
                "num_games_started": 3,
                "ffWAR": 5.2,
                "position": "RB"
            }
        }

        response = flask_client.get('/get_player_manager_aggregation/Christian_McCaffrey/Tommy')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert isinstance(data, list)
        # Verify service was called with correct parameters
        mock_fetch.assert_called_once_with(
            player="Christian McCaffrey",
            manager="Tommy",
            season=None,
            week=None
        )

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_with_season(self, mock_fetch, flask_client):
        """Test player-manager aggregation with season filter."""
        mock_fetch.return_value = {
            "Tommy": {"total_points": 30.0, "num_games_started": 2, "ffWAR": 3.5, "position": "WR"}
        }

        response = flask_client.get('/get_player_manager_aggregation/Amon-Ra_St._Brown/Tommy/2024')
        assert response.status_code == 200

        # Verify season was passed correctly
        call_args = mock_fetch.call_args[1]
        assert call_args['player'] == "Amon-Ra St. Brown"
        assert call_args['manager'] == "Tommy"
        assert call_args['season'] == "2024"
        assert call_args['week'] is None

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_with_season_and_week(self, mock_fetch, flask_client):
        """Test player-manager aggregation with both season and week filters."""
        mock_fetch.return_value = {
            "Tommy": {"total_points": 18.5, "num_games_started": 1, "ffWAR": 2.1, "position": "QB"}
        }

        response = flask_client.get('/get_player_manager_aggregation/Josh_Allen/Tommy/2024/5')
        assert response.status_code == 200

        # Verify all parameters were passed
        call_args = mock_fetch.call_args[1]
        assert call_args['player'] == "Josh Allen"
        assert call_args['manager'] == "Tommy"
        assert call_args['season'] == "2024"
        assert call_args['week'] == "5"

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_empty_result(self, mock_fetch, flask_client):
        """Test player-manager aggregation returns empty when no data."""
        mock_fetch.return_value = {}

        response = flask_client.get('/get_player_manager_aggregation/Unknown_Player/Tommy')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert isinstance(data, list)
        assert len(data) == 0

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_json_format(self, mock_fetch, flask_client):
        """Test player-manager aggregation with JSON format parameter."""
        mock_fetch.return_value = {
            "Tommy": {"total_points": 45.5, "num_games_started": 3, "ffWAR": 5.2, "position": "RB"}
        }

        response = flask_client.get('/get_player_manager_aggregation/Player/Tommy?format=json')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should return raw dict when format=json
        assert isinstance(data, dict)
        assert "Tommy" in data

    @patch('patriot_center_backend.services.aggregated_data.fetch_player_manager_aggregation')
    def test_player_manager_aggregation_handles_apostrophe(self, mock_fetch, flask_client):
        """Test player name with apostrophe is properly decoded."""
        mock_fetch.return_value = {"Mike": {"total_points": 20.0, "num_games_started": 1, "ffWAR": 1.5, "position": "RB"}}

        response = flask_client.get('/get_player_manager_aggregation/D%27Andre_Swift/Mike')
        assert response.status_code == 200

        # Verify player name was converted correctly
        call_args = mock_fetch.call_args[1]
        assert call_args['player'] == "D'Andre Swift"

    def test_player_manager_aggregation_cors_headers(self, flask_client):
        """Test that CORS headers are set."""
        response = flask_client.get('/get_player_manager_aggregation/Player/Manager')
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_player_manager_aggregation_content_type(self, flask_client):
        """Test that response content type is JSON."""
        response = flask_client.get('/get_player_manager_aggregation/Player/Manager')
        assert 'application/json' in response.content_type


class TestManagerEndpoints:
    """Test manager-related API endpoints."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_list_managers_success(self, mock_manager_class, flask_client):
        """Test /get/managers/list endpoint returns manager list."""
        mock_instance = MagicMock()
        mock_instance.get_managers_list.return_value = {
            "managers": [
                {
                    "name": "Tommy",
                    "user_id": "123",
                    "years_active": ["2024"],
                    "total_trades": 10,
                    "overall_record": "8-6-0"
                },
                {
                    "name": "Mike",
                    "user_id": "456",
                    "years_active": ["2024"],
                    "total_trades": 5,
                    "overall_record": "6-8-0"
                }
            ]
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/get/managers/list')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "managers" in data
        assert len(data["managers"]) == 2
        assert data["managers"][0]["name"] == "Tommy"
        mock_instance.get_managers_list.assert_called_once()

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_list_managers_error(self, mock_manager_class, flask_client):
        """Test /get/managers/list handles errors."""
        mock_instance = MagicMock()
        mock_instance.get_managers_list.side_effect = ValueError("Cache error")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/get/managers/list')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_summary_no_year(self, mock_manager_class, flask_client):
        """Test /api/managers/<name>/summary endpoint without year filter."""
        mock_instance = MagicMock()
        mock_instance.get_manager_summary.return_value = {
            "manager_name": "Tommy",
            "user_id": "123",
            "matchup_data": {"overall": {"record": "8-6-0"}},
            "transactions": {"trades": {"total": 10}},
            "overall_data": {"playoff_appearances": 5},
            "head_to_head": {}
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/summary')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["manager_name"] == "Tommy"
        assert "matchup_data" in data
        mock_instance.get_manager_summary.assert_called_once_with("Tommy", None)

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_summary_with_year(self, mock_manager_class, flask_client):
        """Test /api/managers/<name>/summary/<year> endpoint with year filter."""
        mock_instance = MagicMock()
        mock_instance.get_manager_summary.return_value = {
            "manager_name": "Tommy",
            "matchup_data": {"overall": {"record": "8-6-0"}}
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/summary/2024')
        assert response.status_code == 200
        mock_instance.get_manager_summary.assert_called_once_with("Tommy", "2024")

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_summary_invalid_manager(self, mock_manager_class, flask_client):
        """Test manager summary returns 400 for invalid manager."""
        mock_instance = MagicMock()
        mock_instance.get_manager_summary.side_effect = ValueError("Manager not found")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/InvalidManager/summary')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_yearly_data_success(self, mock_manager_class, flask_client):
        """Test /api/managers/<name>/yearly/<year> endpoint."""
        mock_instance = MagicMock()
        mock_instance.get_manager_yearly_data.return_value = {
            "manager_name": "Tommy",
            "year": "2024",
            "matchup_data": {
                "overall": {
                    "weekly_scores": [
                        {"week": "1", "points_for": 120.5, "opponent": "Mike"}
                    ]
                }
            },
            "transactions": {"trades": {"by_week": []}}
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/yearly/2024')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["manager_name"] == "Tommy"
        assert data["year"] == "2024"
        mock_instance.get_manager_yearly_data.assert_called_once_with("Tommy", "2024")

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_yearly_data_invalid_year(self, mock_manager_class, flask_client):
        """Test yearly data returns 400 for invalid year."""
        mock_instance = MagicMock()
        mock_instance.get_manager_yearly_data.side_effect = ValueError("Year not found")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/yearly/2099')
        assert response.status_code == 400

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_head_to_head_no_year(self, mock_manager_class, flask_client):
        """Test head-to-head endpoint without year filter."""
        mock_instance = MagicMock()
        mock_instance.get_head_to_head.return_value = {
            "manager_1": {"name": "Tommy", "wins": 5},
            "manager_2": {"name": "Mike", "wins": 3},
            "matchup_history": [],
            "trades_between": {"total": 2}
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/head-to-head/Mike')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["manager_1"]["name"] == "Tommy"
        assert data["manager_2"]["name"] == "Mike"
        mock_instance.get_head_to_head.assert_called_once_with("Tommy", "Mike", None)

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_head_to_head_with_year(self, mock_manager_class, flask_client):
        """Test head-to-head endpoint with year filter."""
        mock_instance = MagicMock()
        mock_instance.get_head_to_head.return_value = {
            "manager_1": {"name": "Tommy"},
            "manager_2": {"name": "Mike"}
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/head-to-head/Mike/2024')
        assert response.status_code == 200
        mock_instance.get_head_to_head.assert_called_once_with("Tommy", "Mike", "2024")

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_head_to_head_invalid_manager(self, mock_manager_class, flask_client):
        """Test head-to-head returns 400 for invalid manager."""
        mock_instance = MagicMock()
        mock_instance.get_head_to_head.side_effect = ValueError("Manager not found")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/head-to-head/Invalid')
        assert response.status_code == 400

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_transactions_default_params(self, mock_manager_class, flask_client):
        """Test transactions endpoint with default parameters."""
        mock_instance = MagicMock()
        mock_instance.get_manager_transactions.return_value = {
            "manager_name": "Tommy",
            "total_count": 50,
            "transactions": [
                {"type": "trade", "year": "2024", "week": "1"}
            ]
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/transactions')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["manager_name"] == "Tommy"
        assert "transactions" in data
        # Check default parameters: year=None, type=None, limit=50, offset=0
        mock_instance.get_manager_transactions.assert_called_once_with("Tommy", None, None, 50, 0)

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_transactions_with_filters(self, mock_manager_class, flask_client):
        """Test transactions endpoint with year and type filters."""
        mock_instance = MagicMock()
        mock_instance.get_manager_transactions.return_value = {
            "manager_name": "Tommy",
            "total_count": 10,
            "transactions": []
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/transactions/2024/trade/20/5')
        assert response.status_code == 200
        mock_instance.get_manager_transactions.assert_called_once_with("Tommy", "2024", "trade", 20, 5)

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_transactions_invalid_manager(self, mock_manager_class, flask_client):
        """Test transactions returns 400 for invalid manager."""
        mock_instance = MagicMock()
        mock_instance.get_manager_transactions.side_effect = ValueError("Manager not found")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/InvalidManager/transactions')
        assert response.status_code == 400

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_awards_success(self, mock_manager_class, flask_client):
        """Test /api/managers/<name>/awards endpoint."""
        mock_instance = MagicMock()
        mock_instance.get_manager_awards.return_value = {
            "manager_name": "Tommy",
            "awards": {
                "championships": 1,
                "runner_ups": 2,
                "playoff_appearances": 5,
                "highest_weekly_score": {"score": 163.5, "week": "1", "year": "2024"}
            },
            "avatar_urls": {
                "full_size": "https://example.com/avatar.jpg",
                "thumbnail": "https://example.com/thumb.jpg"
            }
        }
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/Tommy/awards')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["manager_name"] == "Tommy"
        assert "awards" in data
        assert data["awards"]["championships"] == 1
        mock_instance.get_manager_awards.assert_called_once_with("Tommy")

    @patch('patriot_center_backend.utils.manager_metadata_manager.ManagerMetadataManager')
    def test_manager_awards_invalid_manager(self, mock_manager_class, flask_client):
        """Test awards returns 400 for invalid manager."""
        mock_instance = MagicMock()
        mock_instance.get_manager_awards.side_effect = ValueError("Manager not found")
        mock_manager_class.return_value = mock_instance

        response = flask_client.get('/api/managers/InvalidManager/awards')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_manager_endpoints_cors_headers(self, flask_client):
        """Test that CORS headers are set for all manager endpoints."""
        response = flask_client.get('/get/managers/list')
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_manager_endpoints_content_type(self, flask_client):
        """Test that response content type is JSON for manager endpoints."""
        response = flask_client.get('/get/managers/list')
        assert 'application/json' in response.content_type
