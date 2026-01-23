"""Central cache management for Patriot Center backend.

This is the ONLY place where cache operations should be coordinated.
All other code should use CacheManager methods.

Single Responsibility: Orchestrate sub-processors and manage persistence
"""

from patriot_center_backend.cache.cache_manager import (
    CacheManager,
    get_cache_manager,
)

CACHE_MANAGER = get_cache_manager()
__all__ = ['CACHE_MANAGER', 'CacheManager']
