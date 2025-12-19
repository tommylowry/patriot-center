"""
Unit tests for manager metadata image_url requirements.
Tests that image_url is included in all managers, players, and matchup data.
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
                                # NEW: Top 3 scorers with image_url
                                "manager_1_top_3_scorers": [
                                    {
                                        "name": "Amon-Ra St. Brown",
                                        "position": "WR",
                                        "score": 28.5,
                                        "image_url": "https://sleepercdn.com/content/nfl/players/7547.jpg"
                                    },
                                    {
                                        "name": "Travis Kelce",
                                        "position": "TE",
                                        "score": 22.3,
                                        "image_url": "https://sleepercdn.com/content/nfl/players/4866.jpg"
                                    },
                                    {
                                        "name": "49ers",
                                        "position": "DEF",
                                        "score": 18.0,
                                        "image_url": "https://sleepercdn.com/images/team_logos/nfl/sf.png"
                                    }
                                ],
                                "manager_2_top_3_scorers": [
                                    {
                                        "name": "Justin Jefferson",
                                        "position": "WR",
                                        "score": 25.1,
                                        "image_url": "https://sleepercdn.com/content/nfl/players/6797.jpg"
                                    },
                                    {
                                        "name": "Josh Allen",
                                        "position": "QB",
                                        "score": 23.4,
                                        "image_url": "https://sleepercdn.com/content/nfl/players/4881.jpg"
                                    },
                                    {
                                        "name": "Eagles",
                                        "position": "DEF",
                                        "score": 16.2,
                                        "image_url": "https://sleepercdn.com/images/team_logos/nfl/phi.png"
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
                                "manager_1_top_3_scorers": [],
                                "manager_2_top_3_scorers": []
                            },
                            "transactions": {}
                        }
                    }
                }
            }
        }
    }


class TestManagerAwardsImageUrls:
    """Test that get_manager_awards includes image_url in all matchup data."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_highest_weekly_score_includes_image_urls_and_matchup_structure(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test highest_weekly_score includes image_url for all players and proper matchup structure."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        assert "awards" in result
        highest_score = result["awards"]["highest_weekly_score"]

        # Verify matchup structure with manager_1 and manager_2
        assert "manager_1" in highest_score, "manager_1 must be present"
        assert "manager_2" in highest_score, "manager_2 must be present"
        assert "manager_1_score" in highest_score, "manager_1_score must be present"
        assert "manager_2_score" in highest_score, "manager_2_score must be present"

        # Verify managers have image_url
        assert "image_url" in highest_score["manager_1"], "manager_1 must have image_url"
        assert "image_url" in highest_score["manager_2"], "manager_2 must have image_url"

        # Verify manager_1 top_3_scorers all have image_url
        manager1_scorers = highest_score.get("manager_1_top_3_scorers", [])
        for i, player in enumerate(manager1_scorers):
            assert "image_url" in player, f"image_url missing for manager_1 top scorer #{i+1}: {player.get('name')}"
            assert player["image_url"] is not None and player["image_url"] != "", \
                f"image_url is empty for manager_1 top scorer #{i+1}: {player.get('name')}"

            # Verify all required fields are present
            assert "name" in player, f"name missing for manager_1 top scorer #{i+1}"
            assert "position" in player, f"position missing for manager_1 top scorer #{i+1}"
            assert "score" in player, f"score missing for manager_1 top scorer #{i+1}"

        # Verify manager_2 top_3_scorers all have image_url
        manager2_scorers = highest_score.get("manager_2_top_3_scorers", [])
        for i, player in enumerate(manager2_scorers):
            assert "image_url" in player, f"image_url missing for manager_2 top scorer #{i+1}: {player.get('name')}"
            assert player["image_url"] is not None and player["image_url"] != "", \
                f"image_url is empty for manager_2 top scorer #{i+1}: {player.get('name')}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_lowest_weekly_score_includes_image_urls_and_matchup_structure(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test lowest_weekly_score includes image_url for all players and proper matchup structure."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        lowest_score = result["awards"]["lowest_weekly_score"]

        # Verify matchup structure
        assert "manager_1_score" in lowest_score, "manager_1_score must be present in lowest_weekly_score"
        assert "manager_2_score" in lowest_score, "manager_2_score must be present in lowest_weekly_score"

        # Verify top_3_scorers have image_url
        for key in ["manager_1_top_3_scorers", "manager_2_top_3_scorers"]:
            scorers = lowest_score.get(key, [])
            for i, player in enumerate(scorers):
                assert "image_url" in player, f"image_url missing in {key} scorer #{i+1}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_biggest_blowout_win_includes_image_urls_and_scores(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test biggest_blowout_win includes image_url, manager_1_score, and manager_2_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        blowout_win = result["awards"]["biggest_blowout_win"]

        # Verify matchup structure with score fields
        assert "manager_1_score" in blowout_win, "manager_1_score must be present in biggest_blowout_win"
        assert "manager_2_score" in blowout_win, "manager_2_score must be present in biggest_blowout_win"
        assert blowout_win["manager_1_score"] is not None
        assert blowout_win["manager_2_score"] is not None

        # Verify differential is still present
        assert "differential" in blowout_win, "differential must still be present"

        # Verify image_urls in top_3_scorers
        for key in blowout_win.keys():
            if key.endswith("_top_3_scorers"):
                scorers = blowout_win[key]
                for i, player in enumerate(scorers):
                    assert "image_url" in player, f"image_url missing in {key} scorer #{i+1}"

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_biggest_blowout_loss_includes_image_urls_and_scores(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test biggest_blowout_loss includes image_url, manager_1_score, and manager_2_score."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        blowout_loss = result["awards"]["biggest_blowout_loss"]

        # Verify matchup structure with score fields
        assert "manager_1_score" in blowout_loss, "manager_1_score must be present in biggest_blowout_loss"
        assert "manager_2_score" in blowout_loss, "manager_2_score must be present in biggest_blowout_loss"

        # Verify image_urls in top_3_scorers
        for key in blowout_loss.keys():
            if key.endswith("_top_3_scorers"):
                scorers = blowout_loss[key]
                for player in scorers:
                    assert "image_url" in player, f"image_url missing in {key}"

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
        all_scorers = highest_score.get("manager_1_top_3_scorers", []) + highest_score.get("manager_2_top_3_scorers", [])
        defense_players = [p for p in all_scorers if p.get("position") == "DEF"]

        assert len(defense_players) > 0, "Test should include at least one DEF player"

        for def_player in defense_players:
            assert "image_url" in def_player, f"DEF player {def_player.get('name')} missing image_url"
            assert "team_logos" in def_player["image_url"] or ".png" in def_player["image_url"], \
                f"DEF player {def_player.get('name')} should have team logo URL, got: {def_player['image_url']}"


class TestManagerYearlyDataImageUrls:
    """Test that get_manager_yearly_data includes image_url in weekly matchup data."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_weekly_scores_include_image_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test weekly_scores include image_url for all players and proper matchup structure."""
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

        # Verify manager_1 top_3_scorers all have image_url
        manager1_scorers = week1.get("manager_1_top_3_scorers", [])
        assert len(manager1_scorers) > 0, "Week 1 should have manager_1 top scorers"

        for i, player in enumerate(manager1_scorers):
            assert "image_url" in player, f"Week 1 - image_url missing for manager_1 scorer #{i+1}: {player.get('name')}"
            assert player["image_url"] is not None and player["image_url"] != "", \
                f"Week 1 - image_url is empty for manager_1 scorer #{i+1}: {player.get('name')}"

            # Verify all required fields
            assert "name" in player
            assert "position" in player
            assert "score" in player

        # Verify manager_2 top_3_scorers all have image_url
        manager2_scorers = week1.get("manager_2_top_3_scorers", [])
        for i, player in enumerate(manager2_scorers):
            assert "image_url" in player, f"Week 1 - image_url missing for manager_2 scorer #{i+1}: {player.get('name')}"
            assert player["image_url"] is not None and player["image_url"] != ""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_all_weekly_matchups_have_image_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test all weekly matchups include image_url for all players."""
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
                    assert "image_url" in player, \
                        f"Week {week_num} - image_url missing in {key} scorer #{i+1}: {player.get('name')}"

                    # Ensure image_url is not None or empty
                    assert player["image_url"], \
                        f"Week {week_num} - image_url is empty in {key} scorer #{i+1}: {player.get('name')}"


class TestImageUrlFormat:
    """Test image_url format validation."""

    @patch('patriot_center_backend.utils.manager_metadata_manager.load_player_ids')
    @patch('patriot_center_backend.utils.manager_metadata_manager.load_cache')
    def test_image_urls_are_valid_urls(
        self, mock_load_cache, mock_load_player_ids, mock_cache_with_matchup_data
    ):
        """Test that image_url values are valid URL strings."""
        from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

        mock_load_cache.side_effect = [{}, {}]
        mock_load_player_ids.return_value = {}

        manager = ManagerMetadataManager()
        manager._cache = mock_cache_with_matchup_data

        result = manager.get_manager_awards("Tommy")

        highest_score = result["awards"]["highest_weekly_score"]
        all_scorers = highest_score.get("manager_1_top_3_scorers", []) + highest_score.get("manager_2_top_3_scorers", [])

        for player in all_scorers:
            image_url = player.get("image_url", "")
            assert image_url.startswith("http://") or image_url.startswith("https://"), \
                f"image_url should be a valid HTTP(S) URL, got: {image_url}"

            # Should contain image extension or be from sleepercdn
            assert any(ext in image_url for ext in [".jpg", ".png", ".jpeg", ".gif", "sleepercdn.com"]), \
                f"image_url should be an image URL, got: {image_url}"
