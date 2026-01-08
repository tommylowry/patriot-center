"""
Transaction processing for manager metadata.

Handles all transaction-related operations including:
- Trade processing and reversal
- Add/drop/waiver processing
- FAAB tracking
- Transaction validation and deduplication
"""
from copy import deepcopy
from typing import Any, Dict, List, Optional

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.utilities import draft_pick_decipher, update_players_cache
from patriot_center_backend.managers.validators import validate_transaction
from patriot_center_backend.utils.helpers import fetch_sleeper_data

CACHE_MANAGER = get_cache_manager()

MANAGER_CACHE         = CACHE_MANAGER.get_manager_cache()
PLAYER_IDS_CACHE      = CACHE_MANAGER.get_player_ids_cache()
TRANSACTION_IDS_CACHE = CACHE_MANAGER.get_transaction_ids_cache()


class TransactionProcessor:
    """
    Processes fantasy football transactions with reversal detection and FAAB tracking.

    Handles:
    - Trade processing (multi-party, draft picks, FAAB)
    - Add/drop/waiver processing
    - Transaction reversal detection (joke trades, accidental transactions)
    - FAAB spending and trading
    - Transaction deduplication
    - Cache updates at 3 levels (weekly, yearly, all-time)

    Key Features:
    - Detects and reverts reversed transactions (same managers, opposite players)
    - Tracks FAAB spent on waivers and traded between managers
    - Handles commissioner actions separately
    - Maintains global transaction ID cache for deduplication

    Uses session state pattern for thread safety during week processing.
    """

    def __init__(self, use_faab: bool) -> None:
        """
        Initialize transaction processor with cache references.

        Args:
            use_faab: Whether league uses FAAB (Free Agent Acquisition Budget)
        """
        self._use_faab = use_faab
        
        # Session state (set externally before processing)
        self._year: Optional[str] = None
        self._week: Optional[str] = None
        self._weekly_roster_ids: Dict[int, str] = {}
        self._weekly_transaction_ids: List[Dict[str, Any]] = []
    
    def set_session_state(self, year: str, week: str, weekly_roster_ids: Dict[int, str], use_faab: bool) -> None:
        """
        Set session state before processing transaction data.

        Must be called before scrub_transaction_data() to establish context.

        Args:
            year: Season year as string
            week: Week number as string
            weekly_roster_ids: Mapping of roster IDs to manager names for this week
            use_faab: Whether FAAB is used this season
        """
        self._year = year
        self._week = week
        self._weekly_roster_ids = weekly_roster_ids
        self._use_faab = use_faab
    
    def clear_session_state(self) -> None:
        """Clear session state after processing week."""
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}
        self._weekly_transaction_ids = []

    def scrub_transaction_data(self, year: str, week: str) -> None:
        """
        Fetch and process all transactions for a given week.

        Workflow:
        1. Fetch transactions from Sleeper API
        2. Reverse order (Sleeper returns newest first, we want oldest first)
        3. Process each transaction via _process_transaction
        4. Transactions are validated, categorized, and cached

        Args:
            year: Season year as string
            week: Week number as string

        Raises:
            ValueError: If no league ID found for the year
        """
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        transactions_list = fetch_sleeper_data(f"league/{league_id}/transactions/{week}")
        
        # transactions come from sleeper newest first, we want to put them in oldest first so that when they're shown they show up its oldest at the top for a week.
        transactions_list.reverse()
        
        for transaction in transactions_list:
           self._process_transaction(transaction)
    
    def check_for_reverse_transactions(self) -> None:
        """
        Detect and revert reversed transactions (joke trades or accidental transactions).

        Compares all weekly transactions to find pairs that undo each other:
        - Same managers involved
        - Same players involved
        - Opposite directions (player moved from A→B then B→A)

        Handles two cases:
        1. Commissioner add/drop reversals (accident correction)
        2. Trade reversals (joke trades or mistakes)

        Reverted transactions are removed from cache and transaction ID list.
        """
        while len(self._weekly_transaction_ids) > 1:
            weekly_transaction_ids = deepcopy(self._weekly_transaction_ids)
            
            transaction_id1 = weekly_transaction_ids.pop()
            transaction1    = TRANSACTION_IDS_CACHE[transaction_id1]

            for transaction_id2 in weekly_transaction_ids:
                transaction2 = TRANSACTION_IDS_CACHE[transaction_id2]

                # Skip if different managers involved
                if sorted(transaction1['managers_involved']) != sorted(transaction2['managers_involved']):
                    continue

                # Check for commissioner add/drop reversals
                # If commissioner adds/drops a player, then opposite action occurs,
                # this was likely an accident - revert both transactions
                if transaction1["commish_action"]:
                    if "add" in transaction1:
                        if transaction1["add"] == transaction2.get("drop", ""):
                            trans_1_removed = self._revert_add_drop_transaction(transaction_id1, "add")
                            trans_2_removed = self._revert_add_drop_transaction(transaction_id2, "drop")
                            
                            if trans_1_removed: # no more transaction 1, so move on to another transaction to evaluate
                                break
                            if trans_2_removed: # no more transaction 2, so move on to the next transaction for transaction 1 to evaluate
                                continue
                    
                    if "drop" in transaction1:
                        if transaction1["drop"] == transaction2.get("add", ""):
                            trans_1_removed = self._revert_add_drop_transaction(transaction_id1, "drop")
                            trans_2_removed = self._revert_add_drop_transaction(transaction_id2, "add")
                            
                            if trans_1_removed:
                                break
                            if trans_2_removed:
                                continue
                
                if transaction2["commish_action"]:
                    if "add" in transaction2:
                        if transaction2["add"] == transaction1.get("drop", ""):
                            trans_1_removed = self._revert_add_drop_transaction(transaction_id1, "drop")
                            trans_2_removed = self._revert_add_drop_transaction(transaction_id2, "add")
                            
                            if trans_1_removed:
                                break
                            if trans_2_removed:
                                continue
                    if "drop" in transaction2:
                        if transaction2["drop"] == transaction1.get("add", ""):
                            trans_1_removed = self._revert_add_drop_transaction(transaction_id1, "add")
                            trans_2_removed = self._revert_add_drop_transaction(transaction_id2, "drop")
                            
                            if trans_1_removed:
                                break
                            if trans_2_removed:
                                continue
                
                # Check for trade reversals (joke trades or immediate regret)
                # Both must be trades with same players, but opposite directions
                if "trade" not in transaction1["types"] or "trade" not in transaction2["types"]:
                    continue

                if sorted(transaction1['players_involved']) != sorted(transaction2['players_involved']):
                    continue

                # If same players and trade details match (opposite directions), it's a reversal
                if sorted(list(transaction1['trade_details'].keys())) == sorted(list(transaction2['trade_details'].keys())):
                    
                    invalid_transaction = True
                    for player in transaction1['trade_details']:
                        if transaction1["trade_details"][player]['old_manager'] != transaction2['trade_details'][player]['new_manager']:
                            invalid_transaction = False
                            break
                        if transaction1["trade_details"][player]['new_manager'] != transaction2['trade_details'][player]['old_manager']:
                            invalid_transaction = False
                            break
                    if not invalid_transaction:
                        continue
                
                # continue wasnt called so the trade is invalid, remove it
                self._revert_trade_transaction(transaction_id1, transaction_id2)
                break
            
            if transaction_id1 in self._weekly_transaction_ids:
                self._weekly_transaction_ids.remove(transaction_id1)

    def _process_transaction(self, transaction: dict) -> None:
        """
        Process a single transaction by categorizing and routing to appropriate handler.

        Workflow:
        1. Determine transaction type (trade, add_or_drop, waiver, commissioner)
        2. Normalize type (free_agent/waiver → add_or_drop)
        3. Detect commissioner actions
        4. Validate transaction
        5. Route to appropriate processor (_process_trade_transaction or _process_add_or_drop_transaction)

        Args:
            transaction: Raw transaction data from Sleeper API
        """
        transaction_type = transaction.get("type", "")
        commish_action = False

        if transaction_type in ["free_agent", "waiver"]:
            transaction_type = "add_or_drop"
        
        elif transaction_type == "commissioner":
            commish_action = True
            # No swap, so it must be add or drop
            if transaction.get("adds", None) is None:
                transaction_type = "add_or_drop"
            elif transaction.get("drops", None) is None:
                transaction_type = "add_or_drop"
            
            # if adds or drops is multiple players, its commish forced swap/trade
            elif len(transaction.get("adds", {})) >= 1 or len(transaction.get("drops", {})) >= 1:
                transaction_type = "trade"
            
            # only one add and only one drop, so add_or_drop
            else:
                transaction_type = "add_or_drop"
        

        # Dynamically collect the proper function to process this transaction type
        process_transaction_type = getattr(self, f"_process_{transaction_type}_transaction", None)

        if not validate_transaction(transaction, transaction_type, process_transaction_type, self._weekly_roster_ids):
            return

        # Run the transaction through the appropriate processor
        process_transaction_type(transaction, commish_action)

    def _revert_trade_transaction(self, transaction_id1: str, transaction_id2: str) -> None:
        """
        Revert two trade transactions that cancel each other out.

        Removes both transactions from cache at all levels (weekly, yearly, all-time)
        and removes from transaction ID list. Used for joke trades or accidental trades.

        Args:
            transaction_id1: First transaction ID to revert
            transaction_id2: Second transaction ID to revert
        """
        transaction = deepcopy(TRANSACTION_IDS_CACHE[transaction_id1])
        
        year = transaction['year']
        week = transaction['week']

        for manager in transaction['managers_involved']:
            
            overall_trades = MANAGER_CACHE[manager]['summary']['transactions']
            yearly_trades  = MANAGER_CACHE[manager]['years'][year]['summary']['transactions']
            weekly_trades  = MANAGER_CACHE[manager]['years'][year]['weeks'][week]['transactions']

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
            
        del TRANSACTION_IDS_CACHE[transaction_id1]
        del TRANSACTION_IDS_CACHE[transaction_id2]
        if transaction_id1 in self._weekly_transaction_ids:
            self._weekly_transaction_ids.remove(transaction_id1)
        if transaction_id2 in self._weekly_transaction_ids:
            self._weekly_transaction_ids.remove(transaction_id2)
    
    def _revert_add_drop_transaction(self, transaction_id: str, transaction_type: str) -> bool:
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

        transaction = deepcopy(TRANSACTION_IDS_CACHE[transaction_id])

        year    = transaction['year']
        week    = transaction['week']
        manager = transaction['managers_involved'][0]
        player  = transaction[transaction_type]

        if len(transaction['managers_involved']) > 1:
            raise Exception(f"Weird {transaction_type} with multiple managers")
        
        places_to_change = []
        places_to_change.append(MANAGER_CACHE[manager]['summary']['transactions'][f"{transaction_type}s"])
        places_to_change.append(MANAGER_CACHE[manager]['years'][year]['summary']['transactions'][f"{transaction_type}s"])
        places_to_change.append(MANAGER_CACHE[manager]['years'][year]['weeks'][week]['transactions'][f"{transaction_type}s"])

        for d in places_to_change:

            # remove the add/drop transaction from the cache
            d['total'] -= 1
            d['players'][player] -=1

            if d['players'][player] == 0:
                del d['players'][player]

        # If this transaction had faab spent and the transaction to remove is add, remove the transaction id from the faab spent portion.
        if "faab_spent" in transaction and transaction_type == "add":
            if transaction_id in MANAGER_CACHE[manager]['years'][year]['weeks'][week]['transactions']['faab']['transaction_ids']:
                MANAGER_CACHE[manager]['years'][year]['weeks'][week]['transactions']['faab']['transaction_ids'].remove(transaction_id)
            
            places_to_change = []
            places_to_change.append(MANAGER_CACHE[manager]['summary']['transactions']["faab"])
            places_to_change.append(MANAGER_CACHE[manager]['years'][year]['summary']['transactions']["faab"])
            places_to_change.append(MANAGER_CACHE[manager]['years'][year]['weeks'][week]['transactions']["faab"])

            for d in places_to_change:
                    
                d['players'][player]['num_bids_won'] -= 1
                if d['players'][player]['num_bids_won'] == 0:
                    del d['players'][player]
        

        # remove the transaction_type portion of this transaction and keep it intact incase there was a the other type involved
        del TRANSACTION_IDS_CACHE[transaction_id][transaction_type]
        TRANSACTION_IDS_CACHE[transaction_id]['types'].remove(transaction_type)
        TRANSACTION_IDS_CACHE[transaction_id]['players_involved'].remove(player)

        # this was the only data in the transaction so it can be fully removed
        if len(TRANSACTION_IDS_CACHE[transaction_id]['types']) == 0:
            del TRANSACTION_IDS_CACHE[transaction_id]
            if transaction_id in self._weekly_transaction_ids:
                self._weekly_transaction_ids.remove(transaction_id)
            return True # return True if transaction_id was deleted
        
        return False # return False if theres still more information

    def _process_trade_transaction(self, transaction: dict, commish_action: bool) -> None:
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
            transaction: Raw trade transaction from Sleeper API
            commish_action: Whether this is a commissioner-forced trade
        """
        for roster_id in transaction.get("roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_id, None)

            trade_partners = transaction.get("roster_ids", []).copy()
            trade_partners.remove(roster_id)
            for i in range(len(trade_partners)):
                trade_partners[i] = self._weekly_roster_ids.get(trade_partners[i], "unknown_manager")

            
            # Players/Draft Picks Acquired and Sent
            acquired = {}
            if "adds" in transaction and transaction["adds"] != None:
                for player_id in transaction.get("adds", {}):
                    if transaction["adds"][player_id] == roster_id:
                        player_name = PLAYER_IDS_CACHE.get(player_id, {}).get("full_name", "unknown_player")
                        acquired[player_name] = self._weekly_roster_ids.get(transaction["drops"][player_id], "unknown_manager")
                        update_players_cache(player_id)
            

            sent = {}
            if "drops" in transaction and transaction["drops"] != None:
                for player_id in transaction.get("drops", {}):
                    if transaction["drops"][player_id] == roster_id:
                        player_name = PLAYER_IDS_CACHE.get(player_id, {}).get("full_name", "unknown_player")
                        sent[player_name] = self._weekly_roster_ids.get(transaction["adds"][player_id], "unknown_manager")
                        update_players_cache(player_id)
            

            if "draft_picks" in transaction and transaction["draft_picks"] != None:
                for draft_pick in transaction.get("draft_picks", []):
                    
                    # Acquired draft pick
                    if draft_pick.get("owner_id", None) == roster_id:
                        draft_pick_name = draft_pick_decipher(draft_pick, self._weekly_roster_ids)
                        acquired[draft_pick_name] = self._weekly_roster_ids.get(draft_pick.get("previous_owner_id", "unknown_manager"), "unknown_manager")
                    
                    # Sent draft pick
                    if draft_pick.get("previous_owner_id", None) == roster_id:
                        draft_pick_name = draft_pick_decipher(draft_pick, self._weekly_roster_ids)
                        sent[draft_pick_name] = self._weekly_roster_ids.get(draft_pick.get("owner_id", "unknown_manager"), "unknown_manager")

            transaction_id = transaction.get("transaction_id", "")

            # get faab traded information
            if self._use_faab and len(transaction.get("waiver_budget", [])) != 0:
                for faab_details in transaction["waiver_budget"]:
                    faab_receiver = self._weekly_roster_ids[faab_details["receiver"]]
                    faab_sender   = self._weekly_roster_ids[faab_details["sender"]]
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
            self._add_trade_details_to_cache(manager, trade_partners, acquired, sent, transaction_id, commish_action)
        

        # Faab Trading
        if self._use_faab and transaction.get("waiver_budget", []) != []:
            for faab_transaction in transaction.get("waiver_budget", []):
                
                faab_amount = faab_transaction.get("amount", 0)
                sender = self._weekly_roster_ids.get(faab_transaction.get("sender", ""), None)
                receiver = self._weekly_roster_ids.get(faab_transaction.get("receiver", ""), None)
                transaction_id = transaction.get("transaction_id", "")

                # add faab trade details to the cache
                self._add_faab_details_to_cache("trade", sender, "FAAB", -faab_amount, transaction_id, trade_partner=receiver)
                self._add_faab_details_to_cache("trade", receiver, "FAAB", faab_amount, transaction_id, trade_partner=sender)
    
    def _add_trade_details_to_cache(self, manager: str, trade_partners: list,
                                    acquired: dict, sent: dict,
                                    transaction_id: str, commish_action: bool) -> None:
        """
        Update cache with trade details at all aggregation levels.

        Updates cache at 3 levels (weekly, yearly, all-time) with:
        - Total trade count
        - Trade partner counts
        - Players acquired/sent (with partner tracking)

        Args:
            manager: Manager name
            trade_partners: List of other managers involved in trade
            acquired: Dict of {player/asset: previous_owner} acquired by manager
            sent: Dict of {player/asset: new_owner} sent by manager
            transaction_id: Unique transaction ID
            commish_action: Whether this is a commissioner-forced trade
        """
        player_initial_dict = {
            "total": 0,
            "trade_partners": {
                # "trade_partner": num_times_acquired_from
            }
        }

        if transaction_id in MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"]["trades"]["transaction_ids"]:
            # Trade already processed for this week
            return
        
        self._add_to_transaction_ids_cache(
            {
                "type": "trade",
                "manager": manager,
                "trade_partners": trade_partners,
                "acquired": acquired,
                "sent": sent,
                "transaction_id": transaction_id
            },
            commish_action
        )
        
        top_level_summary = MANAGER_CACHE[manager]["summary"]["transactions"]["trades"]
        yearly_summary = MANAGER_CACHE[manager]["years"][self._year]["summary"]["transactions"]["trades"]
        weekly_summary = MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"]["trades"]
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
    
    def _process_add_or_drop_transaction(self, transaction: dict, commish_action: bool) -> None:
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
            transaction: Raw add/drop transaction from Sleeper API
            commish_action: Whether this is a commissioner action
        """
        adds  = transaction.get("adds", {})
        drops = transaction.get("drops", {})

        if not adds and not drops:
            print("Waiver transaction with no adds or drops:", transaction)
            return
        
        if adds:
            for player_id in adds:
                roster_id = adds[player_id]
                
                manager = self._weekly_roster_ids.get(roster_id, None)
                player_name = PLAYER_IDS_CACHE.get(player_id, {}).get("full_name", "unknown_player")
                
                transaction_id = transaction.get("transaction_id", "")

                # add add details to the cache
                waiver_bid = None
                if self._use_faab and transaction.get("settings", None) != None:
                    waiver_bid = transaction.get("settings", {}).get("waiver_bid", None)
                self._add_add_or_drop_details_to_cache("add", manager, player_name, transaction_id, commish_action, waiver_bid)
                update_players_cache(player_id)
                
                # add FAAB details to the cache
                if self._use_faab and transaction.get("settings", None) != None:
                    faab_amount = transaction.get("settings", {}).get("waiver_bid", 0)
                    transaction_type = transaction.get("type", "")
                    self._add_faab_details_to_cache(transaction_type, manager, player_name, faab_amount, transaction_id)
        
        if drops:
            for player_id in drops:
                roster_id = drops[player_id]
                
                manager = self._weekly_roster_ids.get(roster_id, None)
                player_name = PLAYER_IDS_CACHE.get(player_id, {}).get("full_name", "unknown_player")
                
                transaction_id = transaction.get("transaction_id", "")

                # add drop details to the cache
                self._add_add_or_drop_details_to_cache("drop", manager, player_name, transaction_id, commish_action)
                update_players_cache(player_id)
    
    def _add_add_or_drop_details_to_cache(self, free_agent_type: str, manager: str,
                                         player_name: str, transaction_id: str,
                                         commish_action: bool,
                                         waiver_bid: int|None = None) -> None:
        """
        Update cache with add or drop details at all aggregation levels.

        Updates cache at 3 levels (weekly, yearly, all-time) with:
        - Total add/drop count
        - Player-specific counts

        Args:
            free_agent_type: Either "add" or "drop"
            manager: Manager name
            player_name: Full player name
            transaction_id: Unique transaction ID
            commish_action: Whether this is a commissioner action
            waiver_bid: FAAB amount bid (for adds only)
        """
        if free_agent_type not in ["add", "drop"]:
            return

        if transaction_id in MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"][f"{free_agent_type}s"]["transaction_ids"]:
            # Add already processed for this week
            return
        
        self._add_to_transaction_ids_cache(
            {
                "type": "add_or_drop",
                "free_agent_type": free_agent_type,
                "manager": manager,
                "player_name": player_name,
                "transaction_id": transaction_id,
                "waiver_bid": waiver_bid
            },
            commish_action
        )
        
        top_level_summary = MANAGER_CACHE[manager]["summary"]["transactions"][f"{free_agent_type}s"]
        yearly_summary = MANAGER_CACHE[manager]["years"][self._year]["summary"]["transactions"][f"{free_agent_type}s"]
        weekly_summary = MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"][f"{free_agent_type}s"]
        summaries = [top_level_summary, yearly_summary, weekly_summary]
        
        # Add add details in all summaries
        for summary in summaries:
            if player_name not in summary["players"]:
                summary["players"][player_name] = 0
            summary["players"][player_name] += 1
            summary["total"] += 1
        
        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)
    
    def _add_faab_details_to_cache(self, transaction_type: str, manager: str,
                                   player_name: str, faab_amount: int,
                                   transaction_id: str,
                                   trade_partner: str = None) -> None:
        """
        Update cache with FAAB spending and trading details.

        Handles two types of FAAB transactions:
        1. Waiver/free agent: FAAB spent on player acquisitions
        2. Trade: FAAB traded between managers (can be positive or negative)

        Updates cache at 3 levels (weekly, yearly, all-time) with:
        - Total FAAB lost/gained
        - Player-specific FAAB spent (for waivers)
        - Trade partner FAAB exchanges (for trades)

        Args:
            transaction_type: "waiver", "free_agent", "commissioner", or "trade"
            manager: Manager name
            player_name: Player name (for waivers) or "FAAB" (for trades)
            faab_amount: Amount of FAAB (positive for spent/sent, negative for received in trade)
            transaction_id: Unique transaction ID
            trade_partner: Other manager in FAAB trade (required for trades)
        """
        if transaction_type == "trade" and trade_partner is None:
            print("Trade transaction missing trade partner for FAAB processing:", transaction_type, manager, player_name, faab_amount, transaction_id)
            return

        if transaction_id in MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"]["faab"]["transaction_ids"]:
            # Waiver already processed for this week
            return
        
        
        top_level_summary = MANAGER_CACHE[manager]["summary"]["transactions"]["faab"]
        yearly_summary = MANAGER_CACHE[manager]["years"][self._year]["summary"]["transactions"]["faab"]
        weekly_summary = MANAGER_CACHE[manager]["years"][self._year]["weeks"][self._week]["transactions"]["faab"]
        summaries = [top_level_summary, yearly_summary, weekly_summary]

        if transaction_type in ["free_agent", "waiver", "commissioner"]:
            # Add waiver details in all summaries
            for summary in summaries:
                # Process total lost or gained
                summary["total_lost_or_gained"] -= faab_amount

                # Process player-specific FAAB amounts
                if player_name not in summary["players"]:
                    summary["players"][player_name] = {
                        'num_bids_won': 0,
                        'total_faab_spent': 0
                    }
                summary["players"][player_name]['num_bids_won']     += 1
                summary["players"][player_name]['total_faab_spent'] += faab_amount
        
        elif transaction_type == "trade":
            # Add trade FAAB details in all summaries
            for summary in summaries:
                if faab_amount > 0:
                    # Acquired FAAB
                    summary["total_lost_or_gained"] += faab_amount
                    summary["acquired_from"]["total"] += faab_amount
                    
                    if trade_partner not in summary["acquired_from"]["trade_partners"]:
                        summary["acquired_from"]["trade_partners"][trade_partner] = 0
                    summary["acquired_from"]["trade_partners"][trade_partner] += faab_amount
                
                # Traded FAAB away
                if faab_amount < 0:
                    summary["total_lost_or_gained"] += faab_amount
                    summary["traded_away"]["total"] -= faab_amount
                    
                    if trade_partner not in summary["traded_away"]["trade_partners"]:
                        summary["traded_away"]["trade_partners"][trade_partner] = 0
                    summary["traded_away"]["trade_partners"][trade_partner] -= faab_amount
        
        else:
            print("Unexpected transaction type for FAAB processing:", transaction_type)
            return
        
        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)
    
    def _add_to_transaction_ids_cache(self, transaction_info: dict, commish_action: bool) -> None:
        """
        Add transaction to global transaction IDs cache for deduplication and reversal detection.

        Creates comprehensive transaction record including:
        - Year, week, transaction type
        - Managers involved
        - Players/assets involved
        - Trade details (for trades)
        - Add/drop details (for add_or_drop)
        - Commissioner action flag

        This cache enables:
        1. Deduplication (prevent processing same transaction twice)
        2. Reversal detection (detect joke trades/accidental transactions)
        3. Transaction history tracking

        Args:
            transaction_info: Dict with transaction details (type, manager, etc.)
            commish_action: Whether this is a commissioner action

        Raises:
            ValueError: If required fields missing from transaction_info
        """
        transaction_type = transaction_info.get("type", "")
        if not transaction_type:
            raise ValueError(f"Transaction type not found in transaction_info: {transaction_info}")
        
        transaction_id = transaction_info.get("transaction_id", "")
        if not transaction_id:
            raise ValueError(f"Transaction transaction_id not found in transaction_info: {transaction_info}")
        
        manager = transaction_info.get("manager", "")
        if not manager:
            raise ValueError(f"Transaction manager not found in transaction_info: {transaction_info}")
        
        valid_add_or_drop_types = ["add", "drop", "commissioner"]
        if transaction_type == "add_or_drop":
            transaction_type = transaction_info.get("free_agent_type", "")
            if transaction_type not in valid_add_or_drop_types:
                raise ValueError(f"Transaction type {transaction_info.get('type') } not a valid 'add_or_drop' type, needs to be one of: {valid_add_or_drop_types}")
        
        # If transaction not in cache, make a new object
        if transaction_id not in TRANSACTION_IDS_CACHE:
            TRANSACTION_IDS_CACHE[transaction_id] = {
                "year":              self._year,
                "week":              self._week,
                "commish_action":    commish_action,
                "managers_involved": [],
                "types":             [],
                "players_involved":  []
            }
        transaction_info_to_cache = TRANSACTION_IDS_CACHE[transaction_id]

        

        if manager not in transaction_info_to_cache["managers_involved"]:
            transaction_info_to_cache["managers_involved"].append(manager)
            
        if transaction_type not in transaction_info_to_cache["types"]:
            transaction_info_to_cache["types"].append(transaction_type)
        

        # Add/Drop transactions
        if transaction_type in valid_add_or_drop_types:
            player_name = transaction_info.get("player_name", "")
            if not player_name:
                raise ValueError(f"player_name not found for {transaction_type} with info: {transaction_info}")
            transaction_info_to_cache["players_involved"].append(transaction_info.get("player_name", ""))
            
            if transaction_type in transaction_info_to_cache:
                raise ValueError(f"Can only add or drop one player per transaction.")
            
            transaction_info_to_cache[transaction_type] = player_name

            if transaction_type == "add" and self._use_faab and transaction_info.get("waiver_bid", None) != None:
                transaction_info_to_cache["faab_spent"] = transaction_info["waiver_bid"]
        
        # Trade transaction
        elif transaction_type == "trade":

            # Get players acquired and players sent
            players_acquired = transaction_info.get("acquired", {})
            players_sent = transaction_info.get("sent", {})
            
            # Initialize trade details if not already in cache
            if "trade_details" not in transaction_info_to_cache:
                transaction_info_to_cache["trade_details"] = {}

            # Add all managers involved if not already in list
            for partner in transaction_info.get("trade_partners", []):
                if partner and partner not in transaction_info_to_cache["managers_involved"]:
                    transaction_info_to_cache["managers_involved"].append(partner)
            
            # Adding player from players_acquired into players_involved and into the trade
            # details if not already in cache
            for player in players_acquired:
                if not player:
                    continue
                
                if player not in transaction_info_to_cache["players_involved"]:
                    transaction_info_to_cache["players_involved"].append(player)
                
                if player not in transaction_info_to_cache["trade_details"]:
                    transaction_info_to_cache["trade_details"][player] = {
                        "old_manager": players_acquired[player],
                        "new_manager": manager
                    }
                
            
            # Adding player from players_sent into players_involved and into the trade
            # details if not already in cache
            for player in players_sent:
                if not player:
                    continue
                
                if player not in transaction_info_to_cache["players_involved"]:
                    transaction_info_to_cache["players_involved"].append(player)
                
                if player not in transaction_info_to_cache["trade_details"]:
                    transaction_info_to_cache["trade_details"][player] = {
                        "old_manager": manager,
                        "new_manager": players_sent[player]
                    }


        # FAAB data being handled in trades and add/drop for transactions
        elif transaction_type != "faab":
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        if transaction_id not in self._weekly_transaction_ids:
            self._weekly_transaction_ids.append(transaction_id)