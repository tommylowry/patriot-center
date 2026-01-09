from copy import deepcopy
from typing import Dict, List

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.transaction_processing.faab_processor import (
    add_faab_details_to_cache,
)
from patriot_center_backend.managers.transaction_processing.transaction_id_processor import (
    add_to_transaction_ids,
)
from patriot_center_backend.managers.utilities import draft_pick_decipher, update_players_cache


def process_trade_transaction(year: str, week: str, transaction: dict,
                              roster_ids: Dict[int, str], weekly_transaction_ids: List[str],
                              commish_action: bool, use_faab: bool) -> None:
    """
    Process a trade transaction involving multiple managers, players, picks, and FAAB.

    Handles:
    - Multi-party trades (2+ managers)
    - Player swaps
    - Draft pick exchanges
    - FAAB trading between managers
    - Commissioner forced trades

    For each manager involved, determines what they acquired vs sent,
    then updates cache and adds to transaction IDs cache.

    Args:
        year: Year of the transaction
        week: Week of the transaction
        transaction: Raw trade transaction from Sleeper API
        roster_ids: Mapping of roster IDs to manager names
        commish_action: Whether this is a commissioner-forced trade
        use_faab: Whether FAAB is used
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    for roster_id in transaction.get("roster_ids", []):
        manager = roster_ids.get(roster_id, None)

        trade_partners = transaction.get("roster_ids", []).copy()
        trade_partners.remove(roster_id)
        for i in range(len(trade_partners)):
            trade_partners[i] = roster_ids.get(trade_partners[i], "unknown_manager")

        
        # Players/Draft Picks Acquired and Sent
        acquired = {}
        if "adds" in transaction and transaction["adds"] != None:
            for player_id in transaction.get("adds", {}):
                if transaction["adds"][player_id] == roster_id:
                    player_name = player_ids_cache.get(player_id, {}).get("full_name", "unknown_player")
                    acquired[player_name] = roster_ids.get(transaction["drops"][player_id], "unknown_manager")
                    update_players_cache(player_id)
        

        sent = {}
        if "drops" in transaction and transaction["drops"] != None:
            for player_id in transaction.get("drops", {}):
                if transaction["drops"][player_id] == roster_id:
                    player_name = player_ids_cache.get(player_id, {}).get("full_name", "unknown_player")
                    sent[player_name] = roster_ids.get(transaction["adds"][player_id], "unknown_manager")
                    update_players_cache(player_id)
        

        if "draft_picks" in transaction and transaction["draft_picks"] != None:
            for draft_pick in transaction.get("draft_picks", []):
                
                # Acquired draft pick
                if draft_pick.get("owner_id", None) == roster_id:
                    draft_pick_name = draft_pick_decipher(draft_pick, roster_ids)
                    acquired[draft_pick_name] = roster_ids.get(draft_pick.get("previous_owner_id", "unknown_manager"), "unknown_manager")
                
                # Sent draft pick
                if draft_pick.get("previous_owner_id", None) == roster_id:
                    draft_pick_name = draft_pick_decipher(draft_pick, roster_ids)
                    sent[draft_pick_name] = roster_ids.get(draft_pick.get("owner_id", "unknown_manager"), "unknown_manager")

        transaction_id = transaction.get("transaction_id", "")

        # get faab traded information
        if use_faab and len(transaction.get("waiver_budget", [])) != 0:
            for faab_details in transaction["waiver_budget"]:
                faab_receiver = roster_ids[faab_details["receiver"]]
                faab_sender   = roster_ids[faab_details["sender"]]
                faab_amount   = faab_details["amount"]

                faab_string = f"${faab_amount} FAAB"
                
                # same faab amount traded in this trade with another party
                if faab_string in sent or faab_string in acquired:
                    print(f"WARNING: {faab_string} already in internal storage for the following trade: {transaction}")
                
                if faab_sender == manager:
                    sent[faab_string] = faab_receiver
                elif faab_receiver == manager:
                    acquired[faab_string] = faab_sender
        
        # add trade details to the cache
        add_trade_details_to_cache(year, week, manager, trade_partners, acquired,
                                   sent, weekly_transaction_ids, transaction_id,
                                   commish_action)
    

    # Faab Trading
    if use_faab and transaction.get("waiver_budget", []) != []:
        for faab_transaction in transaction.get("waiver_budget", []):
            
            faab_amount = faab_transaction.get("amount", 0)
            sender = roster_ids.get(faab_transaction.get("sender", ""), None)
            receiver = roster_ids.get(faab_transaction.get("receiver", ""), None)
            transaction_id = transaction.get("transaction_id", "")

            # add faab trade details to the cache
            add_faab_details_to_cache(year, week, "trade", sender, "FAAB", -faab_amount,
                                      transaction_id, trade_partner=receiver)
            add_faab_details_to_cache(year, week, "trade", receiver, "FAAB", faab_amount,
                                      transaction_id, trade_partner=sender)

def add_trade_details_to_cache(year: str, week: str, manager: str,
                               trade_partners: list, acquired: dict,
                               sent: dict, weekly_transaction_ids: List[str],
                               transaction_id: str, commish_action: bool,
                               use_faab: bool) -> None:
    """
    Update cache with trade details at all aggregation levels.

    Updates cache at 3 levels (weekly, yearly, all-time) with:
    - Total trade count
    - Trade partner counts
    - Players acquired/sent (with partner tracking)

    Args:
        year: year of the trade
        week: week of the trade
        manager: Manager name
        trade_partners: List of other managers involved in trade
        acquired: Dict of {player/asset: previous_owner} acquired by manager
        sent: Dict of {player/asset: new_owner} sent by manager
        transaction_id: Unique transaction ID
        commish_action: Whether this is a commissioner-forced trade
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    player_initial_dict = {
        "total": 0,
        "trade_partners": {
            # "trade_partner": num_times_acquired_from
        }
    }

    if transaction_id in manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["trades"]["transaction_ids"]:
        # Trade already processed for this week
        return
    
    transaction_info = {
        "type": "trade",
        "manager": manager,
        "trade_partners": trade_partners,
        "acquired": acquired,
        "sent": sent,
        "transaction_id": transaction_id
    }
    add_to_transaction_ids(year, week, transaction_info, weekly_transaction_ids, commish_action, use_faab)
    
    top_level_summary = manager_cache[manager]["summary"]["transactions"]["trades"]
    yearly_summary    = manager_cache[manager]["years"][year]["summary"]["transactions"]["trades"]
    weekly_summary    = manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["trades"]
    summaries = [top_level_summary, yearly_summary, weekly_summary]
    
    # Add trade details in all summaries
    for summary in summaries:

        # Process total trades
        if trade_partners:
            summary["total"] += 1
        
        # Process trade partners
        for trade_partner in trade_partners:
            if trade_partner not in summary["trade_partners"]:
                summary["trade_partners"][trade_partner] = 0
            summary["trade_partners"][trade_partner] += 1


        # Process players acquired
        acquired_summary = summary["trade_players_acquired"]
        for player in acquired:
            if player not in acquired_summary:
                acquired_summary[player] = deepcopy(player_initial_dict)
            if acquired[player] not in acquired_summary[player]["trade_partners"]:
                acquired_summary[player]["trade_partners"][acquired[player]] = 0
            acquired_summary[player]["trade_partners"][acquired[player]] += 1
            acquired_summary[player]["total"] += 1


        # Process players sent
        sent_summary = summary["trade_players_sent"]
        for player in sent:
            if player not in sent_summary:
                sent_summary[player] = deepcopy(player_initial_dict)
            if sent[player] not in sent_summary[player]["trade_partners"]:
                sent_summary[player]["trade_partners"][sent[player]] = 0
            sent_summary[player]["trade_partners"][sent[player]] += 1
            sent_summary[player]["total"] += 1

    # Finally, add transaction ID to weekly summary to avoid double counting
    weekly_summary["transaction_ids"].append(transaction_id)

