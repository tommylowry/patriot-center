"""Player class.

This module defines the Player class, which represents a player in the game.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from functools import cache
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import Position

if TYPE_CHECKING:
    from patriot_center_backend.models.manager import Manager

logger = logging.getLogger(__name__)


class Player:
    """Player class.

    Uses singleton pattern via __new__ - instances are stored in
    _instances and never garbage collected. B019 warnings for
    @cache on methods are safe to suppress in this context.
    """
    _instances: ClassVar[dict[str, Player]] = {}

    def __new__(cls, player_id: str, apply: bool = True) -> Player:
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
        # Weird edge case with Zach Ertz traded, his player_id shows twice in
        # 2021 week 6, and one is 1339z
        if player_id == "1339z":
            self._is_real_player = False
            return

        self._apply = apply

        if hasattr(self, "_initialized"):
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

    def __eq__(self, other: object) -> bool:
        """Equality operator for Player class.

        Args:
            other: The object to compare to.

        Returns:
            True if the objects are equal, False otherwise.
        """
        if not isinstance(other, Player):
            return NotImplemented

        return self.player_id == other.player_id

    def __ne__(self, other: object) -> bool:
        """Inequality operator for Player class.

        Args:
            other: The object to compare to.

        Returns:
            True if the objects are not equal, False otherwise.
        """
        return not self == other

    def __hash__(self) -> int:
        """Hash function for Player class.

        Returns:
            The hash of the player.
        """
        return hash(self.player_id)

    @classmethod
    def load_all_players(cls) -> None:
        """Load all players into the cache."""
        cls.get_players()

    @classmethod
    def get_players(
        cls,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
        only_started: bool = True,
    ) -> list[Player]:
        """Get players matching filters.

        Args:
            year: Filter by year
            week: Filter by week
            manager: Filter by manager
            only_started: Whether to only return players who started

        Returns:
            List of players matching filters.
        """
        player_cache = CACHE_MANAGER.get_player_cache()

        players = []
        for player_id in player_cache:
            player = cls(player_id)
            if only_started:
                if player.has_started(year=year, week=week, manager=manager):
                    players.append(player)
            else:
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
            "type": "player",
        }

    def set_week_data(
        self,
        year: str,
        week: str,
        points: float | None = None,
        ffwar: float | None = None,
        manager: Manager | None = None,
        started: bool | None = None,
    ) -> None:
        """Set player data for a given week.

        Args:
            year: The year.
            week: The week.
            points: The points.
            ffwar: The ffWAR.
            manager: The manager.
            started: Whether the player started the week.
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
        if manager is not None:
            self._data[f"{year}_{week}"]["manager"] = str(manager)
        if started is not None:
            self._data[f"{year}_{week}"]["started"] = started

        self._apply_to_cache()

    def set_placement(
        self, year: str, manager: Manager, placement: int
    ) -> None:
        """Set player placement for a given manager.

        Args:
            year: The year.
            manager: The manager.
            placement: The placement.
        """
        if not self._is_real_player:
            return

        self._placements[f"{year}_{manager!s}"] = placement

        self._apply_to_cache()

    @cache  # noqa: B019
    def get_points(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
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
        return round(sum(d.get("points", 0.0) for d in matches), 2)

    @cache  # noqa: B019
    def get_ffwar(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
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

    @cache  # noqa: B019
    def get_managers(
        self,
        year: str | None = None,
        week: str | None = None,
        only_started: bool = True,
        only_rostered: bool = True,
    ) -> list[Manager]:
        """Get the player's managers for matching weeks.

        Args:
            year: Filter by year.
            week: Filter by week.
            only_started: Only include weeks where player started.
            only_rostered: Only include weeks where player is rostered.

        Returns:
            The player's managers
        """
        from patriot_center_backend.models.manager import Manager

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
        return [Manager(d["manager"]) for d in matches]

    def get_num_games(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
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
        manager: Manager | None = None,
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

    def get_placement(
        self, year: str | None = None, manager: Manager | None = None
    ) -> dict[str, int]:
        """Get the player's placement for a given year.

        Args:
            year: Filter by year.
            manager: Filter by manager.

        Returns:
            The player's placement or a dictionary of placements for each
            manager if manager is provided.
        """
        if not self._is_real_player:
            return {}

        if not year and not manager:
            return self._placements

        if year and manager:
            placement = self._placements.get(f"{year}_{manager!s}")
            if placement is None:
                return {}
            else:
                return {f"{year}_{manager!s}": placement}

        placements = {}
        for key, placement in self._placements.items():
            placement_year, placement_manager = key.split("_")
            if year and placement_year != year:
                continue
            if manager and placement_manager != str(manager):
                continue
            placements[key] = placement

        return placements

    def has_started(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
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
        return (
            self.get_num_games(
                year=year,
                week=week,
                manager=manager,
                only_started=True,
                only_rostered=True,
            )
            > 0
        )

    @cache  # noqa: B019
    def get_scoring_summary(
        self,
        year: str | None = None,
        week: str | None = None,
        manager: Manager | None = None,
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

        # Round total_points to 2 decimal places and ffWAR to 3
        raw_dict["total_points"] = round(raw_dict["total_points"], 2)
        raw_dict["ffWAR"] = round(raw_dict["ffWAR"], 3)

        if raw_dict["num_games_started"] == 0:
            raw_dict["ffWAR_per_game"] = 0.0
        else:
            raw_dict["ffWAR_per_game"] = round(
                raw_dict["ffWAR"] / raw_dict["num_games_started"], 3
            )

        placements = self.get_placement(year, manager)
        if not placements:
            return raw_dict
        for key, placement in placements.items():
            placement_year, placement_user_id = key.split("_")

            (
                raw_dict.setdefault("playoff_placement", {}).setdefault(
                    Manager(placement_user_id).real_name, {}
                )[placement_year]
            ) = placement

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

        # Position
        try:  # If a position isn't in Position, it will make position None
            self.position = Position(metadata["position"])
        except ValueError:
            self._is_real_player = False
            return

        # Required Metadata
        self.first_name: str = metadata["first_name"]
        self.last_name: str = metadata["last_name"]
        self.full_name: str = metadata.get("full_name", "")
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}"

        # Optional Metadata
        self.age: int | None = metadata.get("age")
        self.years_exp: int | None = metadata.get("years_exp")
        self.college: str | None = metadata.get("college")
        self.team: str | None = metadata.get("team")
        self.number: int | None = metadata.get("number")
        self._placements: dict[str, int] = metadata.get("placements", {})

        # Set data
        self._data: dict[str, dict[str, Any]] = player_data.get("data", {})

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

    def _set_image_url(self) -> None:
        if self.player_id.isnumeric():
            self.image_url = (
                f"https://sleepercdn.com/content/nfl"
                f"/players/{self.player_id}.jpg"
            )
        elif "faab" in self.player_id.lower():
            self.image_url = (
                "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
            )
        elif "draft pick" in self.player_id.lower():
            self.image_url = (
                "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
                "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
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
                "position": self.position,
                "number": self.number,
                "image_url": self.image_url,
                "placements": self._placements,
            },
            "data": deepcopy(self._data),
        }

    def _get_matching_data(
        self,
        year: str | None,
        week: str | None,
        only_started: bool,
        only_rostered: bool,
        manager: Manager | None = None,
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
            if manager and data["manager"] != str(manager):
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
            if manager and data["manager"] != str(manager):
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

            # Add manager placement if available
            manager = Manager(match["manager"])
            if (  # If manager placement is already set, skip
                key_level.get("playoff_placement")
                .get(manager.real_name)
                .get(match["year"])
                is not None
            ):
                continue

            placements = self.get_placement(
                match["year"], Manager(match["manager"])
            )
            placement = placements.get(f"{match['year']}_{match['manager']}")
            if not placement:
                continue

            (
                key_level.setdefault("playoff_placement", {}).setdefault(
                    Manager(match["manager"]).real_name, {}
                )[match["year"]]
            ) = placement

        for key_value in list(grouped.keys()):
            key_level = grouped[key_value]

            key_level["total_points"] = round(key_level["total_points"], 2)
            key_level["ffWAR"] = round(key_level["ffWAR"], 3)

            if key_level["num_games_started"] == 0:
                key_level["ffWAR_per_game"] = 0.0
            else:
                key_level["ffWAR_per_game"] = round(
                    key_level["ffWAR"] / key_level["num_games_started"], 3
                )

        return grouped
