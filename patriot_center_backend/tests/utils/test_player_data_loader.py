"""
Unit tests for utils/player_data_loader.py - Fantasy Football WAR calculations.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


class TestGetMaxWeeks:
    """Test _get_max_weeks helper function."""

    def test_returns_current_week_for_current_season(self):
        """Test returns current_week for current season."""
        from patriot_center_backend.utils.player_data_loader import _get_max_weeks
        assert _get_max_weeks(season=2024, current_season=2024, current_week=17) == 17
        assert _get_max_weeks(season=2025, current_season=2025, current_week=8) == 8

    def test_returns_17_for_past_seasons(self):
        """Test returns 17 for completed past seasons."""
        from patriot_center_backend.utils.player_data_loader import _get_max_weeks
        assert _get_max_weeks(season=2023, current_season=2024, current_week=17) == 17
        assert _get_max_weeks(season=2021, current_season=2024, current_week=17) == 17

    def test_returns_16_for_2019_and_2020(self):
        """Test returns 16 for 2019 and 2020 seasons (historical cap)."""
        from patriot_center_backend.utils.player_data_loader import _get_max_weeks
        assert _get_max_weeks(season=2019, current_season=2024, current_week=16) == 16
        assert _get_max_weeks(season=2020, current_season=2024, current_week=16) == 16


class TestCalculateFfwarPosition:
    """Test _calculate_ffWAR_position simulation logic."""

    def test_returns_empty_dict_when_no_players(self):
        """Test returns empty dict when no players in scores."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # Empty scores - no managers have players
        scores = {
            "Tommy": {"total_points": 100.0, "players": {}},
            "Mike": {"total_points": 95.0, "players": {}}
        }

        all_player_scores = {
            "123": {
                "score": 30.0,
                "name": "Josh Allen"
            },
            "456": {
                "score": 10.0,
                "name": "Weak QB"
            },
            "789": {
                "score": 20.0,
                "name": "Average QB"
            }
        }

        all_rostered_players = {
            "Tommy": [],  # Josh Allen
            "Mike": [],    # Weak QB
            "James": []    # Average QB
        }

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', {"2024": {"1": {"QB_3yr_avg": 15.0}}}):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        assert result == {}

    @patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES')
    def test_player_above_replacement_wins_extra_games(self, mock_replacement):
        """Test that a player scoring above replacement adds wins."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # Setup: 3 managers with QBs of varying strength
        scores = {
            "Tommy": {
                "total_points": 111.0,  # High total
                "players": {"Josh Allen": 30.0}  # Strong QB
            },
            "Mike": {
                "total_points": 100.0,  # Lower total
                "players": {"Weak QB": 0.0}  # Weak QB
            },
            "James": {
                "total_points": 105.0,
                "players": {"Average QB": 10.0}  # Average QB
            }
        }


        all_player_scores = {
            "123": {
                "score": 30.0,
                "name": "Josh Allen"
            },
            "456": {
                "score": 0.0,
                "name": "Weak QB"
            },
            "789": {
                "score": 10.0,
                "name": "Average QB"
            }
        }

        all_rostered_players = {
            "Tommy": ["123"],  # Josh Allen
            "Mike": ["456"],    # Weak QB
            "James": ["789"]    # Average QB
        }

        # Replacement is 15.0 - between the two players
        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 10.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players) 

        # Josh Allen should have positive ffWAR (wins vs replacement)
        assert "123" in result
        assert "Josh Allen" == result["123"]["name"]
        assert result["123"]["ffWAR"] > 0

        # Weak QB should have negative ffWAR (loses vs replacement)
        assert "456" in result
        assert "Weak QB" == result["456"]["name"]
        assert result["456"]["ffWAR"] < 0

        # Average QB should have 0 ffWAR (didn't win or lose vs replacement)
        assert "789" in result
        assert "Average QB" == result["789"]["name"]
        assert result["789"]["ffWAR"] == 0.0

    @patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES')
    def test_simulates_all_vs_all_matchups(self, mock_replacement):
        """Test that simulation considers all possible matchups."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # With 3 managers, each player gets tested in:
        # - 3 manager_playing scenarios (could be on any team)
        # - Against 2 opponents each (everyone except themselves)
        # Total: 3 * 2 = 6 simulated games per player

        scores = {
            "Tommy": {"total_points": 120.0, "players": {"Elite QB": 30.0}},
            "Mike": {"total_points": 110.0, "players": {"Good QB": 25.0}},
            "Cody": {"total_points": 100.0, "players": {"Bad QB": 10.0}}
        }

        all_player_scores = {
            "1": {"score": 30.0, "name": "Elite QB"},
            "2": {"score": 25.0, "name": "Good QB"},
            "3": {"score": 10.0, "name": "Bad QB"}
        }

        all_rostered_players = {
            "Tommy": ["1"],  # Elite QB
            "Mike": ["2"],    # Good QB
            "Cody": ["3"]     # Bad QB
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 20.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Elite QB should have high positive ffWAR (wins many matchups vs replacement)
        assert result["1"]["ffWAR"] > 0.3

        # Bad QB should have negative ffWAR (loses matchups vs replacement)
        assert result["3"]["ffWAR"] < -0.3

    @patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES')
    def test_includes_manager_and_position_in_result(self, mock_replacement):
        """Test that result includes manager and position metadata."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"Josh Allen": 25.0}
            }
        }

        all_player_scores = {
            "123": {
                "score": 25.0,
                "name": "Josh Allen"
            }
        }

        all_rostered_players = {
            "Tommy": ["123"]  # Josh Allen
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 15.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        assert result["123"]["manager"] == "Tommy"
        assert result["123"]["position"] == "QB"
        assert "ffWAR" in result["123"]
        assert result["123"]["ffWAR"] == 0.0 # No other managers to compare against

    @patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES')
    def test_rounds_ffwar_to_three_decimals(self, mock_replacement):
        """Test that ffWAR is rounded to 3 decimal places."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        scores = {
            "Tommy": {"total_points": 120.0, "players": {"Player": 25.0}},
            "Mike": {"total_points": 110.0, "players": {"Player2": 20.0}}
        }

        all_player_scores = {
            "1": {"score": 25.0, "name": "Player"},
            "2": {"score": 20.0, "name": "Player2"}
        }

        all_rostered_players = {
            "Tommy": ["1"],
            "Mike": ["2"]
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 22.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Check that result is rounded (should have max 3 decimal places)
        for player in result:
            ffwar = result[player]["ffWAR"]
            # Convert to string and check decimal places
            ffwar_str = str(ffwar)
            if '.' in ffwar_str:
                decimals = len(ffwar_str.split('.')[1])
                assert decimals <= 3


class TestFetchFfwar:
    """Test _fetch_ffWAR function that orchestrates position calculations."""

    @patch('patriot_center_backend.utils.player_data_loader._get_all_rostered_players')
    @patch('patriot_center_backend.utils.player_data_loader._get_all_player_scores')
    @patch('patriot_center_backend.utils.player_data_loader._calculate_ffWAR_position')
    @patch('patriot_center_backend.utils.player_data_loader.STARTERS_CACHE')
    def test_groups_players_by_position(self, mock_starters_cache, mock_calculate_ffWAR_position, mock_get_all_player_scores, mock_get_all_rostered):
        """Test that players are correctly grouped by position."""
        from patriot_center_backend.utils.player_data_loader import _fetch_ffWAR

        mock_starters_cache_dict = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB"},
                        "Saquon Barkley": {"points": 20.0, "position": "RB"},
                        "Total_Points": 120.0
                    },
                    "Mike": {
                        "Patrick Mahomes": {"points": 23.0, "position": "QB"},
                        "Total_Points": 115.0
                    }
                }
            }
        }

        mock_get_all_player_scores.return_value= {
            "QB": {
                "1": {
                    "score": 25.0,
                    "name": "Josh Allen"
                },
                "2": {
                    "score": 23.0,
                    "name": "Patrick Mahomes"
                }
            },
            "RB": {
                "3": {
                    "score": 20.0,
                    "name": "Saquon Barkley"
                }
            },
            "WR": {
                "4": {
                    "score": 15.0,
                    "name": "Amon-Ra St. Brown"
                }
            },
            "TE": {
                "5": {
                    "score": 10.0,
                    "name": "Travis Kelce"
                }
            },
            "K": {
                "6": {
                    "score": 8.0,
                    "name": "Justin Tucker"
                }
            },
            "DEF": {
                "7": {
                    "score": 12.0,
                    "name": "New England Patriots"
                }
            }
        }

        mock_get_all_rostered.return_value = {
            "Tommy": ["1", "3"],  # Josh Allen, Saquon Barkley
            "Mike": ["2"]         # Patrick Mahomes
        }

        roster_ids = {
            1: "Tommy",
            2: "Mike"
        }

        mock_calculate_ffWAR_position.return_value = {}

        with patch('patriot_center_backend.utils.player_data_loader.STARTERS_CACHE', mock_starters_cache_dict):
            _fetch_ffWAR(season=2024, week=1, roster_ids=roster_ids)

            # Should call _calculate_ffWAR_position for each position
            # At minimum QB and RB since those have players
            assert mock_calculate_ffWAR_position.call_count == 6  # All 6 positions (QB, RB, WR, TE, K, DEF)


