"""Matchup and playoff processing for manager metadata."""

import logging
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.starters_updater import (
    update_starters_cache,
)
from patriot_center_backend.cache.updaters.valid_options_updater import (
    update_valid_options_cache,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_season_state,
)

logger = logging.getLogger(__name__)


class MatchupProcessor:
    """Processes fantasy football matchups and playoff data.

    Handles:
    - Fetching matchup data from Sleeper API
    - Determining matchup results (win/loss/tie)
    - Updating cache at 4 levels (weekly, yearly-overall, yearly-season-state,
        all-time)
    - Tracking playoff appearances

    Uses session state pattern for thread safety during week processing.
    """

    def __init__(self) -> None:
        """Initialize matchup processor with cache reference."""
        # Session state (set externally before processing)
        self._playoff_week_start: int | None = None
        self._year: str | None = None
        self._week: str | None = None
        self._weekly_roster_ids: dict[int, str] = {}
        self._playoff_roster_ids: list[int] = []

    def set_session_state(
        self,
        year: str,
        week: str,
        weekly_roster_ids: dict[int, str],
        playoff_roster_ids: list[int],
        playoff_week_start: int,
    ) -> None:
        """Set session state before processing matchup data.

        Must be called before scrub_matchup_data() to establish context.

        Args:
            year: Season year as string
            week: Week number as string
            weekly_roster_ids: Mapping of roster IDs to manager names
            playoff_roster_ids: List with playoff bracket roster IDs
            playoff_week_start: Week when playoffs start
        """
        self._year = year
        self._week = week
        self._weekly_roster_ids = weekly_roster_ids
        self._playoff_roster_ids = playoff_roster_ids
        self._playoff_week_start = playoff_week_start

    def clear_session_state(self) -> None:
        """Clear session state after processing week.

        Prevents state leakage between weeks by resetting all session variables.
        """
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}
        self._playoff_roster_ids = []

    def scrub_matchup_data(self) -> None:
        """Fetch and process all matchups for a given week.

        Workflow:
        1. Fetch matchup data from Sleeper API
        2. Filter out non-playoff teams if in playoff weeks
        3. Pair managers by matchup_id
        4. Determine win/loss/tie based on points
        5. Update cache for both managers via _add_matchup_details_to_cache

        Raises:
            ValueError: If no league ID found for the year
        """
        if not self._week or not self._year:
            raise ValueError("Week or Year not set. Cannot process matchups.")

        if not self._playoff_week_start:
            raise ValueError(
                "Playoff week start not set. Cannot process matchups."
            )

        league_id = LEAGUE_IDS.get(int(self._year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {self._year}.")

        matchups_evaluated = []
        manager_matchup_data = fetch_sleeper_data(
            f"league/{league_id}/matchups/{self._week}"
        )

        if isinstance(manager_matchup_data, dict):
            raise ValueError("No matchup data found for week.")


        for manager_1_data in manager_matchup_data:
            manager_1_roster_id = manager_1_data.get("roster_id")
            if (
                not manager_1_roster_id
                or manager_1_roster_id not in self._weekly_roster_ids
            ):
                continue

            matchup_id = manager_1_data.get("matchup_id")
            if matchup_id in matchups_evaluated:
                continue
            matchups_evaluated.append(matchup_id)

            # Find opponent manager data
            for manager_2_data in manager_matchup_data:
                if manager_2_data.get("roster_id") == manager_1_roster_id:
                    continue
                if manager_2_data.get("matchup_id", None) == matchup_id:
                    break
            else:
                logger.warning(
                    f"No manager_2_data found for matchup_id: {matchup_id}"
                )
                continue

            manager_2_roster_id = manager_2_data.get("roster_id")

            # Extract points data
            manager_1_points = manager_1_data.get("points", 0.0)
            manager_2_points = manager_2_data.get("points", 0.0)

            manager_1_name = self._weekly_roster_ids.get(manager_1_roster_id)
            manager_2_name = self._weekly_roster_ids.get(manager_2_roster_id)

            if not manager_1_name or not manager_2_name:
                continue

            # Cache matchup data
            self._cache_matchup_data(manager_1_name, manager_1_data)
            self._cache_matchup_data(manager_2_name, manager_2_data)

            # Construct manager matchup dicts
            manager_1 = {
                "manager": manager_1_name,
                "opponent_manager": manager_2_name,
                "points_for": manager_1_points,
                "points_against": manager_2_points,
            }
            manager_2 = {
                "manager": manager_2_name,
                "opponent_manager": manager_1_name,
                "points_for": manager_2_points,
                "points_against": manager_1_points,
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

    def scrub_playoff_data(self) -> None:
        """Mark playoff appearances for all teams in the playoff bracket.

        Adds the current year to each playoff team's playoff_appearances list
        if not already present. This is used for awards and playoff streak
        tracking.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        for roster_ids in self._playoff_roster_ids:
            manager = self._weekly_roster_ids.get(roster_ids, None)
            if not manager:
                continue

            manager_overall_data = (
                manager_cache[manager]["summary"]["overall_data"]
            )

            # Mark week as playoff week in the weekly summary
            if self._year not in manager_overall_data["playoff_appearances"]:
                manager_overall_data["playoff_appearances"].append(self._year)

    def _add_matchup_details_to_cache(
        self, matchup_data: dict[str, Any]
    ) -> None:
        """Update cache with matchup results at all aggregation levels.

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
            matchup_data: Dict with keys:
                - manager
                - opponent_manager
                - points_for
                - points_against
                - result

        Raises:
            ValueError: If matchup data is invalid or missing required fields
        """
        if not self._week or not self._year:
            raise ValueError("Week or Year not set. Cannot process matchups.")

        if not self._playoff_week_start:
            raise ValueError(
                "Playoff week start not set. Cannot process matchups."
            )

        manager_cache = CACHE_MANAGER.get_manager_cache()

        manager = matchup_data.get("manager")
        opponent_manager = matchup_data.get("opponent_manager")
        points_for = matchup_data.get("points_for")
        points_against = matchup_data.get("points_against")
        result = matchup_data.get("result")

        if not manager or not opponent_manager or result is None:
            raise ValueError("Invalid matchup data for caching:", matchup_data)

        year_level = manager_cache[manager]["years"][self._year]

        # Update weekly matchup summary
        week_level = year_level["weeks"][self._week]
        week_level["matchup_data"]["opponent_manager"] = opponent_manager
        week_level["matchup_data"]["points_for"] = points_for
        week_level["matchup_data"]["points_against"] = points_against
        week_level["matchup_data"]["result"] = result

        # Prepare yearly and top-level summaries
        season_state = get_season_state(
            self._year, self._week, self._playoff_week_start
        )

        yearly_overall_summary = (
            year_level["summary"]["matchup_data"]["overall"]
        )
        yearly_season_state_summary = (
            year_level["summary"]["matchup_data"][season_state]
        )

        top_level_overall_summary = (
            manager_cache[manager]["summary"]["matchup_data"]["overall"]
        )
        top_level_season_state_summary = (
            manager_cache[manager]["summary"]["matchup_data"][season_state]
        )

        summaries = [
            yearly_overall_summary,
            yearly_season_state_summary,
            top_level_overall_summary,
            top_level_season_state_summary,
        ]

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
            #   Total
            points_for_dict = summary["points_for"]
            points_for_dict["total"] += points_for
            points_for_dict["total"] = (
                float(  # Quantize points to 2 decimal places
                    Decimal(points_for_dict["total"]).quantize(Decimal("0.01"))
                )
            )

            #   Opponent-specific
            if opponent_manager not in summary["points_for"]["opponents"]:
                summary["points_for"]["opponents"][opponent_manager] = 0.0

            opp_points_for = summary["points_for"]["opponents"]
            opp_points_for[opponent_manager] += points_for
            opp_points_for[opponent_manager] = float(
                Decimal(opp_points_for[opponent_manager]).quantize(
                    Decimal("0.01")
                )  # Quantize points to 2 decimal places
            )

            # Points against
            #   Total
            points_against_dict = summary["points_against"]
            points_against_dict["total"] += points_against
            points_against_dict["total"] = float(
                Decimal(points_against_dict["total"]).quantize(
                    Decimal("0.01")  # Quantize points to 2 decimal places
                )
            )

            #   Opponent-specific
            if opponent_manager not in summary["points_against"]["opponents"]:
                summary["points_against"]["opponents"][opponent_manager] = 0.0

            opp_points_against = summary["points_against"]["opponents"]
            opp_points_against[opponent_manager] += points_against
            opp_points_against[opponent_manager] = float(
                Decimal(opp_points_against[opponent_manager]).quantize(
                    Decimal("0.01")  # Quantize points to 2 decimal places
                )
            )

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

    def _cache_matchup_data(
        self, manager: str, matchup: dict[str, Any]
    ) -> None:
        if not self._year or not self._week:
            raise ValueError(
                "Invalid year or week for caching:", self._year, self._week
            )

        for player_id in matchup["starters"]:
            if player_id == "0":  # "0" means no player started
                continue

            update_valid_options_cache(
                int(self._year), int(self._week), manager, player_id
            )

            player_score = matchup["players_points"].get(player_id, 0.0)
            update_starters_cache(
                int(self._year),
                int(self._week),
                manager,
                player_id,
                player_score,
            )
