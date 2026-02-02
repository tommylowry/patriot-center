"""Award exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.award_queries import (
    get_manager_awards_from_cache,
    get_manager_score_awards_from_cache,
)
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_manager_awards(manager: str) -> dict[str, Any]:
    """Get awards and recognitions for a specific manager.

    Args:
        manager: Manager name

    Returns:
        dictionary with manager awards and recognitions
    """
    awards_data = {
        "manager": get_image_url(manager, dictionary=True),
        "image_url": get_image_url(manager),
        "awards": get_manager_awards_from_cache(manager),
    }
    score_awards = get_manager_score_awards_from_cache(manager)

    awards_data["awards"].update(deepcopy(score_awards))

    return deepcopy(awards_data)
