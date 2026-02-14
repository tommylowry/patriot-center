"""Manager class."""

from __future__ import annotations

import logging
from copy import deepcopy
from time import time
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import USERNAME_TO_REAL_NAME, Position

if TYPE_CHECKING:
    from patriot_center_backend.models.player import Player

MatchupType = Literal["regular_season", "playoffs"]

logger = logging.getLogger(__name__)


class Manager:
    """Manager class."""

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

    @classmethod
    def get_all_managers(
        cls,
        year: str | None = None,
        week: str | None = None,
    ) -> list[Manager]:
        """Get players who have participated in the given year and week.

        If the manager does not have matching data, return an empty list.
        Defaults to returning all participants.

        Args:
            year: Filter by year
            week: Filter by week
            manager: Filter by manager

        Returns:
            List of managers who have participated in the given year and week.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        managers = []
        for user_id in manager_cache:
            manager = cls(user_id)
            if manager.check_participation(year, week):
                managers.append(manager)

        return managers

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
        self._week_data: dict[str, dict[str, Any]] = manager_data.get(
            "week_data", {}
        )
        self._transactions: dict[str, list[str]] = manager_data.get(
            "transactions", {}
        )
        self._transactions.setdefault("trade", [])
        self._transactions.setdefault("add_or_drop", [])

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
            "week_data": deepcopy(self._week_data),
            "transactions": deepcopy(self._transactions),
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

    def get_metadata(self) -> dict[str, Any]:
        """Get manager metadata.

        Returns:
            Manager metadata
        """
        return {
            "name": self.real_name,
            "first_name": self.real_name,
            "last_name": "",
            "image_url": self.image_url,
            "user_id": self.user_id,
            "username": self.username,
            "provide_link": True,
        }

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

    def set_playoff_placement(self, year: str, playoff_placement: int) -> None:
        """Set manager playoff placement.

        Args:
            year: The year.
            playoff_placement: The playoff placement.
        """
        self._season_data[year]["playoff_placement"] = playoff_placement
        self._apply_to_cache()

    def set_playoff_appearance(self, year: str) -> None:
        """Set manager playoff appearance.

        Args:
            year: The year.
        """
        self._season_data[year]["playoff_appearance"] = True
        self._apply_to_cache()

    def set_week_data(
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
        self._week_data[f"{year}_{week}"] = {
            "opponent": str(opponent),
            "result": result,
            "points_for": points_for,
            "points_against": points_against,
            "starters": [str(p) for p in starters],
            "rostered": [str(p) for p in rostered],
            "matchup_type": matchup_type,
        }

        self._apply_to_cache()

    def set_transaction(
        self,
        transaction_id: str,
        transaction_type: Literal["trade", "add_or_drop"],
    ) -> None:
        """Set manager transaction.

        Args:
            transaction_id: The transaction ID.
            transaction_type: The transaction type.
        """
        if transaction_type == "trade":
            self._transactions["trade"].append(transaction_id)
        elif transaction_type == "add_or_drop":
            self._transactions["add_or_drop"].append(transaction_id)

        self._apply_to_cache()

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

    def check_participation(
        self, year: str | None = None, week: str | None = None
    ) -> bool:
        """Check if a manager participates in a given year and week.

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

        return f"{year}_{week}" in self._week_data

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
        from patriot_center_backend.models.player import Player

        if week and not year:
            logger.warning(
                f"Week {week} provided without year for "
                f"manager {self.real_name}"
            )
            return []

        matches = self._get_matching_data(
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

        return [Player(p) for p in players]

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
        matches = self._get_matching_data(
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

        if wins + losses + ties == 0:
            return {}

        return {
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "points_for": round(points_for, 2),
            "points_against": round(points_against, 2),
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
            year=year, week=week,
            only_starters=True, suppress_warnings=True,
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

    def get_matchup_data(self, year: str, week: str) -> dict[str, Any]:
        """Get matchup data for a given year and week.

        Args:
            year: The year of the matchup.
            week: The week of the matchup.

        Returns:
            A dictionary containing the matchup data.
        """
        data = self._week_data.get(f"{year}_{week}", {})
        if not data:
            return {}

        data = deepcopy(data)
        data["opponent"] = Manager(data["opponent"])
        data["starters"] = [Player(p) for p in data["starters"]]
        data["rostered"] = [Player(p) for p in data["rostered"]]

        return data

    def get_playoff_appearances_list(self) -> list[int]:
        """Get the years in which the manager appeared in the playoffs."""
        years = []
        for year, data in self._season_data.items():
            if data["playoff_appearance"]:
                years.append(int(year))

        return years

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
        matchups = self._get_matching_data(
            year=year,
            result=result,
            opponent=opponent
        )
        if not matchups:
            return {}
        last_matchup = matchups[-1]

        return self.get_matchup_data(last_matchup["year"], last_matchup["week"])

    def _get_matching_data(
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
        if not self._week_data:
            return []

        if year and week:
            data = self.get_matchup_data(year, week)
            if not data:
                return []
            if player:
                if str(player) not in data["rostered"]:
                    return []
                if only_starters and str(player) not in data["starters"]:
                    return []
            if matchup_type and data["matchup_type"] != matchup_type:
                return []
            if opponent and data["opponent"] != str(opponent):
                return []
            if result and data["result"] != result:
                return []
            return_data = deepcopy(data)
            return_data["year"] = year
            return_data["week"] = week
            return [return_data]

        matches = []
        for key in self._week_data:
            data_year, data_week = key.split("_")
            if year and data_year != year:
                continue
            if week and data_week != week:
                continue
            recursive_matches = self._get_matching_data(
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