class TestLoadOrUpdateFfwarCache:
    """Test load_or_update_ffWAR_cache main orchestration function."""

    @patch('patriot_center_backend.utils.player_data_loader.LEAGUE_IDS')
    @patch('patriot_center_backend.utils.player_data_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.player_data_loader.load_cache')
    @patch('patriot_center_backend.utils.player_data_loader.save_cache')
    @patch('patriot_center_backend.utils.player_data_loader._fetch_ffWAR')
    def test_creates_new_cache_with_progress_markers(self, mock_fetch, mock_save, mock_load, mock_current, mock_league_ids):
        """Test creates cache with Last_Updated markers."""
        from patriot_center_backend.utils.player_data_loader import update_player_data_cache

        mock_league_ids.keys = {2024: "league_id"}
        mock_current.return_value = (2024, 1)  # Just week 1
        mock_load.return_value = {}
        mock_fetch.return_value = {
            "123": {
                "name": "Player Name",
                "image_url": "url",
                "score": 12.0,
                "ffWAR": 1.0,
                "position": "QB",
                "manager": "Tommy",
                "started": True
            }
        }

        result = update_player_data_cache()

        # Cache should be created and saved
        assert mock_save.called
        # Result should NOT include metadata markers (they're popped before return)
        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result

    @patch('patriot_center_backend.utils.player_data_loader.LEAGUE_IDS')
    @patch('patriot_center_backend.utils.player_data_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.player_data_loader.load_cache')
    @patch('patriot_center_backend.utils.player_data_loader.save_cache')
    @patch('patriot_center_backend.utils.player_data_loader._get_roster_ids')
    @patch('patriot_center_backend.utils.player_data_loader._fetch_ffWAR')
    def test_resumes_from_last_updated(self, mock_fetch, mock_roster_ids, mock_save, mock_load, mock_current, mock_league_ids):
        """Test resumes processing from Last_Updated markers."""
        from patriot_center_backend.utils.player_data_loader import update_player_data_cache

        mock_league_ids.keys.return_value = [2024]
        mock_current.return_value = (2024, 5)
        # Cache already has weeks 1-3 for 2024
        mock_load.return_value = {
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": 3,
            "2024": {
                "1": {},
                "2": {},
                "3": {}
            }
        }
        mock_roster_ids.return_value = {}
        mock_fetch.return_value = {}

        update_player_data_cache()

        # Should only process weeks 4 and 5 (not 1-3)
        assert mock_fetch.call_count == 2

    @patch('patriot_center_backend.utils.player_data_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.player_data_loader.load_cache')
    @patch('patriot_center_backend.utils.player_data_loader.save_cache')
    @patch('patriot_center_backend.utils.player_data_loader._get_roster_ids')
    @patch('patriot_center_backend.utils.player_data_loader._fetch_ffWAR')
    def test_complete_fill_when_cache_is_empty(self, mock_fetch, mock_roster_ids, mock_save, mock_load, mock_current):
        """Test that weeks are capped correctly per season."""
        from patriot_center_backend.utils.player_data_loader import update_player_data_cache

        mock_current.return_value = (2024, 12)
        mock_load.return_value = {}
        mock_roster_ids.return_value = {}
        mock_fetch.return_value = {}

        update_player_data_cache()

        # Should process all weeks from 2019 to 2024 week 12
        # Seasons: 2019 (16), 2020 (16), 2021 (17), 2022 (17), 2023 (17), 2024 (12)
        # Total weeks = 16 + 16 + 17 + 17 + 17 + 12 = 95
        assert mock_fetch.call_count == 95


    @patch('patriot_center_backend.utils.player_data_loader.LEAGUE_IDS')
    @patch('patriot_center_backend.utils.player_data_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.player_data_loader.load_cache')
    @patch('patriot_center_backend.utils.player_data_loader.save_cache')
    @patch('patriot_center_backend.utils.player_data_loader._get_roster_ids')
    @patch('patriot_center_backend.utils.player_data_loader._fetch_ffWAR')
    def test_caps_weeks_at_17_for_regular_seasons(self, mock_fetch, mock_roster_ids, mock_save, mock_load, mock_current, mock_league_ids):
        """Test that weeks are capped at 17."""
        from patriot_center_backend.utils.player_data_loader import update_player_data_cache
        
        mock_league_ids.keys.return_value = [2024]
        mock_current.return_value = (2024, 18)
        mock_load.return_value = {}
        mock_roster_ids.return_value = {}
        mock_fetch.return_value = {}

        result = update_player_data_cache()

        # Should not process beyond week 17
        assert len(result["2024"]) == 17
        assert "18" not in result["2024"]
        assert "17" in result["2024"]

    @patch('patriot_center_backend.utils.player_data_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.player_data_loader.load_cache')
    @patch('patriot_center_backend.utils.player_data_loader.save_cache')
    @patch('patriot_center_backend.utils.player_data_loader._get_roster_ids')
    @patch('patriot_center_backend.utils.player_data_loader._fetch_ffWAR')
    def test_processes_historical_seasons_from_2019(self, mock_fetch, mock_roster_ids, mock_save, mock_load, mock_current):
        """Test that weeks are capped correctly per season."""
        from patriot_center_backend.utils.player_data_loader import update_player_data_cache

        mock_current.return_value = (2021, 1)
        mock_load.return_value = {}
        mock_roster_ids.return_value = {}
        mock_fetch.return_value = {}

        update_player_data_cache()

        # Should process:
        # - 2019: 16 weeks
        # - 2020: 16 weeks
        # - 2021: 1 week
        # Total: 16 + 16 + 1 = 33 calls
        assert mock_fetch.call_count == 33


