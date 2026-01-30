"""This module provides utility functions for updating the cache."""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.helpers import recursive_replace

logger = logging.getLogger(__name__)


class CacheSynchronizer:
    """This class provides utility functions for updating the cache."""

    def __init__(
        self,
        old_ids: dict[str, dict[str, Any]],
        new_ids: dict[str, dict[str, Any]],
    ) -> None:
        """Initialize the cache synchronizer with the old and new player IDs.

        Args:
            old_ids: The old player IDs
            new_ids: The new player IDs
        """
        self.old_ids = old_ids
        self.new_ids = new_ids

        self._check_for_name_changes()

    def _check_for_name_changes(self) -> None:
        """Check for name changes between the old and new player IDs."""
        for id in self.new_ids:
            # New player entirely being added, continue
            if id not in self.new_ids:
                continue

            if self.old_ids[id]["full_name"] != self.new_ids[id]["full_name"]:
                logger.info("New Player Name Found:")
                logger.info(
                    f"\t'{self.old_ids[id]['full_name']}' has changed "
                    f"his name to '{self.new_ids[id]['full_name']}'"
                )

                self._update_player_names(id)

    def _update_player_names(self, player_id: str) -> None:
        """Update the player names in the cache.

        Args:
            player_id: The player ID
        """
        old_name = self.old_ids[player_id]["full_name"]
        new_name = self.new_ids[player_id]["full_name"]

        self._update_manager_metadata(old_name, new_name)
        self._update_player_data(old_name, new_name)
        self._update_starters(old_name, new_name)
        self._update_transaction_ids(old_name, new_name)
        self._update_valid_options(old_name, new_name)
        self._update_players(old_name, new_name)
        self._update_image_urls(player_id)

    def _update_manager_metadata(self, old_name: str, new_name: str) -> None:
        """Update the manager metadata in the cache.

        Args:
            old_name: The old manager name
            new_name: The new manager name
        """
        manager_metadata_cache = CACHE_MANAGER.get_manager_cache()

        manager_metadata_cache = recursive_replace(
            manager_metadata_cache, old_name, new_name
        )

    def _update_player_data(self, old_name: str, new_name: str) -> None:
        """Update the player data in the cache.

        Args:
            old_name: The old player name
            new_name: The new player name
        """
        player_data_cache = CACHE_MANAGER.get_player_data_cache()

        player_data_cache = recursive_replace(
            player_data_cache, old_name, new_name
        )

    def _update_starters(self, old_name: str, new_name: str) -> None:
        """Update the starters in the cache.

        Args:
            old_name: The old player name
            new_name: The new player name
        """
        starters_cache = CACHE_MANAGER.get_starters_cache()

        starters_cache = recursive_replace(starters_cache, old_name, new_name)

    def _update_transaction_ids(self, old_name: str, new_name: str) -> None:
        """Update the transaction IDs in the cache.

        Args:
            old_name: The old player name
            new_name: The new player name
        """
        transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

        transaction_ids_cache = recursive_replace(
            transaction_ids_cache, old_name, new_name
        )

    def _update_valid_options(self, old_name: str, new_name: str) -> None:
        """Update the valid options in the cache.

        Args:
            old_name: The old player name
            new_name: The new player name
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        valid_options_cache = recursive_replace(
            valid_options_cache, old_name, new_name
        )

    def _update_players(self, old_name: str, new_name: str) -> None:
        """Update the players in the cache.

        Args:
            old_name: The old player name
            new_name: The new player name
        """
        players_cache = CACHE_MANAGER.get_players_cache()

        players_cache = recursive_replace(players_cache, old_name, new_name)

    def _update_image_urls(self, player_id: str) -> None:
        """Update the image URLs in the cache.

        Args:
            player_id: The player ID
        """
        image_urls_cache = CACHE_MANAGER.get_image_urls_cache()

        old_full = self.old_ids[player_id]["full_name"]
        new_full = self.new_ids[player_id]["full_name"]

        new_first = self.new_ids[player_id]["first_name"]
        new_last = self.new_ids[player_id]["last_name"]

        if player_id in image_urls_cache:
            image_urls_cache[player_id]["name"] = new_full
            image_urls_cache[player_id]["first_name"] = new_first
            image_urls_cache[player_id]["last_name"] = new_last

        if old_full in image_urls_cache:
            image_url = image_urls_cache[old_full]["image_url"]

            del image_urls_cache[old_full]

            image_urls_cache[new_full] = {
                "image_url": image_url,
                "name": new_full,
                "first_name": new_first,
                "last_name": new_last,
            }
