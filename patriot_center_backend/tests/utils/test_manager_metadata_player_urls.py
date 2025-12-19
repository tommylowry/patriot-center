"""
Unit tests for manager metadata player_url requirements.
Tests that player_url is included in all top_3_scorers data and new score fields are present.
"""
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_cache_with_matchup_data():
    """Sample cache data with complete matchup structure including top_3_scorers."""
    return {
        "Tommy": {
            "summary": {
                "user_id": "user_123",
                "overall_data": {
                    "avatar_urls": {
                        "full_size": "https://sleepercdn.com/avatars/avatar_url",
                        "thumbnail": "https://sleepercdn.com/avatars/thumbs/avatar_url"
                    },
                    "placement": {"2024": 1},
                    "playoff_appearances": ["2024"]
                },
                "matchup_data": {"overall": {}, "regular_season": {}, "playoffs": {}},
                "transactions": {}
            },
            "years": {
                "2024": {
                    "roster_id": 1,
                    "summary": {
                        "matchup_data": {"overall": {}, "regular_season": {}, "playoffs": {}},
                        "transactions": {}
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Mike",
                                "points_for": 145.6,
                                "points_against": 120.3,
                                "result": "win",
                                # NEW: Top 3 scorers with player_url
                                "tommy_top_3_scorers": [
                                    {
                                        "name": "Amon-Ra St. Brown",
                                        "position": "WR",
                                        "score": 28.5,
                                        "player_url": "https://sleepercdn.com/content/nfl/players/7547.jpg"
                                    },
                                    {
                                        "name": "Travis Kelce",
                                        "position": "TE",
                                        "score": 22.3,
                                        "player_url": "https://sleepercdn.com/content/nfl/players/4866.jpg"
                                    },
                                    {
                                        "name": "49ers",
                                        "position": "DEF",
                                        "score": 18.0,
                                        "player_url": "https://sleepercdn.com/images/team_logos/nfl/sf.png"
                                    }
                                ],
                                "mike_top_3_scorers": [
                                    {
                                        "name": "Justin Jefferson",
                                        "position": "WR",
                                        "score": 25.1,
                                        "player_url": "https://sleepercdn.com/content/nfl/players/6797.jpg"
                                    },
                                    {
                                        "name": "Josh Allen",
                                        "position": "QB",
                                        "score": 23.4,
                                        "player_url": "https://sleepercdn.com/content/nfl/players/4881.jpg"
                                    },
                                    {
                                        "name": "Eagles",
                                        "position": "DEF",
                                        "score": 16.2,
                                        "player_url": "https://sleepercdn.com/images/team_logos/nfl/phi.png"
                                    }
                                ]
                            },
                            "transactions": {}
                        },
                        "2": {
                            "matchup_data": {
                                "opponent_manager": "Owen",
                                "points_for": 110.0,
                                "points_against": 125.0,
                                "result": "loss",
                                "tommy_top_3_scorers": [],
                                "owen_top_3_scorers": []
                            },
                            "transactions": {}
                        }
                    }
                }
            }
        }
    }


