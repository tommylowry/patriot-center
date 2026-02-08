"""Process add/drop transactions (waivers, free agents, commish actions)."""

import logging
from copy import deepcopy
from typing import Any, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.processors.transactions.faab_processor import (  # noqa: E501
    add_faab_details_to_cache,
)
from patriot_center_backend.cache.updaters.processors.transactions.transaction_id_processor import (  # noqa: E501
    add_to_transaction_ids,
)
from patriot_center_backend.models import Player

logger = logging.getLogger(__name__)


def process_add_or_drop_transaction(
    year: str,
    week: str,
    transaction: dict[str, Any],
    roster_ids: dict[int, str],
    weekly_transaction_ids: list[str],
    commish_action: bool,
    use_faab: bool,
) -> None:
    """Process add/drop transactions (waivers, free agents, commish actions).

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
        weekly_transaction_ids: List of transaction IDs for this week
        commish_action: Whether this is a commissioner action
        use_faab: if faab was used at the time of this transaction
    """
    adds = transaction.get("adds", {})
    drops = transaction.get("drops", {})

    if not adds and not drops:
        logger.warning("Waiver transaction with no adds or drops:", transaction)
        return

    if adds:
        for player_id in adds:
            player = Player(player_id)

            roster_id = adds[str(player)]

            manager = roster_ids.get(roster_id, "unknown_manager")
            if manager == "unknown_manager":
                logger.warning(
                    f"Could not find manager for roster ID: {roster_id}"
                )

            transaction_id = transaction.get(
                "transaction_id", "unknown_transaction_id"
            )
            if transaction_id == "unknown_transaction_id":
                logger.warning(
                    f"Could not find transaction ID "
                    f"for transaction: {transaction}"
                )

            # add add details to the cache
            waiver_bid = None
            if use_faab and transaction.get("settings"):
                waiver_bid = transaction.get("settings", {}).get("waiver_bid")
            add_add_or_drop_details_to_cache(
                year,
                week,
                weekly_transaction_ids,
                "add",
                manager,
                player,
                transaction_id,
                commish_action,
                use_faab,
                waiver_bid=waiver_bid,
            )

            # add FAAB details to the cache
            if use_faab and transaction.get("settings"):
                faab_amount = transaction.get("settings", {}).get(
                    "waiver_bid", 0
                )
                transaction_type = transaction.get("type", "")
                add_faab_details_to_cache(
                    year,
                    week,
                    transaction_type,
                    manager,
                    str(player),
                    faab_amount,
                    transaction_id,
                )

    if drops:
        for player_id in drops:
            player = Player(player_id)

            roster_id = drops[str(player)]

            manager = roster_ids.get(roster_id, "unknown_manager")
            if manager == "unknown_manager":
                logger.warning(
                    f"Could not find manager for roster ID: {roster_id}"
                )

            transaction_id = transaction.get("transaction_id", "")

            # add drop details to the cache
            add_add_or_drop_details_to_cache(
                year,
                week,
                weekly_transaction_ids,
                "drop",
                manager,
                player,
                transaction_id,
                commish_action,
                use_faab,
            )


def add_add_or_drop_details_to_cache(
    year: str,
    week: str,
    weekly_transaction_ids: list[str],
    free_agent_type: str,
    manager: str,
    player: Player,
    transaction_id: str,
    commish_action: bool,
    use_faab: bool,
    waiver_bid: int | None = None,
) -> None:
    """Update cache with add or drop details at all aggregation levels.

    Updates cache at 3 levels (weekly, yearly, all-time) with:
    - Total add/drop count
    - Player-specific counts

    Args:
        year: Year of this transaction
        week: Week of this transaction
        weekly_transaction_ids: List of transaction ids for the week
        free_agent_type: Either "add" or "drop"
        manager: Manager name
        player: Player object
        transaction_id: Unique transaction ID
        commish_action: Whether this is a commissioner action
        use_faab: Whether faab was used that season
        waiver_bid: FAAB amount bid (for faab adds only)
    """
    if free_agent_type not in ["add", "drop"]:
        return

    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    if transaction_id in (
        manager_cache.get(manager, {})
        .get("years", {})
        .get(year, {})
        .get("weeks", {})
        .get(week, {})
        .get("transactions", {})
        .get(f"{free_agent_type}s", {})
        .get("transaction_ids", [])
    ):
        # Add already processed for this week
        return

    transaction_info = {
        "type": "add_or_drop",
        "free_agent_type": free_agent_type,
        "manager": manager,
        "player": player,
        "transaction_id": transaction_id,
        "waiver_bid": waiver_bid,
    }
    add_to_transaction_ids(
        year,
        week,
        transaction_info,
        weekly_transaction_ids,
        commish_action,
        use_faab,
    )
    manager_level = manager_cache[manager]
    top_lvl = manager_level["summary"]
    top_level_summary = top_lvl["transactions"][f"{free_agent_type}s"]

    yr_level = manager_level["years"][year]
    yr_summary = yr_level["summary"]
    yearly_summary = yr_summary["transactions"][f"{free_agent_type}s"]

    wk_summary = yr_level["weeks"][week]
    weekly_summary = wk_summary["transactions"][f"{free_agent_type}s"]

    summaries = [top_level_summary, yearly_summary, weekly_summary]

    # Add add details in all summaries
    for summary in summaries:
        if str(player) not in summary["players"]:
            summary["players"][str(player)] = 0
        summary["players"][str(player)] += 1
        summary["total"] += 1

    # Finally, add transaction ID to weekly summary to avoid double counting
    weekly_summary["transaction_ids"].append(transaction_id)


