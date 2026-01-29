"""Utilities to build and maintain the ffWAR cache for Patriot Center.

This module:
- Loads supporting caches at import time (replacement scores and starters).
- Determines the current fantasy season/week.
- Loads an ffWAR cache JSON file and incrementally updates it by year/week.
- Persists the updated cache back to disk.

Algorithm summary:
- For each unprocessed week, derive per-position player scores.
- Simulate hypothetical matchups replacing each player with a positional
    replacement average.
- ffWAR = (net simulated wins difference) / (total simulations), rounded to
    3 decimals.
"""

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.calculations.ffwar_calculator import FFWARCalculator


def update_player_data_cache(year: int, week: int) -> None:
    """Incrementally updates the ffWAR cache JSON file by year/week.

    - Dynamically determines the current season and week
    according to Sleeper API/util logic.
    - Processes all years configured for leagues;
    this drives which seasons we consider for updates.
    - Reads progress markers from the cache to
    support incremental updates and resumability.
    - Skips years that are already fully processed
    based on the last recorded season.
    - If the cache is already up-to-date for
    the current season and week, stops processing.
    - Determines the range of weeks to update.
    - Fetches and updates only the missing weeks for the year.
    - Saves the updated cache to the file.
    - Reloads to remove the metadata fields.

    Args:
        year: The current season
        week: The current week
    """
    player_data_cache = CACHE_MANAGER.get_player_data_cache()

    if str(year) not in player_data_cache:
        player_data_cache[str(year)] = {}

    # Fetch ffWAR for the week.
    calculator = FFWARCalculator(year, week)
    result = calculator.calculate_ffwar()

    player_data_cache[str(year)][str(week)] = result
