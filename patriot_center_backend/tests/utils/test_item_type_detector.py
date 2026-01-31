"""Unit tests for item_type_detector module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.utils.item_type_detector import detect_item_type


class TestDetectItemType:
    """Test detect_item_type function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `NAME_TO_MANAGER_USERNAME`: mock manager mapping
        - `CACHE_MANAGER.get_players_cache`: mock players cache
        - `CACHE_MANAGER.get_player_ids_cache`: mock player IDs cache

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.utils.item_type_detector"
                ".NAME_TO_MANAGER_USERNAME",
                {"Tommy": "tommylowry", "Jay": "Jrazzam"},
            ),
            patch(
                "patriot_center_backend.utils.item_type_detector"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players,
            patch(
                "patriot_center_backend.utils.item_type_detector"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
        ):
            self.mock_players_cache = {
                "Patrick Mahomes": {"player_id": "4046"},
            }
            self.mock_player_ids_cache = {
                "4046": {"full_name": "Patrick Mahomes"},
            }
            mock_get_players.return_value = self.mock_players_cache
            mock_get_player_ids.return_value = self.mock_player_ids_cache

            yield

    def test_detects_manager_type(self):
        """Test detects manager type from NAME_TO_MANAGER_USERNAME."""
        result = detect_item_type("Tommy")

        assert result == "manager"

    def test_detects_draft_pick_type(self):
        """Test detects draft pick type from 'Draft Pick' in name."""
        result = detect_item_type("Tommy's 2024 Round 1 Draft Pick")

        assert result == "draft_pick"

    def test_detects_faab_type(self):
        """Test detects FAAB type from '$' in name."""
        result = detect_item_type("$10 FAAB")

        assert result == "faab"

    def test_detects_player_type_from_players_cache(self):
        """Test detects player type from players cache."""
        result = detect_item_type("Patrick Mahomes")

        assert result == "player"

    def test_detects_player_id_type_from_player_ids_cache(self):
        """Test detects player_id type from player IDs cache."""
        result = detect_item_type("4046")

        assert result == "player_id"

    def test_returns_unknown_for_unrecognized_item(self):
        """Test returns unknown for unrecognized item."""
        result = detect_item_type("some_random_string")

        assert result == "unknown"

    def test_manager_check_takes_priority_over_player(self):
        """Test manager check takes priority over player cache check."""
        self.mock_players_cache["Tommy"] = {"player_id": "9999"}

        result = detect_item_type("Tommy")

        assert result == "manager"

    def test_draft_pick_takes_priority_over_faab(self):
        """Test draft pick check takes priority over FAAB check."""
        result = detect_item_type("$5 Draft Pick")

        assert result == "draft_pick"
