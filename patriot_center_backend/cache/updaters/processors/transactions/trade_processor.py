"""Process trade transactions."""

import logging
from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.player_cache_updater import (
    update_players_cache,
)
from patriot_center_backend.cache.updaters.processors.transactions.faab_processor import (  # noqa: E501
    add_faab_details_to_cache,
)
from patriot_center_backend.cache.updaters.processors.transactions.transaction_id_processor import (  # noqa: E501
    add_to_transaction_ids,
)
from patriot_center_backend.managers.formatters import draft_pick_decipher

logger = logging.getLogger(__name__)


def process_trade_transaction(
    year: str,
    week: str,
    transaction: dict[str, Any],
    roster_ids: dict[int, str],
    weekly_transaction_ids: list[str],
    commish_action: bool,
    use_faab: bool,
) -> None:
    """Process a trade transaction.

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
        weekly_transaction_ids: List of transaction IDs for this week
        commish_action: Whether this is a commissioner-forced trade
        use_faab: Whether FAAB is used
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    for roster_id in transaction.get("roster_ids", []):
        manager = roster_ids.get(roster_id)

        if not manager:
            logger.warning(f"Unknown manager: {roster_id}")
            continue

        trade_partners = deepcopy(transaction.get("roster_ids", []))
        trade_partners.remove(roster_id)
        for i in range(len(trade_partners)):
            trade_partners[i] = roster_ids.get(
                trade_partners[i], "unknown_manager"
            )

        # Players/Draft Picks Acquired and Sent
        acquired = {}
        if transaction.get("adds"):
            for player_id in transaction.get("adds", {}):
                if transaction["adds"][player_id] == roster_id:
                    player_name = player_ids_cache.get(player_id, {}).get(
                        "full_name", "unknown_player"
                    )

                    acquired[player_name] = roster_ids.get(
                        transaction["drops"][player_id], "unknown_manager"
                    )
                    update_players_cache(player_id)

        sent = {}
        if transaction.get("drops"):
            for player_id in transaction.get("drops", {}):
                if transaction["drops"][player_id] == roster_id:
                    player_name = player_ids_cache.get(player_id, {}).get(
                        "full_name", "unknown_player"
                    )

                    sent[player_name] = roster_ids.get(
                        transaction["adds"][player_id], "unknown_manager"
                    )
                    update_players_cache(player_id)

        if transaction.get("draft_picks"):
            for draft_pick in transaction.get("draft_picks", []):
                # Acquired draft pick
                if draft_pick.get("owner_id") == roster_id:
                    draft_pick_name = draft_pick_decipher(
                        draft_pick, roster_ids
                    )
                    acquired[draft_pick_name] = roster_ids.get(
                        draft_pick.get("previous_owner_id", "unknown_manager"),
                        "unknown_manager",
                    )

                # Sent draft pick
                if draft_pick.get("previous_owner_id") == roster_id:
                    draft_pick_name = draft_pick_decipher(
                        draft_pick, roster_ids
                    )
                    sent[draft_pick_name] = roster_ids.get(
                        draft_pick.get("owner_id", "unknown_manager"),
                        "unknown_manager",
                    )

        transaction_id = transaction.get("transaction_id", "")

        # get faab traded information
        if use_faab and len(transaction.get("waiver_budget", [])) != 0:
            for faab_details in transaction["waiver_budget"]:
                faab_receiver = roster_ids[faab_details["receiver"]]
                faab_sender = roster_ids[faab_details["sender"]]
                faab_amount = faab_details["amount"]

                faab_string = f"${faab_amount} FAAB"

                # same faab amount traded in this trade with another party
                if faab_string in sent or faab_string in acquired:
                    logger.warning(
                        f"{faab_string} already in internal storage "
                        f"for the following trade: {transaction}"
                    )

                if faab_sender == manager:
                    sent[faab_string] = faab_receiver
                elif faab_receiver == manager:
                    acquired[faab_string] = faab_sender

        # add trade details to the cache
        add_trade_details_to_cache(
            year,
            week,
            manager,
            trade_partners,
            acquired,
            sent,
            weekly_transaction_ids,
            transaction_id,
            commish_action,
            use_faab,
        )

    # Faab Trading
    waiver_budget = transaction.get("waiver_budget", [])
    if use_faab and waiver_budget:
        for faab_transaction in waiver_budget:
            faab_amount = faab_transaction.get("amount", 0)
            sender = roster_ids.get(faab_transaction.get("sender"))
            receiver = roster_ids.get(faab_transaction.get("receiver"))
            transaction_id = transaction.get("transaction_id", "")

            if not sender or not receiver:
                logger.warning(f"Unknown manager in faab trade: {transaction}")
                continue

            # add faab trade details to the cache
            for mgr in [sender, receiver]:
                if mgr == sender:
                    opposite_manager = receiver
                    faab = -faab_amount
                else:
                    opposite_manager = sender
                    faab = faab_amount

                add_faab_details_to_cache(
                    year,
                    week,
                    "trade",
                    mgr,
                    "FAAB",
                    faab,
                    transaction_id,
                    trade_partner=opposite_manager,
                )


def add_trade_details_to_cache(
    year: str,
    week: str,
    manager: str,
    trade_partners: list[str],
    acquired: dict[str, str],
    sent: dict[str, str],
    weekly_transaction_ids: list[str],
    transaction_id: str,
    commish_action: bool,
    use_faab: bool,
) -> None:
    """Update cache with trade details at all aggregation levels.

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
        weekly_transaction_ids: List of transaction IDs
        transaction_id: Unique transaction ID
        commish_action: Whether this is a commissioner-forced trade
        use_faab: Whether FAAB was involved in this trade
            and in a year where FAAB was used
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    player_initial_dict = {
        "total": 0,
        "trade_partners": {
            # "trade_partner": num_times_acquired_from
        },
    }

    mgr_lvl = manager_cache[manager]
    yr_lvl = mgr_lvl["years"][year]
    wk_lvl = yr_lvl["weeks"][week]

    if transaction_id in wk_lvl["transactions"]["trades"]["transaction_ids"]:
        # Trade already processed for this week
        return

    transaction_info = {
        "type": "trade",
        "manager": manager,
        "trade_partners": trade_partners,
        "acquired": acquired,
        "sent": sent,
        "transaction_id": transaction_id,
    }
    add_to_transaction_ids(
        year,
        week,
        transaction_info,
        weekly_transaction_ids,
        commish_action,
        use_faab,
    )

    top_level_summary = mgr_lvl["summary"]["transactions"]["trades"]
    yearly_summary = yr_lvl["summary"]["transactions"]["trades"]
    weekly_summary = wk_lvl["transactions"]["trades"]
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
            if (
                acquired[player]
                not in (acquired_summary[player]["trade_partners"])
            ):
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


