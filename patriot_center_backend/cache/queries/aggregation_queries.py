"""Cache query helpers for reading aggregated data."""

from functools import lru_cache

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.helpers import get_player_id


@lru_cache(maxsize=10000)
def get_ffwar_from_cache(
    player: str, season: str | None = None, week: str | None = None
) -> float:
    """Lookup ffWAR for a player at a specific season/week granularity.

    Returns zero if season/week not provided or absent from cache.

    Args:
        player: Player identifier.
        season: Season for lookup.
        week: Week for lookup.

    Returns:
        ffWAR value (0.0 if unavailable).
    """
    if season is None or week is None:
        return 0.0

    player_data_cache = CACHE_MANAGER.get_player_data_cache()

    if week in player_data_cache.get(season, {}):
        week_data = player_data_cache[season][week]
        player_id = get_player_id(player)

        if player_id in week_data:
            return week_data[player_id]["ffWAR"]

    return 0.0

def get_team(player: str) -> str | None:
    """Lookup team for a player.

    Args:
        player: Player identifier.

    Returns:
        Team name if found, otherwise None.
    """
    players_cache = CACHE_MANAGER.get_players_cache()

    return players_cache.get(player, {}).get("team")
