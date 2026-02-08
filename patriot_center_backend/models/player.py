"""Player class.

This module defines the Player class, which represents a player in the game.
"""

import logging
from copy import deepcopy
from typing import Any, ClassVar, Literal

from patriot_center_backend.cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class Player:
    """Player class."""
    _instances: ClassVar[dict[str, "Player"]] = {}

    def __new__(cls, player_id: str, apply: bool = True) -> "Player":
        """Create a new player instance or return the existing one.

        Args:
            player_id: The player ID
            apply: Whether to apply the player to the player cache

        Returns:
            The player instance
        """
        if player_id in cls._instances:
            return cls._instances[player_id]
        instance = super().__new__(cls)
        cls._instances[player_id] = instance
        return instance

    def __init__(self, player_id: str, apply: bool = True) -> None:
        """Player class.

        Args:
            player_id: The player ID
            apply: Whether to apply the player to the player cache
        """
        self._apply = apply

        if hasattr(self, '_initialized'):
            return  # Already initialized
        self._initialized = True

        self.player_id = player_id

        self._set_image_url()

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

    @classmethod
    def get_all_starters(
        cls,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
    ) -> list["Player"]:
        """Get players who have started at least one game matching filters.

        Args:
            year: Filter by year
            week: Filter by week
            manager: Filter by manager

        Returns:
            List of players who have started at least one game matching filters
        """
        player_cache = CACHE_MANAGER.get_player_cache()

        players = []
        for player_id in player_cache:
            player = cls(player_id)
            if player.has_started(year=year, week=week, manager=manager):
                players.append(player)

        return players

    def get_metadata(self) -> dict[str, Any]:
        """Get player metadata.

        Returns:
            Player metadata
        """
        if not self._is_real_player:
            return {
                "name": self.full_name,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "image_url": self.image_url,
                "provide_link": False,
            }
        return {
            "name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "image_url": self.image_url,
            "player_id": self.player_id,
            "position": self.position,
            "team": self.team,
            "provide_link": self.has_started(),
        }

    def set_week_data(
        self,
        year: str,
        week: str,
        points: float | None = None,
        ffwar: float | None = None,
        manager: str | None = "",
        started: bool | None = None,
        playoff_placement: int | None = None,
    ) -> None:
        """Set player data for a given week.

        Args:
            year: The year.
            week: The week.
            points: The points.
            ffwar: The ffWAR.
            manager: The manager.
            started: Whether the player started the week.
            playoff_placement: The playoff placement.
        """
        if not self._is_real_player:
            return

        if f"{year}_{week}" not in self._data:
            self._data[f"{year}_{week}"] = {
                "manager": None,
                "started": False,
            }

        if points is not None:
            self._data[f"{year}_{week}"]["points"] = points
        if ffwar is not None:
            self._data[f"{year}_{week}"]["ffwar"] = ffwar
        if manager != "":
            self._data[f"{year}_{week}"]["manager"] = manager
        if started is not None:
            self._data[f"{year}_{week}"]["started"] = started
        if playoff_placement is not None:
            self._data[f"{year}_{week}"]["playoff_placement"] = (
                playoff_placement
            )

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

    def get_points(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> float:
        """Get the player's total points for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's total points
        """
        if not self._is_real_player:
            return 0.0

        matches = self._get_matching_data(
            year, week, only_started, only_rostered, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return 0.0
        return round(sum(d["points"] for d in matches), 2)

    def get_ffwar(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> float:
        """Get the player's total ffWAR for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's total ffWAR
        """
        if not self._is_real_player:
            return 0.0

        matches = self._get_matching_data(
            year, week, only_started, only_rostered, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return 0.0
        return round(sum(d["ffwar"] for d in matches), 3)

    def get_managers(
        self,
        year: str | None = None,
        week: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True
    ) -> list[str]:
        """Get the player's managers for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's managers
        """
        if not self._is_real_player:
            return []

        matches = self._get_matching_data(
            year, week, only_started, only_rostered
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return []
        return [d["manager"] for d in matches]

    def get_num_games(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> int:
        """Get the player's number of games for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's number of games
        """
        return len(
            self._get_matching_data(
                year, week, only_started, only_rostered, manager=manager
            )
        )

    def get_grouped_scoring_summary(
        self,
        group_by: Literal["manager", "year"] = "manager",
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> dict[str, Any]:
        """Get a summary of the player's scoring data grouped by the given key.

        Args:
            group_by: The key to group by.
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's summary
        """
        if not self._is_real_player:
            return {}

        if (manager and group_by == "manager") or (year and group_by == "year"):
            return self.get_scoring_summary(
                year, week, manager, only_started, only_rostered
            )

        matches = self._get_matching_data(
            year, week, only_started, only_rostered, manager=manager
        )
        if not matches:
            logger.warning(
                f"Player {self.full_name} ({self.player_id}) "
                f"does not have data for the given parameters."
            )
            return {}

        return self._group_matches(group_by, matches)

    def has_started(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
    ) -> bool:
        """Check if player has started at least one game matching filters.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.

        Returns:
            True if player has started at least one matching game.
        """
        if not self._is_real_player:
            return False
        return self.get_num_games(
            year=year,
            week=week,
            manager=manager,
            only_started=True,
            only_rostered=True,
        ) > 0

    def get_scoring_summary(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> dict[str, Any]:
        """Get a summary of the player's scoring data.

        Args:
            year: Filter by year.
            week: Filter by week.
            manager: Filter by manager.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's summary
        """
        from patriot_center_backend.calculations.ffwar_calculator import (
            FFWARCalculator,
        )
        if not self._is_real_player:
            return {}

        matches = self._get_matching_data(
            year, week, only_started, only_rostered, manager=manager
        )

        raw_dict = {
            "total_points": 0.0,
            "ffWAR": 0.0,
            "num_games_started": 0,
        }

        # Add up the total points, ffWAR, and number of games started
        for match in matches:
            points = match.get("points")
            ffwar = match.get("ffwar")

            # If a manager started a player but player didn't play in real life
            if points is None:
                points = 0.0

                # The player was technically started in fantasy so their ffWAR
                # needs to be calculated and shared for the scoring summary but
                # not stored in the database as an actual ffWAR value set
                # against them.
                ffwar_calculator = FFWARCalculator(match["year"], match["week"])
                ffwar = ffwar_calculator.calculate_ffwar_for_player(
                    0.0, self.position
                )

            raw_dict["total_points"] += points
            raw_dict["ffWAR"] += ffwar
            raw_dict["num_games_started"] += 1

            # Add playoff placement if available
            if "playoff_placement" in match:
                (
                    raw_dict
                    .setdefault("playoff_placement", {})
                    .setdefault(match["manager"], {})
                )[match["year"]] = match["playoff_placement"]

        # Round total_points to 2 decimal places and ffWAR to 3
        raw_dict["total_points"] = round(
            raw_dict["total_points"], 2
        )
        raw_dict["ffWAR"] = round(raw_dict["ffWAR"], 3)

        if raw_dict["num_games_started"] == 0:
            raw_dict["ffWAR_per_game"] = 0.0
        else:
            raw_dict["ffWAR_per_game"] = round(
                raw_dict["ffWAR"] / raw_dict["num_games_started"], 3
            )

        return raw_dict

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
        self.first_name: str = metadata["first_name"]
        self.last_name: str = metadata["last_name"]
        self.position: str = metadata["position"]
        self.fantasy_positions: list[str] = metadata["fantasy_positions"]

        self.full_name: str = metadata.get("full_name", "")
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}"

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

    def _set_image_url(self) -> None:
        if "faab" in self.player_id.lower():
            self.image_url = (
                "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
            )
        elif "draft pick" in self.player_id.lower():
            self.image_url = (
                "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
                "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
            )
        elif self.player_id.isnumeric():
            self.image_url = (
                f"https://sleepercdn.com/content/nfl"
                f"/players/{self.player_id}.jpg"
            )
        else:
            self.image_url = (
                f"https://sleepercdn.com/images/team_logos"
                f"/nfl/{self.player_id.lower()}.png"
            )

    def _apply_to_cache(self) -> None:
        """Applies the player data to the cache."""
        if not self._apply:
            return
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
                "image_url": self.image_url,
            },
            "data": deepcopy(self._data),
            "transactions": deepcopy(self._transactions),
        }

    def _get_matching_data(
        self,
        year: str | None,
        week: str | None,
        only_started: bool,
        only_rostered: bool,
        manager: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all data entries matching the given filters.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.
            manager: Filter by manager.

        Returns:
            List of matching data entries.
        """
        if not self._data:
            return []
        if year and week:
            data = self._data.get(f"{year}_{week}")
            if not data:
                return []
            if manager and data["manager"] != manager:
                return []
            if only_started and not data["started"]:
                return []
            if only_rostered and data["manager"] is None:
                return []
            data["year"] = year
            data["week"] = week
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
            if only_rostered and data["manager"] is None:
                continue
            data["year"] = data_year
            data["week"] = data_week
            matches.append(data)

        return matches

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
                    "total_points": 0.0,
                    "ffWAR": 0.0,
                    "num_games_started": 0,
                }
            key_level = grouped[key_value]

            key_level["total_points"] += match["points"]
            key_level["ffWAR"] += match["ffwar"]
            key_level["num_games_started"] += 1

            if "playoff_placement" in match:
                (
                    key_level
                    .setdefault("playoff_placement", {})
                    .setdefault(match["manager"], {})
                )[match["year"]] = match["playoff_placement"]

        for key_value in list(grouped.keys()):
            key_level = grouped[key_value]

            key_level["total_points"] = round(
                key_level["total_points"], 2
            )
            key_level["ffWAR"] = round(key_level["ffWAR"], 3)

            if key_level["num_games_started"] == 0:
                key_level["ffWAR_per_game"] = 0.0
            else:
                key_level["ffWAR_per_game"] = round(
                    key_level["ffWAR"] / key_level["num_games_started"], 3
                )

        return grouped
