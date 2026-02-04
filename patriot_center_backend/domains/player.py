

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


class Player:
    """Player class."""

    def __init__(self, player_id: str) -> None:
        """Player class.

        Args:
            player_id: The player ID
        """
        self.player_id: str = player_id
        self._load_from_cache()

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

        # Set years and transactions
        self._years: dict[str, dict[str, dict[str, Any]]] = player_data.get(
            "years", {}
        )
        self._transactions: list[str] = player_data.get("transactions", [])

        if metadata_from_player_ids_cache:
            self.apply_to_cache()

    def apply_to_cache(self) -> None:
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
            "years": self._years,
            "transactions": self._transactions,
        }

    def _ensure_year_week(self, year: str, week: str) -> None:
        """Ensure that the year and week exist in the player data.

        Args:
            year: The year.
            week: The week.
        """
        if year not in self._years:
            self._years[year] = {}

        if week not in self._years[year]:
            self._years[year][week] = {"transactions": []}

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
            score: The player's score.
            ffwar: The player's ffWar.
            manager: The player's manager.
            started: Whether the player started.
        """
        self._ensure_year_week(year, week)

        self._years[year][week]["score"] = score
        self._years[year][week]["ffWar"] = ffwar
        self._years[year][week]["manager"] = manager  # TODO: change to Manager
        self._years[year][week]["started"] = started

    def set_transaction(
        self, year: str, week: str, transaction_id: str
    ) -> None:
        """Set player data for a given transaction.

        Args:
            year: The year.
            week: The week.
            transaction_id: The transaction ID.
        """
        if transaction_id in self._transactions:
            return

        self._ensure_year_week(year, week)

        # TODO: change to Transaction class instead of using id

        # Add to transactions
        self._transactions.append(transaction_id)

        # Add to years
        self._years[year][week]["transactions"].append(transaction_id)
