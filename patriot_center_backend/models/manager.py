"""Manager class."""

from __future__ import annotations

import logging
from copy import deepcopy
from functools import cache
from time import time
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import (
    LEAGUE_IDS,
    USERNAME_TO_REAL_NAME,
    Position,
)

if TYPE_CHECKING:
    from patriot_center_backend.models.player import Player

MatchupType = Literal["regular_season", "playoffs"]

logger = logging.getLogger(__name__)


class Manager:
    """Manager class.

    Uses singleton pattern via __new__ - instances are stored in
    _instances and never garbage collected. B019 warnings for
    @cache on methods are safe to suppress in this context.
    """
    _instances: ClassVar[dict[str, Manager]] = {}

    def __new__(cls, user_id: str) -> Manager:
        """Create a new manager instance or return the existing one.

        Args:
            user_id: The user ID of the manager

        Returns:
            The manager instance
        """
        if user_id in cls._instances:
            return cls._instances[user_id]
        instance = super().__new__(cls)
        cls._instances[user_id] = instance
        return instance

    def __init__(self, user_id: str) -> None:
        """Manager class.

        Args:
            user_id: The user ID of the manager
        """
        if hasattr(self, "_initialized"):
            return  # Already initialized
        self._initialized = True

        self.user_id = user_id

        self._load_from_cache()

    def __str__(self) -> str:
        """String representation of the manager.

        Returns:
            The user ID of the manager
        """
        return self.user_id

    def __eq__(self, other: object) -> bool:
        """Equality operator for Manager class.

        Args:
            other: The object to compare to.

        Returns:
            True if the objects are equal, False otherwise.
        """
        if not isinstance(other, Manager):
            return NotImplemented

        return self.user_id == other.user_id

    def __ne__(self, other: object) -> bool:
        """Inequality operator for Manager class.

        Args:
            other: The object to compare to.

        Returns:
            True if the objects are not equal, False otherwise.
        """
        return not self == other

    def __hash__(self) -> int:
        """Hash function for Manager class.

        Returns:
            The hash of the manager.
        """
        return hash(self.user_id)

    @classmethod
    def load_all_managers(cls) -> None:
        """Load all managers into the cache."""
        cls.get_managers()

    @classmethod
    def get_managers(
        cls,
        year: str | None = None,
        week: str | None = None,
        active_only: bool = False,
    ) -> list[Manager]:
        """Get players who have participated in the given year and week.

        If the manager does not have matching data, return an empty list.
        Defaults to returning all participants.

        Args:
            year: Filter by year
            week: Filter by week
            active_only: Filter by active managers only

        Returns:
            List of managers who have participated in the given year and week.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        managers = []
        for user_id in manager_cache:
            manager = cls(user_id)
            if active_only and not manager.is_active():
                continue
            if manager.participated(year, week):
                managers.append(manager)

        return managers

    @classmethod
    def get_name_to_user_id_map(cls) -> dict[str, str]:
        """Get a mapping of real names to user IDs.

        Returns:
            A dictionary mapping real names to user IDs.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()
        return {
            data["real_name"]: user_id
            for user_id, data in manager_cache.items()
        }

    def participated(
        self, year: str | None = None, week: str | None = None
    ) -> bool:
        """Check if a manager participated in a given year and week.

        If year or week is not provided, defaults to all years or all weeks.

        Args:
            year: Filter by year.
            week: Filter by week.

        Returns:
            True if the manager participated in the given parameters,
            False otherwise.
        """
        if not self._season_data:
            return False

        if week and not year:
            logger.warning(
                f"Week {week} provided without year for "
                f"manager {self.real_name}"
            )
            return False

        if not year:
            return True

        if not self._season_data.get(year):
            return False

        if not week:
            return True

        return f"{year}_{week}" in self._matchup_data

    def set_season_data(
        self,
        year: str,
        team_image_url: str,
        team_name: str,
        season_complete: bool,
        roster_id: int,
        playoff_appearance: bool = False,
    ) -> None:
        """Set manager season data.

        Args:
            year: The year.
            week: The week.
            league_id: The league ID.
            team_image_url: The team image URL.
            team_name: The team name.
            season_complete: Whether the season is complete.
            roster_id: The roster ID.
            playoff_appearance: Whether the manager appeared in the playoffs.
        """
        if (  # If season already set and complete
            self._season_data.get(year)
            and self._season_data[year]["season_complete"]
        ):
            return

        self._season_data[year] = {
            "team_image_url": team_image_url,
            "team_name": team_name,
            "season_complete": season_complete,
            "roster_id": roster_id,
            "playoff_appearance": playoff_appearance,
        }

        if "playoff_placement" not in self._season_data[year]:
            self._season_data[year]["playoff_placement"] = None

        self._apply_to_cache()

    def set_playoff_appearance(self, year: str) -> None:
        """Set manager playoff appearance.

        Args:
            year: The year.
        """
        self._season_data[year]["playoff_appearance"] = True
        self._apply_to_cache()

    def set_matchup_data(
        self,
        year: str,
        week: str,
        opponent: Manager,
        result: Literal["win", "loss", "tie"],
        points_for: float,
        points_against: float,
        starters: list[Player],
        rostered: list[Player],
        matchup_type: Literal["regular_season", "playoffs"],
    ) -> None:
        """Set manager week data.

        Args:
            year: The year.
            week: The week.
            opponent: The opponent.
            result: The result.
            points_for: The points for.
            points_against: The points against.
            starters: The started players.
            rostered: The rostered players.
            matchup_type: The matchup type.
        """
        self._matchup_data.setdefault(f"{year}_{week}", {})
        self._matchup_data[f"{year}_{week}"] = {
            "opponent": str(opponent),
            "result": result,
            "points_for": points_for,
            "points_against": points_against,
            "starters": [str(p) for p in starters],
            "rostered": [str(p) for p in rostered],
            "matchup_type": matchup_type,
        }

        self._apply_to_cache()

    def set_playoff_placement(self, year: str, playoff_placement: int) -> None:
        """Set manager playoff placement.

        Args:
            year: The year.
            playoff_placement: The playoff placement.
        """
        self._season_data[year]["playoff_placement"] = playoff_placement
        self._apply_to_cache()

    def get_metadata(self) -> dict[str, Any]:
        """Get manager metadata.

        Returns:
            Manager metadata
        """
        return {
            "name": self.real_name,
            "full_name": self.real_name,
            "first_name": self.real_name,
            "last_name": "",
            "image_url": self.image_url,
            "user_id": self.user_id,
            "username": self.username,
            "provide_link": True,
            "type": "manager",
        }

    def get_roster_id(self, year: str) -> int | None:
        """Get the roster ID for a manager.

        Args:
            year: The year.

        Returns:
            The roster ID.
        """
        roster_id = self._season_data.get(year, {}).get("roster_id")
        if roster_id is None:
            logger.warning(
                f"Roster ID not found for manager {self.real_name} in "
                f"year {year}"
            )
        return roster_id

    @cache  # noqa: B019
    def get_score_awards(
        self, year: str | None = None, opponent: Manager | None = None
    ) -> dict[str, Any]:
        """Get manager scoring records and extremes.

        Iterates through all matchups to find:
        - Highest weekly score
        - Lowest weekly score
        - Biggest blowout win
        - Biggest blowout loss

        Each record includes full matchup card with top/lowest scorers.

        Args:
            year: Season year (optional - defaults to all-time)
            opponent: Filter by opponent (optional - defaults to all opponents)

        Returns:
            Dictionary with all scoring records
        """
        matches = self._get_matching_matchup_data(year=year, opponent=opponent)

        highest_weekly_score = (0.0, "", "")
        lowest_weekly_score = (float("inf"), "", "")
        biggest_blowout_win = (0.0, "", "")
        biggest_blowout_loss = (0.0, "", "")

        for match in matches:
            if match["points_for"] > highest_weekly_score[0]:
                highest_weekly_score = (
                    match["points_for"],
                    match["year"],
                    match["week"],
                )
            if match["points_for"] < lowest_weekly_score[0]:
                lowest_weekly_score = (
                    match["points_for"],
                    match["year"],
                    match["week"],
                )
            if (
                match["points_for"] - match["points_against"]
                > biggest_blowout_win[0]
            ):
                biggest_blowout_win = (
                    match["points_for"] - match["points_against"],
                    match["year"],
                    match["week"],
                )
            if (
                match["points_for"] - match["points_against"]
                < biggest_blowout_loss[0]
            ):
                biggest_blowout_loss = (
                    match["points_for"] - match["points_against"],
                    match["year"],
                    match["week"],
                )

        returning_dictionary = {}
        if highest_weekly_score[0] != 0.0:
            returning_dictionary["highest_weekly_score"] = (
                self.get_matchup_data(
                    highest_weekly_score[1], highest_weekly_score[2]
                )
            )
        if lowest_weekly_score[0] != float("inf"):
            returning_dictionary["lowest_weekly_score"] = self.get_matchup_data(
                lowest_weekly_score[1], lowest_weekly_score[2]
            )
        if biggest_blowout_win[0] != 0.0:
            returning_dictionary["biggest_blowout_win"] = self.get_matchup_data(
                biggest_blowout_win[1], biggest_blowout_win[2]
            )
        if biggest_blowout_loss[0] != 0.0:
            returning_dictionary["biggest_blowout_loss"] = (
                self.get_matchup_data(
                    biggest_blowout_loss[1], biggest_blowout_loss[2]
                )
            )

        return returning_dictionary

    def get_players(
        self,
        year: str | None = None,
        week: str | None = None,
        only_starters: bool = False,
        suppress_warnings: bool = False,
    ) -> list[Player]:
        """Get players for a given year and week.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_starters: Only include players who started the week.
            suppress_warnings: Whether to suppress warnings.

        Returns:
            List of players.
        """
        if week and not year:
            logger.warning(
                f"Week {week} provided without year for "
                f"manager {self.real_name}"
            )
            return []

        matches = self._get_matching_matchup_data(
            year=year, week=week, only_starters=only_starters
        )
        if not matches:
            if suppress_warnings:
                return []
            logger.warning(
                f"Manager {self.real_name} ({self.user_id}) "
                f"does not have data for the given parameters."
            )
            return []

        players = []
        for match in matches:
            if only_starters:
                players.extend(match["starters"])
            else:
                players.extend(match["rostered"])

        if not players:
            if suppress_warnings:
                return []
            logger.warning(
                f"Manager {self.real_name} ({self.user_id}) "
                f"does not have data for the given parameters."
            )
            return []

        return players

    @cache  # noqa: B019
    def get_opponents(self, year: str | None = None) -> set[Manager]:
        """Get opponents for a manager.

        Args:
            year: Filter by year.

        Returns:
            Set of opponents.
        """
        matches = self._get_matching_matchup_data(year=year)

        opponents = set()
        for match in matches:
            opponents.add(match["opponent"])
        return opponents

    @cache  # noqa: B019
    def get_matchup_data_summary(
        self,
        year: str | None = None,
        week: str | None = None,
        only_starters: bool = True,
        player: Player | None = None,
        matchup_type: MatchupType | None = None,
        opponent: Manager | None = None,
    ) -> dict[str, int | float]:
        """Get the points scored by the manager.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_starters: Whether to filter by player if they started the week.
            player: Filter by player.
            matchup_type: Filter by matchup type.
            opponent: Filter by opponent.

        Returns:
            The points scored by the manager.
        """
        matches = self._get_matching_matchup_data(
            year=year,
            week=week,
            only_starters=only_starters,
            player=player,
            matchup_type=matchup_type,
            opponent=opponent,
        )

        wins = 0
        losses = 0
        ties = 0
        points_for = 0.0
        points_against = 0.0
        for match in matches:
            wins += match["result"] == "win"
            losses += match["result"] == "loss"
            ties += match["result"] == "tie"
            points_for += match["points_for"]
            points_against += match["points_against"]

        num_games = wins + losses + ties
        if num_games == 0:
            return {}

        return {
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_percentage": round((wins / num_games) * 100, 1),
            "average_points_for": round(points_for / num_games, 2),
            "average_points_against": round(points_against / num_games, 2),
            "average_point_differential": round(
                (points_for - points_against) / num_games, 2
            ),
        }

    def get_positional_scores_for_starters(
        self,
        year: str | None = None,
        week: str | None = None,
    ) -> dict[Position, list[float]]:
        """Get the positional scores for a given list of players.

        Args:
            players: A list of players.
            year: The year (defaults to all years).
            week: The week (defaults to all weeks).

        Returns:
            A dictionary where keys are Positions and values are positional
            scores for each position.
        """
        if week and not year:
            logger.warning(
                f"Week {week} provided without year for "
                f"manager {self.real_name}"
            )
            return {}

        starters = self.get_players(
            year=year,
            week=week,
            only_starters=True,
            suppress_warnings=True,
        )

        pos_scores: dict[Position, list[float]] = {}
        for player in starters:
            pos_scores.setdefault(player.position, []).append(
                player.get_points(year=year, week=week)
            )

        return pos_scores

    def get_years_active(self) -> list[str]:
        """Get a list of years the manager has been active.

        Returns:
            A list of years the manager has been active.
        """
        return list(self._season_data.keys())

    @cache  # noqa: B019
    def get_matchup_data(self, year: str, week: str) -> dict[str, Any]:
        """Get matchup data for a given year and week.

        Args:
            year: The year of the matchup.
            week: The week of the matchup.
            player_output_type: Whether to return player IDs or objects

        Returns:
            A dictionary containing the matchup data.
        """
        from patriot_center_backend.models.player import Player

        data = self._matchup_data.get(f"{year}_{week}", {})
        if not data:
            return {}

        data = deepcopy(data)
        data["opponent"] = Manager(data["opponent"])

        data["starters"] = [Player(p) for p in data["starters"]]
        data["rostered"] = [Player(p) for p in data["rostered"]]

        return data

    @cache  # noqa: B019
    def get_playoff_appearances_list(self) -> list[int]:
        """Get the years in which the manager appeared in the playoffs."""
        years = []
        for year, data in self._season_data.items():
            if data["playoff_appearance"]:
                years.append(int(year))

        return years

    @cache  # noqa: B019
    def get_playoff_placements(self, year: str | None = None) -> dict[str, int]:
        """Get the manager's placement in the playoffs.

        Args:
            year: The year.
        """
        placements = {}
        for yr, data in self._season_data.items():
            if data.get("playoff_placement") is not None:
                placements[yr] = data.get("playoff_placement")

        if year is not None:
            return placements.get(year, {})

        return placements

    @cache  # noqa: B019
    def get_last_matchup(
        self,
        year: str | None = None,
        result: Literal["win", "loss", "tie"] | None = None,
        opponent: Manager | None = None,
    ) -> dict[str, Any]:
        """Get the last matchup for a given year and result.

        Args:
            year: Filter by year.
            result: Filter by result.
            opponent: Filter by opponent.

        Returns:
            A dictionary containing the matchup data.
        """
        matchups = self._get_matching_matchup_data(
            year=year, result=result, opponent=opponent
        )
        if not matchups:
            return {}
        last_matchup = matchups[-1]

        return self.get_matchup_data(last_matchup["year"], last_matchup["week"])

    def is_active(self) -> bool:
        """Check if manager is active.

        Returns:
            True if manager is active, False otherwise.
        """
        return self.participated(year=str(max(LEAGUE_IDS.keys())))

    def _load_from_cache(self) -> None:
        """Loads manager data from cache."""
        manager_cache = CACHE_MANAGER.get_manager_cache()

        # Get manager data
        manager_data = deepcopy(manager_cache.get(self.user_id, {}))

        self._overall_data: dict[str, Any] = manager_data.get(
            "overall_data", {}
        )
        self._season_data: dict[str, dict[str, Any]] = manager_data.get(
            "season_data", {}
        )
        self._matchup_data: dict[str, dict[str, Any]] = manager_data.get(
            "matchup_data", {}
        )

        self._summary: dict[str, Any] = manager_data.get("summary", {})

        self._fetch_and_apply_user_metadata()

        self._apply_to_cache()

    def _apply_to_cache(self) -> None:
        """Applies the manager data to the cache."""
        manager_cache = CACHE_MANAGER.get_manager_cache()

        manager_cache[self.user_id] = {
            "real_name": self.real_name,  # Not read but used for display
            "overall_data": deepcopy(self._overall_data),
            "season_data": deepcopy(self._season_data),
            "matchup_data": deepcopy(self._matchup_data),
            "summary": deepcopy(self._summary),
        }

    def _fetch_and_apply_user_metadata(self) -> None:
        """Fetches and applies user metadata to the manager."""
        from patriot_center_backend.utils.sleeper_helpers import (
            fetch_user_metadata,
        )

        user_metadata = fetch_user_metadata(self.user_id, bypass_cache=True)

        self.username = user_metadata["display_name"]
        self.image_url = (
            f"https://sleepercdn.com/avatars/{user_metadata['avatar']}"
        )

        # TODO: change to cached data and make dynamic with user entry
        if self.username in USERNAME_TO_REAL_NAME:
            self.real_name = USERNAME_TO_REAL_NAME[self.username]
        else:
            self.real_name = self.username

        self._time_updated = time()

    def _get_matching_matchup_data( # turn public
        self,
        year: str | None = None,
        week: str | None = None,
        only_starters: bool = True,
        player: Player | None = None,
        result: Literal["win", "loss", "tie"] | None = None,
        matchup_type: MatchupType | None = None,
        opponent: Manager | None = None,
    ) -> list[dict[str, Any]]:
        """Get all data entries matching the given filters.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_starters: Only include players who started the week.
            player: Filter by player.
            result: Filter by result.
            matchup_type: Filter by matchup type.
            opponent: Filter by opponent.

        Returns:
            List of matching data entries.
        """
        if not self._matchup_data:
            return []

        if year and week:
            data = self.get_matchup_data(year, week)
            if not data:
                return []
            if player:
                if player not in data["rostered"]:
                    return []
                if only_starters and str(player) not in data["starters"]:
                    return []
            if matchup_type and data["matchup_type"] != matchup_type:
                return []
            if opponent and data["opponent"] != opponent:
                return []
            if result and data["result"] != result:
                return []
            data["year"] = year
            data["week"] = week
            return [data]

        matches = []
        for key in self._matchup_data:
            data_year, data_week = key.split("_")
            if year and data_year != year:
                continue
            if week and data_week != week:
                continue
            recursive_matches = self._get_matching_matchup_data(
                year=data_year,
                week=data_week,
                only_starters=only_starters,
                player=player,
                result=result,
                matchup_type=matchup_type,
                opponent=opponent,
            )
            matches.extend(recursive_matches)

        return matches
