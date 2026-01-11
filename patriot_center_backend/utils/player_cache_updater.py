
from copy import deepcopy

from patriot_center_backend.cache import CACHE_MANAGER


def update_players_cache(item: list|str) -> None:
    """
    Update players cache with player metadata from matchup data or individual player ID.

    Adds player metadata including full name, position, team, and URL slug.
    Supports two input modes:
    - List: Process all players from matchup data
    - String: Process a single player ID

    Args:
        item: Either list of matchup data or single player_id string

    Returns:
        None (modifies players_cache in-place)

    Raises:
        ValueError: If item is None or empty, or if wrong type provided
    """
    if not item:
        raise ValueError("Item to update players cache cannot be None or empty.")
    
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    players_cache = CACHE_MANAGER.get_players_cache()

    # Handle single player ID
    if isinstance(item, str):
        player_name = player_ids_cache.get(item, {}).get("full_name", "")

        if player_name == '':
            print(f"WARNING: player_id {item} not found in player_ids")
            return

        if player_name not in players_cache:
            player_meta = player_ids_cache.get(item, {})

            # Create URL-encoded slug for player name (for API/URL usage)
            slug = player_meta.get("full_name", "").lower()
            slug = slug.replace(" ", "%20")
            slug = slug.replace("'", "%27")
            
            players_cache[player_meta["full_name"]] = {
                "full_name": player_meta.get("full_name", ""),
                "first_name": player_meta.get("first_name", ""),
                "last_name": player_meta.get("last_name", ""),
                "position": player_meta.get("position", ""),
                "team": player_meta.get("team", ""),
                "slug": slug,
                "player_id": item
            }
            
        return

    # Handle list of matchup data
    elif isinstance(item, list):
        for matchup in item:
            for player_id in matchup['players']:
                player_meta = player_ids_cache.get(player_id, {})

                player_meta = deepcopy(player_meta)
                player_meta["player_id"] = player_id

                if player_meta.get("full_name") not in players_cache:

                    # Create URL-encoded slug for player name
                    slug = player_meta.get("full_name", "").lower()
                    slug = slug.replace(" ", "%20")
                    slug = slug.replace("'", "%27")
                    
                    players_cache[player_meta["full_name"]] = {
                        "full_name": player_meta.get("full_name", ""),
                        "first_name": player_meta.get("first_name", ""),
                        "last_name": player_meta.get("last_name", ""),
                        "position": player_meta.get("position", ""),
                        "team": player_meta.get("team", ""),
                        "slug": slug,
                        "player_id": player_id
                    }
        
        return
    
    raise ValueError("Either matchups or player_id must be provided to update players cache.")