def revert_trade_transaction(transaction_id1: str, transaction_id2: str,
                             weekly_transaction_ids: List[str]) -> None:
    """
    Revert two trade transactions that cancel each other out.

    Removes both transactions from cache at all levels (weekly, yearly, all-time)
    and removes from transaction ID list. Used for joke trades or accidental trades.

    Args:
        transaction_id1: First transaction ID to revert
        transaction_id2: Second transaction ID to revert
        weekly_transaction_ids: A list of weekly transaction IDs for the current week.
                                This list is updated to remove the reverted transaction IDs.
    """
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()
    manager_cache         = CACHE_MANAGER.get_manager_cache()

    transaction = deepcopy(transaction_ids_cache[transaction_id1])
    
    year = transaction['year']
    week = transaction['week']

    for manager in transaction['managers_involved']:
        
        overall_trades = manager_cache[manager]['summary']['transactions']
        yearly_trades  = manager_cache[manager]['years'][year]['summary']['transactions']
        weekly_trades  = manager_cache[manager]['years'][year]['weeks'][week]['transactions']

        if transaction_id1 in weekly_trades['trades']['transaction_ids']:
            weekly_trades['trades']['transaction_ids'].remove(transaction_id1)
        if transaction_id2 in weekly_trades['trades']['transaction_ids']:
            weekly_trades['trades']['transaction_ids'].remove(transaction_id2)
        if "faab" in weekly_trades and "transaction_ids" in weekly_trades['faab'] and transaction_id1 in weekly_trades['faab']['transaction_ids']:
            weekly_trades['faab']['transaction_ids'].remove(transaction_id1)
        if "faab" in weekly_trades and "transaction_ids" in weekly_trades['faab'] and transaction_id2 in weekly_trades['faab']['transaction_ids']:
            weekly_trades['faab']['transaction_ids'].remove(transaction_id2)

        for d in [overall_trades, yearly_trades, weekly_trades]:

            # if there were 2 trades made, these 2 were the 2, so it should now be empty
            d['trades']['total'] -= 2
            if d['trades']['total'] == 0:
                d['trades']['trade_partners']         = {}
                d['trades']['trade_players_acquired'] = {}
                d['trades']['trade_players_sent']     = {}
                d['trades']['transaction_ids']        = []
                continue

            # first remove all other managers as ones this manager has traded with
            other_managers = deepcopy(transaction['managers_involved'])
            other_managers.remove(manager)
            for other_manager in other_managers:
                
                d['trades']['trade_partners'][other_manager] -= 2
                if d['trades']['trade_partners'][other_manager] == 0:
                    del d['trades']['trade_partners'][other_manager]
            
            for player in list(transaction['trade_details'].keys()):
                
                # If manager wasn't involved, skip
                if manager != transaction['trade_details'][player].get('new_manager', '') and manager != transaction['trade_details'][player].get('old_manager', ''):
                    continue
                
                # Remove from acquired
                d['trades']['trade_players_acquired'][player]['total'] -= 1
                if d['trades']['trade_players_acquired'][player]['total'] == 0:
                    del d['trades']['trade_players_acquired'][player]
                
                else:
                    trade_partner = transaction['trade_details'][player].get('new_manager', '')
                    if trade_partner == manager:
                        trade_partner = transaction['trade_details'][player].get('old_manager', '')
                    
                    d['trades']['trade_players_acquired'][player]['trade_partners'][trade_partner] -= 1
                    if d['trades']['trade_players_acquired'][player]['trade_partners'][trade_partner] == 0:
                        del d['trades']['trade_players_acquired'][player]['trade_partners'][trade_partner]

                # Remove from sent
                d['trades']['trade_players_sent'][player]['total'] -= 1
                if d['trades']['trade_players_sent'][player]['total'] == 0:
                    del d['trades']['trade_players_sent'][player]
                
                else:
                    trade_partner = transaction['trade_details'][player].get('new_manager', '')
                    if trade_partner == manager:
                        trade_partner = transaction['trade_details'][player].get('old_manager', '')
                    
                    d['trades']['trade_players_sent'][player]['trade_partners'][trade_partner] -= 1
                    if d['trades']['trade_players_sent'][player]['trade_partners'][trade_partner] == 0:
                        del d['trades']['trade_players_sent'][player]['trade_partners'][trade_partner]

                
                # faab is here, the logic is to turn it into an int, so player = "$1 FAAB" -> faab = 1
                if "FAAB" in player:
                    
                    faab = player.split(" ")[0]
                    faab = faab.replace("$", "")
                    faab = int(faab)    
                    d['faab']['traded_away']['total'] -= faab
                    d['faab']['acquired_from']['total'] -= faab

                    trade_partner = transaction['trade_details'][player].get('new_manager', '')
                    if trade_partner == manager:
                        trade_partner = transaction['trade_details'][player].get('old_manager', '')

                    d['faab']['traded_away']['trade_partners'][trade_partner] -= faab
                    if d['faab']['traded_away']['trade_partners'][trade_partner] == 0:
                        del d['faab']['traded_away']['trade_partners'][trade_partner]
                    
                    d['faab']['acquired_from']['trade_partners'][trade_partner] -= faab
                    if d['faab']['acquired_from']['trade_partners'][trade_partner] == 0:
                        del d['faab']['acquired_from']['trade_partners'][trade_partner]
    
    del transaction_ids_cache[transaction_id1]
    del transaction_ids_cache[transaction_id2]
    if transaction_id1 in weekly_transaction_ids:
        weekly_transaction_ids.remove(transaction_id1)
    if transaction_id2 in weekly_transaction_ids:
        weekly_transaction_ids.remove(transaction_id2)