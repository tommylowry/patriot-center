
from copy import deepcopy
from typing import List

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.transaction_processing.faab_processor import (
    add_faab_details_to_cache,
)
from patriot_center_backend.managers.transaction_processing.transaction_id_processor import (
    add_to_transaction_ids,
)
from patriot_center_backend.managers.utilities import update_players_cache


def process_add_or_drop_transaction(year: str, week: str, transaction: dict,
                                    roster_ids: dict, weekly_transaction_ids: List[str],
                                    commish_action: bool, use_faab: bool) -> None:
    """
    Process add/drop transactions (waivers, free agents, commissioner actions).

    Handles:
    - Waiver claims (with FAAB bidding)
    - Free agent pickups
    - Player drops
    - Commissioner manual adds/drops

    For each add, tracks player and FAAB spent (if applicable).
    For each drop, tracks player only.

    Args:
        year: year of the transaction
        week: week of the transaction
        transaction: Raw add/drop transaction from Sleeper API
        roster_ids: Mapping of roster IDs to manager names
        commish_action: Whether this is a commissioner action
        use_faab: if faab was used at the time of this transaction
    """
    adds  = transaction.get("adds", {})
    drops = transaction.get("drops", {})

    if not adds and not drops:
        print("Waiver transaction with no adds or drops:", transaction)
        return
    
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    
    if adds:
        for player_id in adds:
            roster_id = adds[player_id]
            
            manager = roster_ids.get(roster_id, None)
            player_name = player_ids_cache.get(player_id, {}).get("full_name", "unknown_player")
            
            transaction_id = transaction.get("transaction_id", "")

            # add add details to the cache
            waiver_bid = None
            if use_faab and transaction.get("settings", None) != None:
                waiver_bid = transaction.get("settings", {}).get("waiver_bid", None)
            add_add_or_drop_details_to_cache(year, week, weekly_transaction_ids, "add",
                                             manager, player_name, transaction_id,
                                             commish_action, use_faab, waiver_bid)
            update_players_cache(player_id)
            
            # add FAAB details to the cache
            if use_faab and transaction.get("settings", None) != None:
                faab_amount = transaction.get("settings", {}).get("waiver_bid", 0)
                transaction_type = transaction.get("type", "")
                add_faab_details_to_cache(year, week, transaction_type, manager,
                                          player_name, faab_amount, transaction_id)
    
    if drops:
        for player_id in drops:
            roster_id = drops[player_id]
            
            manager = roster_ids.get(roster_id, None)
            player_name = player_ids_cache.get(player_id, {}).get("full_name", "unknown_player")
            
            transaction_id = transaction.get("transaction_id", "")

            # add drop details to the cache
            add_add_or_drop_details_to_cache(year, week, weekly_transaction_ids, "drop",
                                             manager, player_name, transaction_id,
                                             commish_action, use_faab)
            update_players_cache(player_id)

def add_add_or_drop_details_to_cache(year: str, week: str, weekly_transaction_ids: List[str],
                                     free_agent_type: str, manager: str, player_name: str,
                                     transaction_id: str, commish_action: bool, use_faab: bool,
                                     waiver_bid: int|None = None) -> None:
    """
    Update cache with add or drop details at all aggregation levels.

    Updates cache at 3 levels (weekly, yearly, all-time) with:
    - Total add/drop count
    - Player-specific counts

    Args:
        year: Year of this transaction
        week: Week of this transaction
        weekly_transaction_ids: List of transaction ids for the week
        free_agent_type: Either "add" or "drop"
        manager: Manager name
        player_name: Full player name
        transaction_id: Unique transaction ID
        commish_action: Whether this is a commissioner action
        use_faab: Whether faab was used that season
        waiver_bid: FAAB amount bid (for adds only)
    """
    if free_agent_type not in ["add", "drop"]:
        return
    
    manager_cache = CACHE_MANAGER.get_manager_cache()

    if transaction_id in manager_cache[manager]["years"][year]["weeks"][week]["transactions"][f"{free_agent_type}s"]["transaction_ids"]:
        # Add already processed for this week
        return
    
    transaction_info = {
        "type": "add_or_drop",
        "free_agent_type": free_agent_type,
        "manager": manager,
        "player_name": player_name,
        "transaction_id": transaction_id,
        "waiver_bid": waiver_bid
    }
    add_to_transaction_ids(year, week, transaction_info, weekly_transaction_ids, commish_action, use_faab)
    
    top_level_summary = manager_cache[manager]["summary"]["transactions"][f"{free_agent_type}s"]
    yearly_summary    = manager_cache[manager]["years"][year]["summary"]["transactions"][f"{free_agent_type}s"]
    weekly_summary    = manager_cache[manager]["years"][year]["weeks"][week]["transactions"][f"{free_agent_type}s"]
    summaries = [top_level_summary, yearly_summary, weekly_summary]
    
    # Add add details in all summaries
    for summary in summaries:
        if player_name not in summary["players"]:
            summary["players"][player_name] = 0
        summary["players"][player_name] += 1
        summary["total"] += 1
    
    # Finally, add transaction ID to weekly summary to avoid double counting
    weekly_summary["transaction_ids"].append(transaction_id)