def revert_trade_transaction(
    transaction_id1: str,
    transaction_id2: str,
    weekly_transaction_ids: list[str],
) -> None:
    """Revert two trade transactions that cancel each other out.

    Removes both transactions from cache at all levels (weekly, yearly,
    all-time) and removes from transaction ID list. Used for joke trades
    or accidental trades.

    Args:
        transaction_id1: First transaction ID to revert
        transaction_id2: Second transaction ID to revert
        weekly_transaction_ids: A list of transaction IDs for the current week.
            - This list is updated to remove the reverted transaction IDs.
    """
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()
    manager_cache = CACHE_MANAGER.get_manager_cache()

    transaction = deepcopy(transaction_ids_cache[transaction_id1])

    year = transaction["year"]
    week = transaction["week"]

    for manager in transaction["managers_involved"]:
        mgr_lvl = manager_cache[manager]
        yr_lvl = mgr_lvl["years"][year]
        wk_lvl = yr_lvl["weeks"][week]

        overall_trades = mgr_lvl["summary"]["transactions"]
        yearly_trades = yr_lvl["summary"]["transactions"]
        weekly_trades = wk_lvl["transactions"]

        # Remove transaction IDs from cache
        if transaction_id1 in weekly_trades["trades"]["transaction_ids"]:
            weekly_trades["trades"]["transaction_ids"].remove(transaction_id1)
        if transaction_id2 in weekly_trades["trades"]["transaction_ids"]:
            weekly_trades["trades"]["transaction_ids"].remove(transaction_id2)

        if transaction_id1 in (
            weekly_trades.get("faab", {}).get("transaction_ids", [])
        ):
            weekly_trades["faab"]["transaction_ids"].remove(transaction_id1)

        if transaction_id2 in (
            weekly_trades.get("faab", {}).get("transaction_ids", [])
        ):
            weekly_trades["faab"]["transaction_ids"].remove(transaction_id2)

        for d in [overall_trades, yearly_trades, weekly_trades]:
            # if there were 2 trades made, these 2 were the 2,
            # so it should now be empty
            d["trades"]["total"] -= 2
            if d["trades"]["total"] == 0:
                d["trades"]["trade_partners"] = {}
                d["trades"]["trade_players_acquired"] = {}
                d["trades"]["trade_players_sent"] = {}
                d["trades"]["transaction_ids"] = []
                continue

            # Remove from trade partners and
            # traverse trade details by trade partner
            other_managers = deepcopy(transaction["managers_involved"])
            other_managers.remove(manager)
            for other_manager in other_managers:
                d["trades"]["trade_partners"][other_manager] -= 2
                if d["trades"]["trade_partners"][other_manager] == 0:
                    del d["trades"]["trade_partners"][other_manager]

            for player in list(transaction["trade_details"].keys()):
                new_mgr = transaction["trade_details"][player].get(
                    "new_manager"
                )
                old_mgr = transaction["trade_details"][player].get(
                    "old_manager"
                )

                if not new_mgr or not old_mgr:
                    logger.warning(
                        f"Transaction {transaction} has missing manager info."
                    )
                    continue

                # If manager wasn't involved, skip
                if manager != new_mgr and manager != old_mgr:
                    continue

                plyrs_acq = d["trades"]["trade_players_acquired"]
                plyrs_sent = d["trades"]["trade_players_sent"]

                trade_partner = new_mgr if manager == old_mgr else old_mgr

                # Remove from acquired
                plyrs_acq[player]["total"] -= 1
                if plyrs_acq[player]["total"] == 0:
                    del plyrs_acq[player]
                else:
                    plyrs_acq[player]["trade_partners"][trade_partner] -= 1
                    if plyrs_acq[player]["trade_partners"][trade_partner] == 0:
                        del plyrs_acq[player]["trade_partners"][trade_partner]

                # Remove from sent
                plyrs_sent[player]["total"] -= 1
                if plyrs_sent[player]["total"] == 0:
                    del plyrs_sent[player]
                else:
                    plyrs_sent[player]["trade_partners"][trade_partner] -= 1
                    if plyrs_sent[player]["trade_partners"][trade_partner] == 0:
                        del plyrs_sent[player]["trade_partners"][trade_partner]

                # faab is here, the logic is to turn it
                # into an int, so player = "$1 FAAB" -> faab = 1
                if "FAAB" in player:
                    faab = player.split(" ")[0]
                    faab = faab.replace("$", "")
                    faab = int(faab)

                    # Remove from traded
                    faab_traded = d["faab"]["traded_away"]

                    faab_traded["total"] -= faab
                    faab_traded["trade_partners"][trade_partner] -= faab
                    if faab_traded["trade_partners"][trade_partner] == 0:
                        del faab_traded["trade_partners"][trade_partner]

                    # Remove from acquired
                    faab_acq = d["faab"]["acquired_from"]

                    faab_acq["total"] -= faab
                    faab_acq["trade_partners"][trade_partner] -= faab
                    if faab_acq["trade_partners"][trade_partner] == 0:
                        del faab_acq["trade_partners"][trade_partner]

    del transaction_ids_cache[transaction_id1]
    del transaction_ids_cache[transaction_id2]
    if transaction_id1 in weekly_transaction_ids:
        weekly_transaction_ids.remove(transaction_id1)
    if transaction_id2 in weekly_transaction_ids:
        weekly_transaction_ids.remove(transaction_id2)
