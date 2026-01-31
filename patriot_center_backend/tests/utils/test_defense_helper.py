"""Unit tests for defense_helper module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.utils.defense_helper import get_defense_entries


class TestGetDefenseEntries:
    """Test get_defense_entries function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `TEAM_DEFENSE_NAMES`: mock team defense names

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.utils.defense_helper"
            ".TEAM_DEFENSE_NAMES",
            {
                "SEA": {
                    "full_name": "Seattle Seahawks",
                    "first_name": "Seattle",
                    "last_name": "Seahawks",
                },
                "NE": {
                    "full_name": "New England Patriots",
                    "first_name": "New England",
                    "last_name": "Patriots",
                },
            },
        ):
            yield

    def test_returns_correct_structure_for_each_team(self):
        """Test returns correct structure with all required fields."""
        result = get_defense_entries()

        assert "SEA" in result
        entry = result["SEA"]
        assert entry["active"] is True
        assert entry["position"] == "DEF"
        assert entry["full_name"] == "Seattle Seahawks"
        assert entry["first_name"] == "Seattle"
        assert entry["last_name"] == "Seahawks"
        assert entry["sport"] == "nfl"
        assert entry["team"] == "SEA"
        assert entry["player_id"] == "SEA"
        assert entry["fantasy_positions"] == ["DEF"]
        assert entry["injury_status"] is None

    def test_returns_entry_for_every_team(self):
        """Test returns an entry for every team in TEAM_DEFENSE_NAMES."""
        result = get_defense_entries()

        assert len(result) == 2
        assert "SEA" in result
        assert "NE" in result

    def test_returns_empty_dict_when_no_teams(self):
        """Test returns empty dict when TEAM_DEFENSE_NAMES is empty."""
        with patch(
            "patriot_center_backend.utils.defense_helper"
            ".TEAM_DEFENSE_NAMES",
            {},
        ):
            result = get_defense_entries()

        assert result == {}

    def test_player_id_matches_team_abbreviation(self):
        """Test player_id matches the team abbreviation key."""
        result = get_defense_entries()

        for team_abbr, entry in result.items():
            assert entry["player_id"] == team_abbr
            assert entry["team"] == team_abbr
