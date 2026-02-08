"""Replacement-score cache builder for Patriot Center.

Responsibilities:
- Maintain a JSON cache of per-week replacement-level scores by position.
- Backfill historical seasons and compute 3-year rolling averages keyed by bye
counts.
- Persist an incrementally updated cache to disk and expose it to callers.

Notes:
- Uses Sleeper API data (network I/O) via fetch_sleeper_data.
- Seed player metadata via load_player_ids to filter and position players.
- Current season/week is resolved at runtime and weeks are capped by era rules.
"""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._base import (
    log_cache_update,
)
from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)
from patriot_center_backend.calculations.rolling_average_calculator import (
    calculate_three_year_averages,
)
from patriot_center_backend.constants import LEAGUE_IDS, Position
from patriot_center_backend.models import Player
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
)

logger = logging.getLogger(__name__)


class ReplacementScoreCacheBuilder:
    """Replacement-score cache builder for Patriot Center.

    Responsibilities:
    - Maintain a JSON cache of per-week replacement-level scores by position.
    - Backfill historical seasons and compute 3-year rolling averages keyed by
        bye counts.
    - Persist an incrementally updated cache to disk and expose it to callers.

    Notes:
    - Uses Sleeper API data (network I/O) via fetch_sleeper_data.
    - Seed player metadata via load_player_ids to filter and position players.
    - Current season/week is resolved at runtime and weeks are capped by era
        rules.
    """

    def __init__(self, year: int) -> None:
        """Initialize the ReplacementScoreCacheBuilder.

        Args:
            year: The NFL season year (e.g., 2024).
        """
        self.year = year
        self.week = self._get_next_week_to_update()

        self._initial_three_year_backfill()

        self.week_data: dict[str, Any] = {}
        self._set_week_data()

        self.yearly_score_settings: dict[int, dict[str, Any]] = {}
        self._set_yearly_score_settings()

    def update(self) -> None:
        """Update the replacement score cache for the current week."""
        # If no data for the current week, there's nothing left to update
        if not self.week_data:
            return

        # Initialize the replacement score cache
        replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()
        replacement_score_cache.setdefault(str(self.year), {})

        while self.week_data:
            # Fetch and update the replacement score for the current week
            replacement_score_cache[str(self.year)][str(self.week)] = (
                self._fetch_replacement_score_for_week()
            )
            log_cache_update(self.year, self.week, "Replacement Score")

            # Augment with bye-aware 3-year rolling averages
            if self._has_three_year_averages():
                replacement_score_cache[str(self.year)][str(self.week)] = (
                    calculate_three_year_averages(self.year, self.week)
                )

            # Move to the next week
            self._proceed_to_next_week()

    def _initial_three_year_backfill(self) -> None:
        """Backfill the initial three years of replacement scores."""
        replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

        if replacement_score_cache:
            return

        logger.info(
            f"Starting backfill of Replacement "
            f"Score Cache for season {self.year}"
        )

        for backfill_year in range(self.year - 3, self.year):
            replacement_score_cache[str(backfill_year)] = {}
            ReplacementScoreCacheBuilder(backfill_year).update()

    def _has_three_year_averages(self) -> bool:
        """Check if there are 3-year averages for the current year.

        Returns:
            True if there are 3-year averages, False otherwise.
        """
        replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

        return str(self.year - 3) in replacement_score_cache

    def _get_next_week_to_update(self) -> int:
        """Determine the next week to update.

        Returns:
            The next week to update.
        """
        replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

        # If cache is not empty, return the last week + 1
        if len(replacement_score_cache.get(str(self.year), {})) > 0:
            last_week = list(replacement_score_cache[str(self.year)].keys())[-1]
            return int(last_week) + 1

        # If cache is empty, start at week 1
        else:
            return 1

    def _set_week_data(self) -> None:
        """Fetch data for the current week from the Sleeper API.

        Raises:
            ValueError: If the request to the Sleeper API fails.
        """
        # Fetch data from the Sleeper API for the given season and week
        week_data = fetch_sleeper_data(
            f"stats/nfl/regular/{self.year}/{self.week}"
        )
        if not isinstance(week_data, dict):
            raise ValueError(
                f"Sleeper API call failed for "
                f"year {self.year}, week {self.week}"
            )

        self.week_data = week_data

    def _set_yearly_score_settings(self) -> None:
        """Fetch the scoring settings for each year from the Sleeper API.

        Raises:
            ValueError: If the request to the Sleeper API fails.
        """
        yearly_scoring_settings = {}
        for yr in range(self.year, self.year + 4):
            if yr not in LEAGUE_IDS:
                continue
            scoring_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS[yr]}")
            if not isinstance(scoring_settings, dict):
                raise ValueError(
                    f"Sleeper API call failed to retrieve "
                    f"scoring settings for year {yr}"
                )
            yearly_scoring_settings[yr] = scoring_settings["scoring_settings"]

        self.yearly_score_settings = yearly_scoring_settings

    def _proceed_to_next_week(self) -> None:
        """Move to the next week for the current season."""
        self.week += 1
        self._set_week_data()

    def _fetch_replacement_score_for_week(self) -> dict[str, Any]:
        """Fetch the replacement score for the current week.

        Returns:
            The replacement score for the current week.
        """
        # Initialize the byes counter
        final_week_scores: dict[str, Any] = {"byes": 32}
        first = True
        for yr in self.yearly_score_settings:
            week_scores = {pos: [] for pos in Position}

            for player_id in self.week_data:
                if "TEAM_" in player_id:
                    if first:
                        # TEAM_ entries represent real teams -> decrement byes
                        final_week_scores["byes"] -= 1
                    continue

                # Weird edge case with Zach Ertz traded, his stats show twice
                # and one is 1339z
                if player_id == "1339z":
                    continue

                player = Player(player_id, apply=False)

                if player.position not in Position:
                    continue

                player_data = self.week_data[str(player)]

                if player_data.get("gp", 0.0) == 0.0:
                    continue

                player_score = calculate_player_score(
                    player_data, self.yearly_score_settings[yr]
                )

                # Add the player's points to the appropriate position list
                week_scores[Position(player.position)].append(player_score)

            # Set first to false after first iteration
            # since we have the number of byes
            first = False

            # Sort scores for each position in descending order
            for position in week_scores:
                week_scores[position].sort(reverse=True)

            # Determine the replacement scores for each position
            final_week_scores[f"{yr}_scoring"] = {
                Position.QB: week_scores[Position.QB][12],  # 13th QB
                Position.RB: week_scores[Position.RB][30],  # 31st RB
                Position.WR: week_scores[Position.WR][30],  # 31st WR
                Position.TE: week_scores[Position.TE][12],  # 13th TE
                Position.K: week_scores[Position.K][12],  # 13th K
                Position.DEF: week_scores[Position.DEF][12],  # 13th DEF
            }

        return final_week_scores