def revert_add_drop_transaction(transaction_id: str, transaction_type: str,
                                weekly_transaction_ids: List[str]) -> bool:
    """
    Revert a specific add or drop from a transaction (used for commissioner reversals).

    Decrements counts in cache at all levels and removes from transaction lists.
    Handles FAAB spent if applicable. Returns whether transaction was fully removed.

    Args:
        transaction_id: Transaction ID to revert
        transaction_type: Either "add" or "drop" to specify which portion to revert

    Returns:
        True if transaction was completely removed from cache, False otherwise

    Raises:
        Exception: If transaction involves multiple managers (unexpected)
    """
    if transaction_type != "add" and transaction_type != "drop":
        print(f"Cannot revert type {transaction_type} in _revert_add_or_drop_transaction for transaction_id {transaction_id}")
        return
    
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()
    manager_cache         = CACHE_MANAGER.get_manager_cache()

    transaction = deepcopy(transaction_ids_cache[transaction_id])

    year    = transaction['year']
    week    = transaction['week']
    manager = transaction['managers_involved'][0]
    player  = transaction[transaction_type]

    if len(transaction['managers_involved']) > 1:
        raise Exception(f"Weird {transaction_type} with multiple managers")
    
    places_to_change = []
    places_to_change.append(manager_cache[manager]['summary']['transactions'][f"{transaction_type}s"])
    places_to_change.append(manager_cache[manager]['years'][year]['summary']['transactions'][f"{transaction_type}s"])
    places_to_change.append(manager_cache[manager]['years'][year]['weeks'][week]['transactions'][f"{transaction_type}s"])

    for d in places_to_change:

        # remove the add/drop transaction from the cache
        d['total'] -= 1
        d['players'][player] -=1

        if d['players'][player] == 0:
            del d['players'][player]

    # If this transaction had faab spent and the transaction to remove is add, remove the transaction id from the faab spent portion.
    if "faab_spent" in transaction and transaction_type == "add":
        if transaction_id in manager_cache[manager]['years'][year]['weeks'][week]['transactions']['faab']['transaction_ids']:
            manager_cache[manager]['years'][year]['weeks'][week]['transactions']['faab']['transaction_ids'].remove(transaction_id)
        
        places_to_change = []
        places_to_change.append(manager_cache[manager]['summary']['transactions']["faab"])
        places_to_change.append(manager_cache[manager]['years'][year]['summary']['transactions']["faab"])
        places_to_change.append(manager_cache[manager]['years'][year]['weeks'][week]['transactions']["faab"])

        for d in places_to_change:
                
            d['players'][player]['num_bids_won'] -= 1
            if d['players'][player]['num_bids_won'] == 0:
                del d['players'][player]
    

    # remove the transaction_type portion of this transaction and keep it intact incase there was a the other type involved
    del transaction_ids_cache[transaction_id][transaction_type]
    transaction_ids_cache[transaction_id]['types'].remove(transaction_type)
    transaction_ids_cache[transaction_id]['players_involved'].remove(player)

    # this was the only data in the transaction so it can be fully removed
    if len(transaction_ids_cache[transaction_id]['types']) == 0:
        del transaction_ids_cache[transaction_id]
        if transaction_id in weekly_transaction_ids:
            weekly_transaction_ids.remove(transaction_id)
        return True # return True if transaction_id was deleted
    
    return False # return False if theres still more information