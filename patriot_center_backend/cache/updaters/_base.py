"""Base cache updater functions."""

import logging

logger = logging.getLogger(__name__)


def log_cache_update(year: int, week: int, cache_name: str) -> None:
    """Log cache update message.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-18).
        cache_name: The name of the cache being updated.
    """
    padding = " "
    if week >= 10:
        padding = ""
    logger.info(
        f"\tSeason {year}, Week {week}:{padding} {cache_name} Cache Updated."
    )
