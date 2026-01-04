"""
Matchup and playoff processing for manager metadata.

Handles matchup data collection and playoff bracket processing.
"""
from typing import Dict, Any, Optional
from decimal import Decimal

from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.managers.formatters import get_season_state


class MatchupProcessor:
    """
    Processes fantasy football matchups and playoff data.
    
    This class handles weekly matchup ingestion and playoff bracket processing.
    """
    
    def __init__(self, cache: dict, playoff_week_start: Optional[int]):
        """
        Initialize matchup processor.
        
        Args:
            cache: Main manager metadata cache (will be modified)
            playoff_week_start: Week when playoffs start (from league settings)
        """
        self._cache = cache
        self._playoff_week_start = playoff_week_start
        
        # Session state (set externally before processing)
        self._year: Optional[str] = None
        self._week: Optional[str] = None
        self._weekly_roster_ids: Dict[int, str] = {}
        self._playoff_roster_ids: Dict[int, str] = {}
    
    def set_session_state(self, year: str, week: str, weekly_roster_ids: Dict[int, str],
                         playoff_roster_ids: Dict[int, str], playoff_week_start: int) -> None:
        """Set session state before processing matchups."""
        self._year = year
        self._week = week
        self._weekly_roster_ids = weekly_roster_ids
        self._playoff_roster_ids = playoff_roster_ids
        self._playoff_week_start = playoff_week_start
    
    def clear_session_state(self) -> None:
        """Clear session state after processing week."""
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}
        self._playoff_roster_ids = {}

    def scrub_matchup_data(self, year: str, week: str) -> None:
        """
        Scrub and process matchup data for a given week.
        
        Args:
            year: Season year
            week: Week number
        """
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        matchups_evaluated = []
        manager_matchup_data , _ = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
        for manager_1_data in manager_matchup_data:
            if get_season_state(self._week, self._year, self._playoff_week_start) == "playoffs" and manager_1_data.get("roster_id", None) not in self._playoff_roster_ids.get("round_roster_ids", []):
                # Manager not in playoffs; skip
                continue

            matchup_id = manager_1_data.get("matchup_id", None)
            if matchup_id in matchups_evaluated:
                continue
            matchups_evaluated.append(matchup_id)

            # Find opponent manager data
            for manager_2_data in manager_matchup_data:
                if manager_2_data.get("roster_id", None) == manager_1_data.get("roster_id", None):
                    continue
                if manager_2_data.get("matchup_id", None) == matchup_id:
                    break
            
            # Extract points data
            manager_1_points = manager_1_data.get("points", 0.0)
            manager_2_points = manager_2_data.get("points", 0.0)

            # Construct manager matchup dicts
            manager_1 = {
                "manager": self._weekly_roster_ids.get(manager_1_data.get("roster_id", None), None),
                "opponent_manager": self._weekly_roster_ids.get(manager_2_data.get("roster_id", None), None),
                "points_for": manager_1_points,
                "points_against": manager_2_points
            }
            manager_2 = {
                "manager": self._weekly_roster_ids.get(manager_2_data.get("roster_id", None), None),
                "opponent_manager": self._weekly_roster_ids.get(manager_1_data.get("roster_id", None), None),
                "points_for": manager_2_data.get("points", 0.0),
                "points_against": manager_1_points
            }

            # Determine results
            if manager_1["points_for"] > manager_2["points_for"]:
                manager_1["result"] = "win"
                manager_2["result"] = "loss"
            elif manager_1["points_for"] < manager_2["points_for"]:
                manager_1["result"] = "loss"
                manager_2["result"] = "win"
            else:
                manager_1["result"] = "tie"
                manager_2["result"] = "tie"
            

            self._add_matchup_details_to_cache(manager_1)
            self._add_matchup_details_to_cache(manager_2)
    
    def _add_matchup_details_to_cache(self, matchup_data: dict) -> None:
        """Add matchup details to cache."""
        manager = matchup_data.get("manager", None)
        opponent_manager = matchup_data.get("opponent_manager", None)
        points_for = matchup_data.get("points_for", 0.0)
        points_against = matchup_data.get("points_against", 0.0)
        result = matchup_data.get("result", None)

        if not manager or not opponent_manager or result is None:
            raise ValueError("Invalid matchup data for caching:", matchup_data)
        
        # Update weekly summary
        weekly_summary = self._cache[manager]["years"][self._year]["weeks"][self._week]["matchup_data"]
        weekly_summary["opponent_manager"] = opponent_manager
        weekly_summary["points_for"] = points_for
        weekly_summary["points_against"] = points_against
        weekly_summary["result"] = result

        # Prepare yearly and top-level summaries
        yearly_overall_summary         = self._cache[manager]["years"][self._year]["summary"]["matchup_data"]["overall"]
        yearly_season_state_summary    = self._cache[manager]["years"][self._year]["summary"]["matchup_data"][get_season_state(self._week, self._year, self._playoff_week_start)]

        top_level_overall_summary      = self._cache[manager]["summary"]["matchup_data"]["overall"]
        top_level_season_state_summary = self._cache[manager]["summary"]["matchup_data"][get_season_state(self._week, self._year, self._playoff_week_start)]
        
        summaries = [yearly_overall_summary, yearly_season_state_summary,
                     top_level_overall_summary, top_level_season_state_summary]
        
        # Determine result key
        if result == "win":
            result_key = "wins"
        elif result == "loss":
            result_key = "losses"
        elif result == "tie":
            result_key = "ties"
        else:
            raise ValueError("Invalid matchup result for caching:", result)
        
        
        # Add matchup details in all summaries
        for summary in summaries:
            
            # Points for
            summary["points_for"]["total"] += points_for
            if opponent_manager not in summary["points_for"]["opponents"]:
                summary["points_for"]["opponents"][opponent_manager] = 0.0
            summary["points_for"]["opponents"][opponent_manager] += points_for

            # Points against
            summary["points_against"]["total"] += points_against
            if opponent_manager not in summary["points_against"]["opponents"]:
                summary["points_against"]["opponents"][opponent_manager] = 0.0
            summary["points_against"]["opponents"][opponent_manager] += points_against

            # Total matchups
            summary["total_matchups"]["total"] += 1
            if opponent_manager not in summary["total_matchups"]["opponents"]:
                summary["total_matchups"]["opponents"][opponent_manager] = 0
            summary["total_matchups"]["opponents"][opponent_manager] += 1

            # Wins/Losses/Ties
            summary[result_key]["total"] += 1
            if opponent_manager not in summary[result_key]["opponents"]:
                summary[result_key]["opponents"][opponent_manager] = 0
            summary[result_key]["opponents"][opponent_manager] += 1

            # Quantize points to 2 decimal places
            summary["points_for"]["total"] = float(Decimal(summary["points_for"]["total"]).quantize(Decimal('0.01')))
            summary["points_for"]["opponents"][opponent_manager] = float(Decimal(summary["points_for"]["opponents"][opponent_manager]).quantize(Decimal('0.01')))
            
            summary["points_against"]["total"] = float(Decimal(summary["points_against"]["total"]).quantize(Decimal('0.01')))
            summary["points_against"]["opponents"][opponent_manager] = float(Decimal(summary["points_against"]["opponents"][opponent_manager]).quantize(Decimal('0.01')))
    
    def scrub_playoff_data(self) -> None:
        """
        Scrub playoff data and update placements.
        """
        for roster_ids in self._playoff_roster_ids.get("round_roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_ids, None)
            if not manager:
                continue

            manager_overall_data = self._cache[manager]["summary"]["overall_data"]

            # Mark week as playoff week in the weekly summary
            if self._year not in manager_overall_data["playoff_appearances"]:
                manager_overall_data["playoff_appearances"].append(self._year)