"""Detects the type of item based on its name."""

from typing import Literal

from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME


def detect_item_type(
    item: str
) -> Literal["manager", "unknown"]:
    """Detects the type of item based on its name.

    Args:
        item: Item to detect type for

    Returns:
        Type of item
    """
    # Manager: identified by presence in manager username mapping
    if item in NAME_TO_MANAGER_USERNAME:
        return "manager"

    return "unknown"
