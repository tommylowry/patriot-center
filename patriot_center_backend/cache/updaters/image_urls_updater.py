"""This module provides utility functions for updating the image URLs cache."""

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._url_builders import build_url
from patriot_center_backend.utils.item_type_detector import detect_item_type


def update_image_urls_cache(item: str,) -> dict[str, str]:
    """Update the image URLs cache.

    Args:
        item: The item for which to update the image URLs cache.

    Returns:
        The updated image URLs cache.
    """
    item_type = detect_item_type(item)
    url_dict = build_url(item, item_type)

    image_urls_cache = CACHE_MANAGER.get_image_urls_cache()
    image_urls_cache[item] = url_dict

    if item_type == "manager":
        CACHE_MANAGER.save_image_urls_cache()

    return url_dict