class TestManagerAwardsPlayerUrls:
    """Test that get_manager_awards includes player_url in all top_3_scorers arrays."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_highest_weekly_score_includes_player_urls_and_opponent_score(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test highest_weekly_score includes player_url for all top_3_scorers and opponent_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        assert "awards" in result
        highest_score = result["awards"]["highest_weekly_score"]

        # Verify opponent_score is present
        assert "opponent_score" in highest_score, "opponent_score must be present in highest_weekly_score"
        assert highest_score["opponent_score"] is not None

        # Verify manager's top_3_scorers all have player_url
        manager_scorers = highest_score.get("tommy_top_3_scorers", [])
        for i, player in enumerate(manager_scorers):
            assert "player_url" in player, f"player_url missing for manager's top scorer #{i+1}: {player.get('name')}"
            assert player["player_url"] is not None and player["player_url"] != "", \
                f"player_url is empty for manager's top scorer #{i+1}: {player.get('name')}"

            # Verify all required fields are present
            assert "name" in player, f"name missing for manager's top scorer #{i+1}"
            assert "position" in player, f"position missing for manager's top scorer #{i+1}"
            assert "score" in player, f"score missing for manager's top scorer #{i+1}"

        # Verify opponent's top_3_scorers all have player_url
        opponent_scorers = highest_score.get("mike_top_3_scorers", [])
        for i, player in enumerate(opponent_scorers):
            assert "player_url" in player, f"player_url missing for opponent's top scorer #{i+1}: {player.get('name')}"
            assert player["player_url"] is not None and player["player_url"] != "", \
                f"player_url is empty for opponent's top scorer #{i+1}: {player.get('name')}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_lowest_weekly_score_includes_player_urls_and_opponent_score(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test lowest_weekly_score includes player_url for all top_3_scorers and opponent_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        lowest_score = result["awards"]["lowest_weekly_score"]

        # Verify opponent_score is present
        assert "opponent_score" in lowest_score, "opponent_score must be present in lowest_weekly_score"

        # Verify both manager and opponent top_3_scorers have player_url
        for key in ["tommy_top_3_scorers", "mike_top_3_scorers", "owen_top_3_scorers"]:
            scorers = lowest_score.get(key, [])
            for i, player in enumerate(scorers):
                assert "player_url" in player, f"player_url missing in {key} scorer #{i+1}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_biggest_blowout_win_includes_player_urls_and_scores(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test biggest_blowout_win includes player_url, manager_score, and opponent_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        blowout_win = result["awards"]["biggest_blowout_win"]

        # Verify NEW score fields are present
        assert "manager_score" in blowout_win, "manager_score must be present in biggest_blowout_win"
        assert "opponent_score" in blowout_win, "opponent_score must be present in biggest_blowout_win"
        assert blowout_win["manager_score"] is not None
        assert blowout_win["opponent_score"] is not None

        # Verify differential is still present
        assert "differential" in blowout_win, "differential must still be present"

        # Verify player_urls in top_3_scorers
        for key in blowout_win.keys():
            if key.endswith("_top_3_scorers"):
                scorers = blowout_win[key]
                for i, player in enumerate(scorers):
                    assert "player_url" in player, f"player_url missing in {key} scorer #{i+1}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_biggest_blowout_loss_includes_player_urls_and_scores(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test biggest_blowout_loss includes player_url, manager_score, and opponent_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        blowout_loss = result["awards"]["biggest_blowout_loss"]

        # Verify NEW score fields are present
        assert "manager_score" in blowout_loss, "manager_score must be present in biggest_blowout_loss"
        assert "opponent_score" in blowout_loss, "opponent_score must be present in biggest_blowout_loss"

        # Verify player_urls in top_3_scorers
        for key in blowout_loss.keys():
            if key.endswith("_top_3_scorers"):
                scorers = blowout_loss[key]
                for player in scorers:
                    assert "player_url" in player, f"player_url missing in {key}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_defense_players_have_team_logo_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test that DEF position players have team logo URLs."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        highest_score = result["awards"]["highest_weekly_score"]

        # Find defense players
        all_scorers = highest_score.get("tommy_top_3_scorers", []) + highest_score.get("mike_top_3_scorers", [])
        defense_players = [p for p in all_scorers if p.get("position") == "DEF"]

        assert len(defense_players) > 0, "Test should include at least one DEF player"

        for def_player in defense_players:
            assert "player_url" in def_player, f"DEF player {def_player.get('name')} missing player_url"
            assert "team_logos" in def_player["player_url"] or ".png" in def_player["player_url"], \
                f"DEF player {def_player.get('name')} should have team logo URL, got: {def_player['player_url']}"


class TestManagerYearlyDataPlayerUrls:
    """Test that get_manager_yearly_data includes player_url in weekly matchup top_3_scorers."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_weekly_scores_include_player_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test weekly_scores include player_url for all top_3_scorers."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_yearly_data("Tommy", "2024")

        weekly_scores = result["matchup_data"]["overall"]["weekly_scores"]

        assert len(weekly_scores) > 0, "Should have at least one weekly score"

        # Check first week's matchup
        week1 = weekly_scores[0]

        # Verify manager's top_3_scorers all have player_url
        manager_scorers = week1.get("tommy_top_3_scorers", [])
        assert len(manager_scorers) > 0, "Week 1 should have manager top scorers"

        for i, player in enumerate(manager_scorers):
            assert "player_url" in player, f"Week 1 - player_url missing for manager's scorer #{i+1}: {player.get('name')}"
            assert player["player_url"] is not None and player["player_url"] != "", \
                f"Week 1 - player_url is empty for manager's scorer #{i+1}: {player.get('name')}"

            # Verify all required fields
            assert "name" in player
            assert "position" in player
            assert "score" in player

        # Verify opponent's top_3_scorers all have player_url
        opponent_scorers = week1.get("mike_top_3_scorers", [])
        for i, player in enumerate(opponent_scorers):
            assert "player_url" in player, f"Week 1 - player_url missing for opponent's scorer #{i+1}: {player.get('name')}"
            assert player["player_url"] is not None and player["player_url"] != ""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_all_weekly_matchups_have_player_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test all weekly matchups include player_url for all players."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_yearly_data("Tommy", "2024")

        weekly_scores = result["matchup_data"]["overall"]["weekly_scores"]

        # Check all weeks
        for week_num, week_data in enumerate(weekly_scores, start=1):
            # Get all top_3_scorers keys for this week
            scorer_keys = [k for k in week_data.keys() if k.endswith("_top_3_scorers")]

            for key in scorer_keys:
                scorers = week_data[key]
                for i, player in enumerate(scorers):
                    assert "player_url" in player, \
                        f"Week {week_num} - player_url missing in {key} scorer #{i+1}: {player.get('name')}"

                    # Ensure player_url is not None or empty
                    assert player["player_url"], \
                        f"Week {week_num} - player_url is empty in {key} scorer #{i+1}: {player.get('name')}"


class TestPlayerUrlFormat:
    """Test player_url format validation."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_player_urls_are_valid_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test that player_url values are valid URL strings."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        highest_score = result["awards"]["highest_weekly_score"]
        all_scorers = highest_score.get("tommy_top_3_scorers", []) + highest_score.get("mike_top_3_scorers", [])

        for player in all_scorers:
            player_url = player.get("player_url", "")
            assert player_url.startswith("http://") or player_url.startswith("https://"), \
                f"player_url should be a valid HTTP(S) URL, got: {player_url}"

            # Should contain image extension or be from sleepercdn
            assert any(ext in player_url for ext in [".jpg", ".png", ".jpeg", ".gif", "sleepercdn.com"]), \
                f"player_url should be an image URL, got: {player_url}"
