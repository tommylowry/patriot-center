

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
            self.is_real_player = False
            self._initialize_faab()
        elif " draft pick" in player_id.lower():
            self.is_real_player = False
            self._initialize_draft_pick()
        else:
            self.is_real_player = True
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

        Raises:
            ValueError: If the player is not a real player
        """
        if not self.is_real_player:
            raise ValueError(
                f"Player {self.player_id} is not a real player"
            )

        self._data[f"{year}_{week}"] = {
            "score": score,
            "ffwar": ffwar,
            "manager": manager,
            "started": started,
        }
        self._apply_to_cache()

    def set_transaction(
        self, year: str, week: str, transaction_id: str
    ) -> None:
        """Set player data for a given transaction.

        Args:
            year: The year.
            week: The week.
            transaction_id: The transaction ID.

        Raises:
            ValueError: If the player is not a real player
        """
        if not self.is_real_player:
            raise ValueError(
                f"Player {self.player_id} is not a real player"
            )

        if transaction_id in self._transactions:
            return

        self._transactions.append(transaction_id)
        self._apply_to_cache()

    def remove_transaction(
        self, year: str, week: str, transaction_id: str
    ) -> None:
        """Remove player data for a given transaction.

        Args:
            year: The year.
            week: The week.
            transaction_id: The transaction ID.

        Raises:
            ValueError: If the player is not a real player
        """
        if not self.is_real_player:
            raise ValueError(
                f"Player {self.player_id} is not a real player"
            )

        if transaction_id not in self._transactions:
            return

        # Remove from transactions
        self._transactions.remove(transaction_id)
        self._apply_to_cache()

    def _get_data(
        self,
        year: str | None,
        week: str | None,
        manager: str | None,
        only_started: bool,
        data_type: Literal["score", "ffwar"],
    ) -> float:
        """Get the player's data for a given week.

        Args:
            year: The year.
            week: The week.
            manager: The manager.
            only_started: Whether to only return the player's data if they
                started the week.
            data_type: The data type to return.

        Returns:
            The player's data.
        """
        if year and week:
            data = self._data.get(f"{year}_{week}")
            if not data:
                logger.warning(
                    f"Player {self.full_name} ({self.player_id}) "
                    f"does not have data for {year} week {week}."
                )
                return 0.0
            if manager and data["manager"] != manager:
                logger.warning(
                    f"Player {self.full_name} ({self.player_id}) "
                    f"does not have data for {year} week {week} "
                    f"from manager {manager}."
                )
                return 0.0
            if only_started and not data["started"]:
                logger.warning(
                    f"Player {self.full_name} ({self.player_id}) "
                    f"did not start {year} week {week}."
                )
                return 0.0

            return data[data_type]

        data_num = 0.0
        count = 0
        for key in self._data:
            data_year, data_week = key.split("_")
            if year and data_year != year:
                continue
            if week and data_week != week:
                continue
            if manager and self._data[key]["manager"] != manager:
                continue
            if only_started and not self._data[key]["started"]:
                continue

            data_num += self._data[key][data_type]
            count += 1

        if count == 0:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return 0.0

        return data_num

    def get_score(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = False,
    ) -> float:
        """Get the player's score for a given week.

        Args:
            year: The year.
            week: The week.
            manager: The manager.
            only_started: Whether to only return the player's data if they
                started the week.

        Returns:
            The player's score.

        Raises:
            ValueError: If the player is not a real player
        """
        if not self.is_real_player:
            raise ValueError(
                f"Player {self.player_id} is not a real player"
            )

        return self._get_data(year, week, manager, only_started, "score")

    def get_ffwar(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = False,
    ) -> float:
        """Get the player's ffWAR for a given week.

        Args:
            year: The year.
            week: The week.
            manager: The manager.
            only_started: Whether to only return the player's data if they
                started the week.

        Returns:
            The player's ffWAR.

        Raises:
            ValueError: If the player is not a real player
        """
        if not self.is_real_player:
            raise ValueError(
                f"Player {self.player_id} is not a real player"
            )

        return self._get_data(year, week, manager, only_started, "ffwar")
