"""Cache module."""

from patriot_center_backend.cache.cache_manager import (
    get_cache_manager,
)

CACHE_MANAGER = get_cache_manager()
__all__ = ['CACHE_MANAGER']
