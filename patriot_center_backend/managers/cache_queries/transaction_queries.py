"""
Cache query helpers for reading transaction related manager metadata.

All functions are read-only and query the manager cache to extract
the transaction view of data.
"""
from copy import deepcopy
from typing import Dict, List

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.managers.formatters import get_trade_card
from patriot_center_backend.managers.utilities import extract_dict_data

CACHE_MANAGER = get_cache_manager()

MANAGER_CACHE         = CACHE_MANAGER.get_manager_cache()
TRANSACTION_IDS_CACHE = CACHE_MANAGER.get_transaction_ids_cache()


def get_transaction_details_from_cache(year: str, manager: str,
                                       image_urls: dict) -> Dict:
    """
    Get comprehensive transaction summary with formatted data and image URLs.

    Extracts and formats trades, adds, drops, and FAAB spending including:
    - Trade partners and most acquired/sent players
    - Top added/dropped players
    - FAAB spending and trading

    All player/manager names enriched with image URLs.

    Args:
        year: Season year (optional - defaults to all-time stats)
        manager: Manager name
        image_urls: Dict of image URLs
        player_ids: Player ID to metadata mapping

    Returns:
        Dictionary with trades, adds, drops, and faab summaries
    """
    transaction_summary = {
        "trades":      {},
        "adds":        {},
        "drops":       {},
        "faab":        {}
    }

    # Get all-time stats by default, or single season stats if year specified
    cached_transaction_data = deepcopy(MANAGER_CACHE[manager]["summary"]["transactions"])
    if year:
        cached_transaction_data = deepcopy(MANAGER_CACHE[manager]["years"][year]["summary"]["transactions"])

    # Flatten FAAB player data to just total spent (if FAAB exists)
    if 'faab' in cached_transaction_data:
        for player in cached_transaction_data['faab']['players']:
            cached_transaction_data['faab']['players'][player] = cached_transaction_data['faab']['players'][player]['total_faab_spent']
    
    trades = {
        "total":              cached_transaction_data["trades"]["total"],
        "top_trade_partners": extract_dict_data(deepcopy(cached_transaction_data["trades"]["trade_partners"]), image_urls)
    }

    # ---- Trades Summary ----
    
    # Most Aquired Players
    trade_players_acquired = cached_transaction_data["trades"]["trade_players_acquired"]
    most_acquired_players = extract_dict_data(deepcopy(trade_players_acquired), image_urls)
    for player in most_acquired_players:
        player_details = deepcopy(trade_players_acquired[player["name"]])
        player["from"] = extract_dict_data(deepcopy(player_details.get("trade_partners", {})), image_urls, cutoff=0)
    trades["most_acquired_players"] = most_acquired_players

    # Most Sent Players
    trade_players_sent = cached_transaction_data["trades"]["trade_players_sent"]
    most_sent_players = extract_dict_data(deepcopy(trade_players_sent), image_urls)
    for player in most_sent_players:
        player_details = deepcopy(trade_players_sent.get(player["name"], {}))
        player["to"] = extract_dict_data(player_details.get("trade_partners", {}), image_urls, cutoff=0)
    trades["most_sent_players"] = most_sent_players

    transaction_summary["trades"] = trades


    # ---- Adds Summary ----
    adds = {
        "total":             cached_transaction_data["adds"]["total"],
        "top_players_added": extract_dict_data(deepcopy(cached_transaction_data["adds"]["players"]), image_urls)
    }
    transaction_summary["adds"] = adds
    

    # ---- Drops Summary ----
    drops = {
            "total":               cached_transaction_data["drops"]["total"],
            "top_players_dropped": extract_dict_data(deepcopy(cached_transaction_data["drops"]["players"]), image_urls)
    }
    transaction_summary["drops"] = drops


    # ---- FAAB Summary ----
    # Handle cases where FAAB doesn't exist (e.g., older years before FAAB was implemented)
    if "faab" in cached_transaction_data and cached_transaction_data["faab"]:
        faab = {
            "total_spent": abs(cached_transaction_data["faab"]["total_lost_or_gained"]),
            "biggest_acquisitions": extract_dict_data(deepcopy(cached_transaction_data["faab"]["players"]), image_urls, value_name="amount")
        }

        # FAAB Traded
        sent = cached_transaction_data["faab"]["traded_away"]["total"]
        received = cached_transaction_data["faab"]["acquired_from"]["total"]
        net = received - sent
        faab["faab_traded"] = {
            "sent":     sent,
            "received": received,
            "net":      net
        }
    else:
        # FAAB not available for this year/manager
        faab = {
            "total_spent": 0,
            "biggest_acquisitions": [],
            "faab_traded": {
                "sent": 0,
                "received": 0,
                "net": 0
            }
        }
    transaction_summary["faab"] = faab

    # Return final transaction summary
    return deepcopy(transaction_summary)

def get_trade_history_between_two_managers(manager1: str, manager2: str,
                                           image_urls: dict, year: str|None = None) -> List:
    """
    Get complete trade history between two managers.

    Finds all trades involving both managers and returns formatted trade cards.

    Args:
        manager1: First manager name
        manager2: Second manager name
        image_urls: Dict of image URLs
        year: Season year (optional - defaults to all-time)

    Returns:
        List of trade cards in reverse chronological order (newest first)
    """
    years = list(MANAGER_CACHE[manager1].get("years", {}).keys())
    if year:
        years = [year]
    
    # Gather all transaction IDs for manager_1
    transaction_ids = []
    for y in years:
        weeks = deepcopy(MANAGER_CACHE[manager1]["years"][y]["weeks"])
        for w in weeks:
            weekly_trade_transaction_ids = deepcopy(MANAGER_CACHE.get(manager1, {}).get("years", {}).get(y, {}).get("weeks", {}).get(w, {}).get("transactions", {}).get("trades", {}).get("transaction_ids", []))
            transaction_ids.extend(weekly_trade_transaction_ids)


    # Filter to only those involving both managers
    for tid in deepcopy(transaction_ids):
        if manager2 not in TRANSACTION_IDS_CACHE.get(tid, {}).get("managers_involved", []):
            transaction_ids.remove(tid)

    trades_between = []
    

    for t in transaction_ids:
        trades_between.append(get_trade_card(t, image_urls))
    
    trades_between.reverse()
    return trades_between