def revert_add_drop_transaction(
    transaction_id: str,
    transaction_type: Literal["add", "drop"],
    weekly_transaction_ids: list[str],
) -> bool | None:
    """Revert a specific add or drop from a transaction.

    - Used for commissioner reversals.
    - Decrements counts in cache at all levels and removes from transaction
    lists.
    - Handles FAAB spent if applicable. Returns whether transaction was fully
    removed.

    Args:
        transaction_id: Transaction ID to revert
        transaction_type: Either "add" or "drop" to specify which portion to
            revert
        weekly_transaction_ids: List of transaction IDs for the week

    Returns:
        True if transaction was completely removed from cache, False otherwise

    Raises:
        Exception: If transaction involves multiple managers (unexpected)
    """
    if transaction_type != "add" and transaction_type != "drop":
        logger.warning(
            f"Cannot revert type {transaction_type} "
            f"in revert_add_or_drop_transaction for "
            f"transaction_id: {transaction_id}"
        )
        return None  # Returns None to signal failure

    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    transaction = deepcopy(transaction_ids_cache[transaction_id])

    year = transaction["year"]
    week = transaction["week"]
    manager = transaction["managers_involved"][0]
    player_id = transaction[transaction_type]
    player = Player(player_id)

    if len(transaction["managers_involved"]) > 1:
        raise Exception(f"Weird {transaction_type} with multiple managers")

    mgr_lvl = manager_cache[manager]
    yr_lvl = mgr_lvl["years"][year]
    wk_lvl = yr_lvl["weeks"][week]

    mgr_trans = mgr_lvl["summary"]["transactions"]
    yr_trans = yr_lvl["summary"]["transactions"]
    wk_trans = wk_lvl["transactions"]

    places_to_change = [
        mgr_trans[f"{transaction_type}s"],
        yr_trans[f"{transaction_type}s"],
        wk_trans[f"{transaction_type}s"],
    ]

    for d in places_to_change:
        # remove the add/drop transaction from the cache
        d["total"] -= 1
        d["players"][str(player)] -= 1

        if d["players"][str(player)] == 0:
            del d["players"][str(player)]

    # If this transaction had faab spent and the transaction to remove is add,
    # remove the transaction id from the faab spent portion.
    if "faab_spent" in transaction and transaction_type == "add":
        if transaction_id in wk_trans["faab"]["transaction_ids"]:
            wk_trans["faab"]["transaction_ids"].remove(transaction_id)

        places_to_change = [
            mgr_trans["faab"],
            yr_trans["faab"],
            wk_trans["faab"],
        ]

        for d in places_to_change:
            d["players"][str(player)]["num_bids_won"] -= 1
            if d["players"][str(player)]["num_bids_won"] == 0:
                del d["players"][str(player)]

    # remove the transaction_type portion of this transaction and keep
    # it intact in case there was the other type involved
    del transaction_ids_cache[transaction_id][transaction_type]
    transaction_ids_cache[transaction_id]["types"].remove(transaction_type)
    transaction_ids_cache[transaction_id]["players_involved"].remove(
        str(player)
    )

    player.remove_transaction(transaction_id)

    # this was the only data in the transaction so it can be fully removed
    if len(transaction_ids_cache[transaction_id]["types"]) == 0:
        del transaction_ids_cache[transaction_id]
        if transaction_id in weekly_transaction_ids:
            weekly_transaction_ids.remove(transaction_id)
        return True  # return True if transaction_id was deleted

    return False  # return False if theres still more information
