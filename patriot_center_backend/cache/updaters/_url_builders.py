"""This module provides utility functions for building URLs."""

import logging
from time import time

from patriot_center_backend.utils.sleeper_helpers import fetch_user_metadata

logger = logging.getLogger(__name__)


def build_manager_url(manager_name: str) -> dict[str, str]:
    """Builds a URL for a manager.

    Args:
        manager_name: The name of the manager.

    Returns:
        A dictionary containing the name, image URL, and timestamp.
    """
    user_metadata = fetch_user_metadata(manager_name, bypass_cache=True)

    avatar = user_metadata.get("avatar")
    if not avatar:
        logger.warning(
            f"Manager {manager_name} does not have an avatar in sleeper data."
        )
        return {}

    url = f"https://sleepercdn.com/avatars/{avatar}"

    output = {
        "name": manager_name,
        "image_url": url,
        "timestamp": time(),
    }

    return output


def build_url(item: str, item_type: str) -> dict[str, str]:
    """Builds a URL based on the item type.

    Args:
        item: The item for which to build the URL.
        item_type: The type of the item.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    url_builders = {
        "manager": build_manager_url,
    }

    return url_builders[item_type](item)
