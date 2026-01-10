"""
Cache management package.
Centralized cache operations for all cache files.
"""
from patriot_center_backend.cache.cache_manager import CacheManager, get_cache_manager

CACHE_MANAGER = get_cache_manager()
__all__ = ['CacheManager', 'get_cache_manager', 'CACHE_MANAGER']