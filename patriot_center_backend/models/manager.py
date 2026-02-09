"""Manager class."""

import logging
from copy import deepcopy
from time import time
from typing import Any, ClassVar, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import USERNAME_TO_REAL_NAME

logger = logging.getLogger(__name__)


class Manager:
    """Manager class."""

    _instances: ClassVar[dict[str, "Manager"]] = {}

    def __new__(cls, user_id: str) -> "Manager":
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
    ) -> list["Manager"]:
        """Get players who have started at least one game matching filters.

        Args:
            year: Filter by year
            week: Filter by week
            manager: Filter by manager

        Returns:
            List of players who have started at least one game matching filters
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        managers = []
        for user_id in manager_cache:
            manager = cls(user_id)
            if manager.participates_in_season(year, week):
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
        }

    def set_season_data(
        self,
        year: str,
        week: str,
        team_image_url: str,
        team_name: str,
        season_complete: bool,
        roster_id: int,
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
        """
        if (  # If season already set and complete
            self._season_data.get(year)
            and self._season_data[year]["season_complete"]
        ):
            if week not in self._season_data[year]["weeks"]:
                self._season_data[year]["weeks"].append(week)
            return

        self._season_data[year] = {
            "team_image_url": team_image_url,
            "team_name": team_name,
            "season_complete": season_complete,
            "roster_id": roster_id,
            "weeks": [week],
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

    def set_week_data(
        self,
        year: str,
        week: str,
        opponent: str,
        result: str,
        points_for: float,
        points_against: float,
        starters: list[str],
        rostered_players: list[str]
    ) -> None:
        """Set manager week data.

        Args:
            year: The year.
            week: The week.
            opponent: The opponent.
            result: The result.
            points_for: The points for.
            points_against: The points against.
            starters: The starters.
            rostered_players: The rostered players.
        """
        self._week_data[year][week] = {
            "opponent": opponent,
            "result": result,
            "points_for": points_for,
            "points_against": points_against,
            "starters": starters,
            "rostered_players": rostered_players,
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

    def participates_in_season(
        self, year: str | None = None, week: str | None = None
    ) -> bool:
        """Check if a manager participates in a given season and week.

        Args:
            year: The year.
            week: The week.

        Returns:
            True if the manager participates in the given season and week,
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

        if year not in self._season_data:
            return False

        if not week:
            return True

        return week in self._season_data[year]["weeks"]
