"""This module provides utility functions for handling image URLs."""

import logging
from copy import deepcopy
from time import time
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.image_urls_updater import (
    update_image_urls_cache,
)
from patriot_center_backend.utils.item_type_detector import detect_item_type

logger = logging.getLogger(__name__)


def get_image_url(item: str, dictionary: bool = False) -> dict[str, str] | str:
    """Get image URL for item.

    If item is manager, check to see if manager image URL is already in cache
    if it is, and its less than one hour old, return it,
    otherwise fetch it

    Note: If dictionary is True, and item is manager, returns dictionary
    with just image URL and name

    Args:
        item: Item to get image URL for
        dictionary: If True, return dictionary with other values, otherwise
            return string

    Returns:
        Image URL for item
            or dictionary of image URL, name, first name, and last name
    """
    item_type = detect_item_type(item)

    if item_type == "unknown":
        logger.warning(f"Could not find image URL for item: {item}")
        return {} if dictionary else ""

    image_urls_cache = CACHE_MANAGER.get_image_urls_cache()

    item_entry = image_urls_cache.get(item, {})

    if not item_entry:
        item_entry = update_image_urls_cache(item)
        return deepcopy(item_entry) if dictionary else item_entry["image_url"]

    if item_type == "manager":
        return _handle_if_manager(item_entry, dictionary)

    return deepcopy(item_entry) if dictionary else item_entry["image_url"]


def _handle_if_manager(
    manager_entry: dict[str, Any], dictionary: bool
) -> dict[str, str] | str:
    """Get image URL for manager.

    Args:
        manager_entry: Manager entry
        dictionary: If True, return dictionary with other values, otherwise
            return string

    Returns:
        Image URL for manager
            or dictionary of image URL and name
    """
    if float(manager_entry.get("timestamp", 0.0)) + 3600.0 < time():
        update_return = update_image_urls_cache(manager_entry["name"])
        manager_entry = deepcopy(update_return)

        if "timestamp" in manager_entry:
            manager_entry.pop("timestamp")

    return manager_entry if dictionary else manager_entry["image_url"]
