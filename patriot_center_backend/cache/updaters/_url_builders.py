
import logging
from time import time

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.helpers import get_player_id, get_player_name
from patriot_center_backend.utils.sleeper_helpers import fetch_user_metadata

logger = logging.getLogger(__name__)


def build_manager_url(manager_name: str) -> dict[str, str]:
    user_metadata = fetch_user_metadata(manager_name)

    avatar = user_metadata.get("avatar")
    if not avatar:
        logger.warning(
            f"Manager {manager_name} does not have an avatar in sleeper data."
        )
        return {}

    url = f"https://sleepercdn.com/avatars/{avatar}"

    output = {
        "name": manager_name,
        "image_url": url,
        "timestamp": time(),
    }

    return output

def build_draft_pick_url(draft_pick_name: str) -> dict[str, str]:
    abridged_name = draft_pick_name.replace(" Draft Pick", "")
    abridged_name = abridged_name.replace("Round ", "R")

    first_name = abridged_name.split(" ")[0]
    last_name = abridged_name.replace(f"{first_name} ", "")

    output = {
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
            "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
        ),
        "name": draft_pick_name,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output

def build_faab_url(item: str) -> dict[str, str]:
    first_name = item.split(" ")[0]
    last_name = item.split(" ")[1]

    output = {
        "image_url": (
            "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
        ),
        "name": item,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output

def build_player_id_url(player_id: str) -> dict[str, str]:
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    if player_id.isnumeric():
        url = f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
    else:
        url = (
            f"https://sleepercdn.com/images/"
            f"team_logos/nfl/{player_id.lower()}.png"
        )


    full_name = get_player_name(player_id)
    if not full_name:
        logger.warning(
            f"Player {player_id} does not have a full name in player_ids_cache."
        )
        return {}

    first_name = player_ids_cache.get(player_id, {}).get("first_name", "")
    last_name = player_ids_cache.get(player_id, {}).get("last_name", "")

    output = {
        "name": full_name,
        "image_url": url,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output


def build_player_url(player_name: str) -> dict[str, str]:

    player_id = get_player_id(player_name)
    if not player_id:
        logger.warning(
            f"Player {player_name} does not have "
            f"a player_id in player_ids_cache."
        )
        return {}

    return build_player_id_url(player_id)


def build_url(item: str, type: str) -> dict[str, str]:
    url_builders = {
        "manager": build_manager_url,
        "draft_pick": build_draft_pick_url,
        "faab": build_faab_url,
        "player_id": build_player_id_url,
        "player": build_player_url,
    }

    return url_builders[type](item)
