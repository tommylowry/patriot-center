

import logging
from copy import deepcopy
from typing import Any, Literal

from patriot_center_backend.cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class Player:
    """Player class."""

    def __init__(self, player_id: str) -> None:
        """Player class.

        Args:
            player_id: The player ID
        """
        self.player_id: str = player_id

        if " faab" in player_id.lower():
            self._is_real_player = False
            self._initialize_faab()
        elif " draft pick" in player_id.lower():
            self._is_real_player = False
            self._initialize_draft_pick()
        else:
            self._is_real_player = True
            self._load_from_cache()

    def __str__(self) -> str:
        """String representation of the player.

        Returns:
            The player ID
        """
        return self.player_id

    def _load_from_cache(self) -> None:
        """Loads player data from cache.

        Raises:
            ValueError: Player not found
        """
        player_cache = CACHE_MANAGER.get_player_cache()
        player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

        # Get player data
        player_data = deepcopy(player_cache.get(self.player_id, {}))

        # Check player IDs cache first in case
        # there is an update to the metadata
        metadata_from_player_ids_cache = False
        if self.player_id in player_ids_cache:

            # TODO: pop not get for the future
            metadata = deepcopy(player_ids_cache.get(self.player_id))
            metadata_from_player_ids_cache = True
        else:
            metadata = player_data.get("metadata", {})
        if not metadata:
            raise ValueError(f"Player with ID {self.player_id} not found")

        # Required Metadata
        self.full_name: str = metadata["full_name"]
        self.first_name: str = metadata["first_name"]
        self.last_name: str = metadata["last_name"]
        self.position: str = metadata["position"]
        self.slug: str = metadata["slug"]
        self.image_url: str = metadata["image_url"]
        self.fantasy_positions: list[str] = metadata["fantasy_positions"]

        # Optional Metadata
        self.age: int | None = metadata.get("age")
        self.years_exp: int | None = metadata.get("years_exp")
        self.college: str | None = metadata.get("college")
        self.team: str | None = metadata.get("team")
        self.depth_chart_position: str | None = metadata.get(
            "depth_chart_position"
        )
        self.number: int | None = metadata.get("number")

        # Set data, data_map, and transactions
        self._data: dict[str, dict[str, Any]] = player_data.get(
            "data", {}
        )
        self._transactions: list[str] = player_data.get("transactions", [])

        if metadata_from_player_ids_cache:
            self._apply_to_cache()

    def _initialize_faab(self) -> None:
        """Initialize FAAB player."""
        self.full_name = self.player_id
        self.first_name = self.player_id.split(" ")[0]
        self.last_name = self.player_id.split(" ")[1]
        self.image_url = (
            "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
        )

    def _initialize_draft_pick(self) -> None:
        """Initialize draft pick player."""
        abridged_name = self.player_id.replace(" Draft Pick", "")
        abridged_name = abridged_name.replace("Round ", "R")

        self.full_name = self.player_id
        self.first_name = abridged_name.split(" ")[0]
        self.last_name = abridged_name.replace(f"{self.first_name} ", "")
        self.image_url = (
            "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
            "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
        )

    def _apply_to_cache(self) -> None:
        """Applies the player data to the cache."""
        player_cache = CACHE_MANAGER.get_player_cache()

        player_cache[self.player_id] = {
            "metadata": {
                "full_name": self.full_name,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "age": self.age,
                "years_exp": self.years_exp,
                "college": self.college,
                "team": self.team,
                "depth_chart_position": self.depth_chart_position,
                "fantasy_positions": self.fantasy_positions,
                "position": self.position,
                "number": self.number,
                "slug": self.slug,
                "image_url": self.image_url,
            },
            "data": self._data,
            "transactions": self._transactions,
        }

    def set_week_data(
        self,
        year: str,
        week: str,
        score: float,
        ffwar: float,
        manager: str | None,
        started: bool
    ) -> None:
        """Set player data for a given week.

        Args:
            year: The year.
            week: The week.
            score: The score.
            ffwar: The ffWAR.
            manager: The manager.
            started: Whether the player started the week.
        """
        if not self._is_real_player:
            return

        self._data[f"{year}_{week}"] = {
            "score": score,
            "ffwar": ffwar,
            "manager": manager,
            "started": started,
        }
        self._apply_to_cache()

    def set_transaction(self, transaction_id: str) -> None:
        """Set player data for a given transaction.

        Args:
            year: The year.
            week: The week.
            transaction_id: The transaction ID.
        """
        if not self._is_real_player or transaction_id in self._transactions:
            return

        self._transactions.append(transaction_id)
        self._apply_to_cache()

    def remove_transaction(self, transaction_id: str) -> None:
        """Remove player data for a given transaction.

        Args:
            year: The year.
            week: The week.
            transaction_id: The transaction ID.
        """
        if not self._is_real_player or transaction_id not in self._transactions:
            return

        # Remove from transactions
        self._transactions.remove(transaction_id)
        self._apply_to_cache()

    def _get_matching_data(
        self,
        year: str | None,
        week: str | None,
        only_started: bool,
        manager: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all data entries matching the given filters.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_started: Only include weeks where player started.
            manager: Filter by manager.

        Returns:
            List of matching data entries.
        """
        if year and week:
            data = self._data.get(f"{year}_{week}")
            if not data:
                return []
            if manager and data["manager"] != manager:
                return []
            if only_started and not data["started"]:
                return []
            return [data]

        matches = []
        for key, data in self._data.items():
            data_year, data_week = key.split("_")
            if year and data_year != year:
                continue
            if week and data_week != week:
                continue
            if manager and data["manager"] != manager:
                continue
            if only_started and not data["started"]:
                continue
            matches.append(data)

        return matches

    def get_score(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = False,
    ) -> float:
        """Get the player's total score for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.

        Returns:
            The player's total score
        """
        if not self._is_real_player:
            return 0.0

        matches = self._get_matching_data(
            year, week, only_started, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return 0.0
        return sum(d["score"] for d in matches)


    def get_ffwar(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = False,
    ) -> float:
        """Get the player's total ffWAR for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.

        Returns:
            The player's total ffWAR
        """
        if not self._is_real_player:
            return 0.0

        matches = self._get_matching_data(
            year, week, only_started, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return 0.0
        return sum(d["ffwar"] for d in matches)


    def get_managers(
        self,
        year: str | None = None,
        week: str | None = None,
        only_started: bool = False,
    ) -> list[str]:
        """Get the player's managers for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_started: Only include weeks where player started.

        Returns:
            The player's managers
        """
        if not self._is_real_player:
            return []

        matches = self._get_matching_data(year, week, only_started)
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return []
        return [d["manager"] for d in matches]

    def get_scoring_summary(
        self,
        key: Literal["manager", "year"] = "manager",
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = False
    ) -> dict[str, Any]:
        """Get a summary of the player's scoring data.

        Args:
            key: The key to group by.
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.

        Returns:
            The player's scoring summary
        """
        if not self._is_real_player:
            return {}

        matches = self._get_matching_data(
            year, week, only_started, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return {}

        return self._group_matches(key, matches)

    def _group_matches(
        self, key: Literal["manager", "year"], matches: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Group matches by the specified key.

        Args:
            key: The key to group by.
            matches: The matches to group.

        Returns:
            The grouped matches
        """
        grouped = {}

        for match in matches:
            key_value = match[key]
            if key_value not in grouped:
                grouped[key_value] = {
                    "score": 0.0,
                    "ffwar": 0.0,
                }
            grouped[key_value]["score"] += match["score"]
            grouped[key_value]["ffwar"] += match["ffwar"]

        return grouped
