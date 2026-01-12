"""
Matchup and playoff processing for manager metadata.

Handles matchup data collection and playoff bracket processing.
"""
from decimal import Decimal
from typing import Dict, Optional

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.formatters import get_season_state
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data


class MatchupProcessor:
    """
    Processes fantasy football matchups and playoff data.

    Handles:
    - Fetching matchup data from Sleeper API
    - Determining matchup results (win/loss/tie)
    - Updating cache at 4 levels (weekly, yearly-overall, yearly-season-state, all-time)
    - Tracking playoff appearances

    Uses session state pattern for thread safety during week processing.
    """

    def __init__(self, playoff_week_start: Optional[int]) -> None:
        """
        Initialize matchup processor with cache reference.

        Args:
            playoff_week_start: Week when playoffs start (from league settings)
        """
        self._playoff_week_start = playoff_week_start
        
        # Session state (set externally before processing)
        self._year: Optional[str] = None
        self._week: Optional[str] = None
        self._weekly_roster_ids: Dict[int, str] = {}
        self._playoff_roster_ids: Dict[int, str] = {}
    
    def set_session_state(self, year: str, week: str, weekly_roster_ids: Dict[int, str],
                         playoff_roster_ids: Dict[int, str], playoff_week_start: int) -> None:
        """
        Set session state before processing matchup data.

        Must be called before scrub_matchup_data() to establish context.

        Args:
            year: Season year as string
            week: Week number as string
            weekly_roster_ids: Mapping of roster IDs to manager names for this week
            playoff_roster_ids: Dict with playoff bracket roster IDs
            playoff_week_start: Week when playoffs start
        """
        self._year = year
        self._week = week
        self._weekly_roster_ids = weekly_roster_ids
        self._playoff_roster_ids = playoff_roster_ids
        self._playoff_week_start = playoff_week_start
    
    def clear_session_state(self) -> None:
        """
        Clear session state after processing week.

        Prevents state leakage between weeks by resetting all session variables.
        """
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}
        self._playoff_roster_ids = {}

    def scrub_matchup_data(self, year: str, week: str) -> None:
        """
        Fetch and process all matchups for a given week.

        Workflow:
        1. Fetch matchup data from Sleeper API
        2. Filter out non-playoff teams if in playoff weeks
        3. Pair managers by matchup_id
        4. Determine win/loss/tie based on points
        5. Update cache for both managers via _add_matchup_details_to_cache

        Args:
            year: Season year as string
            week: Week number as string

        Raises:
            ValueError: If no league ID found for the year
        """
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        matchups_evaluated = []
        manager_matchup_data = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
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
        """
        Update cache with matchup results at all aggregation levels.

        Updates cache at 4 levels:
        1. Weekly summary (specific opponent and result)
        2. Yearly overall summary (all matchups that year)
        3. Yearly season-state summary (regular season OR playoffs)
        4. Top-level overall summary (all-time stats)

        For each level, updates:
        - Points for/against (total and opponent-specific)
        - Total matchups count
        - Wins/losses/ties (total and opponent-specific)

        Uses Decimal for precise point quantization to 2 decimal places.

        Args:
            matchup_data: Dict with manager, opponent_manager, points_for, points_against, result

        Raises:
            ValueError: If matchup data is invalid or missing required fields
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        manager = matchup_data.get("manager", None)
        opponent_manager = matchup_data.get("opponent_manager", None)
        points_for = matchup_data.get("points_for", 0.0)
        points_against = matchup_data.get("points_against", 0.0)
        result = matchup_data.get("result", None)

        if not manager or not opponent_manager or result is None:
            raise ValueError("Invalid matchup data for caching:", matchup_data)
        
        # Update weekly summary
        weekly_summary = manager_cache[manager]["years"][self._year]["weeks"][self._week]["matchup_data"]
        weekly_summary["opponent_manager"] = opponent_manager
        weekly_summary["points_for"] = points_for
        weekly_summary["points_against"] = points_against
        weekly_summary["result"] = result

        # Prepare yearly and top-level summaries
        yearly_overall_summary         = manager_cache[manager]["years"][self._year]["summary"]["matchup_data"]["overall"]
        yearly_season_state_summary    = manager_cache[manager]["years"][self._year]["summary"]["matchup_data"][get_season_state(self._week, self._year, self._playoff_week_start)]

        top_level_overall_summary      = manager_cache[manager]["summary"]["matchup_data"]["overall"]
        top_level_season_state_summary = manager_cache[manager]["summary"]["matchup_data"][get_season_state(self._week, self._year, self._playoff_week_start)]
        
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
        Mark playoff appearances for all teams in the playoff bracket.

        Adds the current year to each playoff team's playoff_appearances list
        if not already present. This is used for awards and playoff streak tracking.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        for roster_ids in self._playoff_roster_ids.get("round_roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_ids, None)
            if not manager:
                continue

            manager_overall_data = manager_cache[manager]["summary"]["overall_data"]

            # Mark week as playoff week in the weekly summary
            if self._year not in manager_overall_data["playoff_appearances"]:
                manager_overall_data["playoff_appearances"].append(self._year)