class TestPlayoffScaling:
    """Test playoff ffWAR scaling logic (division by 3 for 4-team playoffs)."""

    def test_regular_season_no_scaling_2020(self):
        """Test that regular season weeks (< week 14) are not scaled in 2020."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position


        scores = {
            "Tommy": {"total_points": 120.0, "players": {"Elite QB": 30.0}},
            "Mike": {"total_points": 110.0, "players": {"Good QB": 25.0}},
            "Cody": {"total_points": 100.0, "players": {"Bad QB": 10.0}},
            "James": {"total_points": 105.0, "players": {"Average QB": 20.0}}
        }

        all_player_scores = {
            "123": {
                "score": 30.0,
                "name": "Elite QB"
            },
            "456": {
                "score": 25.0,
                "name": "Good QB"
            },
            "789": {
                "score": 10.0,
                "name": "Bad QB"
            },
            "101": {
                "score": 20.0,
                "name": "Average QB"
            }
        }

        all_rostered_players = {
            "Tommy": ["123"],
            "Mike":  ["456"],
            "James": ["101"],
            "Cody":  ["789"]
        }

        mock_replacement_data = {"2020": {"13": {"QB_3yr_avg": 20.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2020, week=13, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Elite QB should have positive ffWAR (no scaling)
        assert result["123"]["name"] == "Elite QB"
        assert result["123"]["ffWAR"] > 0
        # Store for comparison
        regular_season_ffwar = result["123"]["ffWAR"]

        # Now test playoff week 14 in 2020 - should be scaled by /3
        mock_replacement_data_playoff = {"2020": {"14": {"QB_3yr_avg": 20.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data_playoff):
            playoff_result = _calculate_ffWAR_position(scores, season=2020, week=14, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)
        
        playoff_ffwar = playoff_result["123"]["ffWAR"]

        # Playoff ffWAR should be approximately 1/3 of equivalent regular season
        # (allowing for rounding differences)
        assert abs(playoff_ffwar * 3 - regular_season_ffwar) < 0.01

    def test_playoff_scaling_2020_week_14(self):
        """Test playoffs start at week 14 for 2020 and earlier."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # 4 playoff teams
        scores = {
            "Seed1": {"total_points": 130.0, "players": {"Player1": 35.0}},
            "Seed2": {"total_points": 125.0, "players": {"Player2": 30.0}},
            "Seed3": {"total_points": 115.0, "players": {"Player3": 25.0}},
            "Seed4": {"total_points": 110.0, "players": {"Player4": 20.0}}
        }

        all_player_scores = {
            "1": {
                "score": 35.0,
                "name": "Player1"
            },
            "2": {
                "score": 20.0,
                "name": "Player2"
            },
            "3": {
                "score": 25.0,
                "name": "Player3"
            },
            "4": {
                "score": 20.0,
                "name": "Player4"
            }
        }

        all_rostered_players = {
            "Seed1": ["1"],
            "Seed2": ["2"],
            "Seed3": ["3"],
            "Seed4": ["4"]
        }

        # Playoffs
        mock_replacement_data = {"2020": {"14": {"QB_3yr_avg": 25.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2020, week=14, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)
        # Verify all players have results
        assert len(result) == 4

        # Player1 should have positive ffWAR (above replacement)
        assert result["1"]["name"] == "Player1"
        assert result["1"]["ffWAR"] > 0
        playoff_ffWAR = result["1"]["ffWAR"]

        # Non Playoffs
        mock_replacement_data = {"2020": {"13": {"QB_3yr_avg": 25.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2020, week=13, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)
        # Verify all players have results
        assert len(result) == 4

        # Player1 should have positive ffWAR (above replacement)
        assert result["1"]["name"] == "Player1"
        assert result["1"]["ffWAR"] > 0
        non_playoff_war = result["1"]["ffWAR"]

        # The ffWAR should be scaled (divided by 3)
        # With 4 teams: 4 * 3 = 12 simulated games
        # Raw ffWAR would be wins/12, scaled ffWAR is (wins/12)/3 = wins/36
        # So the values should be relatively small due to scaling
        assert abs(playoff_ffWAR * 3 - non_playoff_war) < 0.01

    def test_playoff_scaling_2021_week_15(self):
        """Test playoffs start at week 15 for 2021 and later."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # 4 playoff teams
        scores = {
            "Seed1": {"total_points": 130.0, "players": {"Player1": 35.0}},
            "Seed2": {"total_points": 125.0, "players": {"Player2": 30.0}},
            "Seed3": {"total_points": 115.0, "players": {"Player3": 25.0}},
            "Seed4": {"total_points": 110.0, "players": {"Player4": 20.0}}
        }

        all_player_scores = {
            "1": {
                "score": 35.0,
                "name": "Player1"
            },
            "2": {
                "score": 20.0,
                "name": "Player2"
            },
            "3": {
                "score": 25.0,
                "name": "Player3"
            },
            "4": {
                "score": 20.0,
                "name": "Player4"
            }
        }

        all_rostered_players = {
            "Seed1": ["1"],
            "Seed2": ["2"],
            "Seed3": ["3"],
            "Seed4": ["4"]
        }

        # Playoffs
        mock_replacement_data = {"2021": {"15": {"QB_3yr_avg": 25.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2021, week=15, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)
        # Verify all players have results
        assert len(result) == 4

        # Player1 should have positive ffWAR (above replacement)
        assert result["1"]["name"] == "Player1"
        assert result["1"]["ffWAR"] > 0
        playoff_ffWAR = result["1"]["ffWAR"]

        # Non Playoffs
        mock_replacement_data = {"2021": {"14": {"QB_3yr_avg": 25.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2021, week=14, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)
        # Verify all players have results
        assert len(result) == 4

        # Player1 should have positive ffWAR (above replacement)
        assert result["1"]["name"] == "Player1"
        assert result["1"]["ffWAR"] > 0
        non_playoff_war = result["1"]["ffWAR"]

        # The ffWAR should be scaled (divided by 3)
        # With 4 teams: 4 * 3 = 12 simulated games
        # Raw ffWAR would be wins/12, scaled ffWAR is (wins/12)/3 = wins/36
        # So the values should be relatively small due to scaling
        assert abs(playoff_ffWAR * 3 - non_playoff_war) < 0.01

    def test_playoff_scaling_maintains_rounding(self):
        """Test that playoff scaling still rounds to 3 decimal places."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        scores = {
            "Team1": {"total_points": 125.0, "players": {"Player1": 28.5}},
            "Team2": {"total_points": 120.0, "players": {"Player2": 26.3}},
            "Team3": {"total_points": 115.0, "players": {"Player3": 23.7}},
            "Team4": {"total_points": 110.0, "players": {"Player4": 21.1}}
        }

        all_player_scores = {
            "1": {
                "score": 28.5,
                "name": "Player1"
            },
            "2": {
                "score": 26.3,
                "name": "Player2"
            },
            "3": {
                "score": 23.7,
                "name": "Player3"
            },
            "4": {
                "score": 21.1,
                "name": "Player4"
            }
        }

        all_rostered_players = {
            "Team1": ["1"],
            "Team2": ["2"],
            "Team3": ["3"],
            "Team4": ["4"]
        }

        mock_replacement_data = {"2024": {"15": {"QB_3yr_avg": 24.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=15, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Check all results are rounded to max 3 decimal places
        for player in result:
            ffwar = result[player]["ffWAR"]
            ffwar_str = str(ffwar)
            if '.' in ffwar_str:
                decimals = len(ffwar_str.split('.')[1])
                assert decimals <= 3, f"{player} has {decimals} decimal places: {ffwar}"

    def test_playoff_negative_ffwar_also_scaled(self):
        """Test that negative playoff ffWAR is also scaled down by 3."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        # Create scenario where a player performs below replacement
        scores = {
            "Team1": {"total_points": 120.0, "players": {"Good Player": 30.0}},
            "Team2": {"total_points": 115.0, "players": {"Average Player": 20.0}},
            "Team3": {"total_points": 110.0, "players": {"Bad Player": 5.0}},
            "Team4": {"total_points": 105.0, "players": {"Decent Player": 18.0}}
        }

        all_player_scores = {
            "1": {
                "score": 30.0,
                "name": "Good Player"
            },
            "2": {
                "score": 20.0,
                "name": "Average Player"
            },
            "3": {
                "score": 5.0,
                "name": "Bad Player"
            },
            "4": {
                "score": 18.0,
                "name": "Decent Player"
            }
        }

        all_rostered_players = {
            "Team1": ["1"],
            "Team2": ["2"],
            "Team3": ["3"],
            "Team4": ["4"]
        }

        # Set replacement at 18.0 - Bad Player should have negative ffWAR
        mock_replacement_data = {"2022": {"15": {"RB_3yr_avg": 18.0}}}

        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2022, week=15, position="RB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Bad Player should have negative ffWAR (below replacement)
        assert result["3"]["name"] == "Bad Player"
        assert result["3"]["ffWAR"] < 0

        # Good Player should have positive ffWAR
        assert result["1"]["name"] == "Good Player"
        assert result["1"]["ffWAR"] > 0

        # Both should be scaled (relatively small absolute values)
        assert abs(result["3"]["ffWAR"]) < 1.0
        assert abs(result["1"]["ffWAR"]) < 1.0

    def test_playoff_boundary_conditions(self):
        """Test exact week boundaries for playoff scaling."""
        from patriot_center_backend.utils.player_data_loader import _calculate_ffWAR_position

        scores = {
            "A": {"total_points": 120.0, "players": {"P1": 25.0}},
            "B": {"total_points": 115.0, "players": {"P2": 20.0}}
        }

        all_player_scores = {
            "1": {
                "score": 25.0,
                "name": "P1"
            },
            "2": {
                "score": 20.0,
                "name": "P2"
            }
        }

        all_rostered_players = {
            "A": ["1"],
            "B": ["2"]
        }

        # 2019: week 13 regular, week 14 playoffs
        mock_replacement_data = {"2019": {"13": {"QB_3yr_avg": 20.0}}}
        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result_2019_w13 = _calculate_ffWAR_position(scores, season=2019, week=13, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        mock_replacement_data = {"2019": {"14": {"QB_3yr_avg": 20.0}}}
        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result_2019_w14 = _calculate_ffWAR_position(scores, season=2019, week=14, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Week 14 should be approximately 1/3 of week 13 (accounting for rounding)
        assert abs(result_2019_w14["1"]["ffWAR"] * 3 - result_2019_w13["1"]["ffWAR"]) < 0.01

        # 2021: week 14 regular, week 15 playoffs
        mock_replacement_data = {"2021": {"14": {"QB_3yr_avg": 20.0}}}
        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result_2021_w14 = _calculate_ffWAR_position(scores, season=2021, week=14, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        mock_replacement_data = {"2021": {"15": {"QB_3yr_avg": 20.0}}}
        with patch('patriot_center_backend.utils.player_data_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result_2021_w15 = _calculate_ffWAR_position(scores, season=2021, week=15, position="QB", all_player_scores=all_player_scores, all_rostered_players=all_rostered_players)

        # Week 15 should be approximately 1/3 of week 14 (accounting for rounding)
        assert abs(result_2021_w15["1"]["ffWAR"] * 3 - result_2021_w14["1"]["ffWAR"]) < 0.01
