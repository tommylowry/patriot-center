"""Cache query helpers for reading transaction related manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.formatters import (
    extract_dict_data,
    get_trade_card,
)


def get_transaction_details_from_cache(
    manager: str, year: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get comprehensive transaction summary with formatted data and image URLs.

    Extracts and formats trades, adds, drops, and FAAB spending including:
    - Trade partners and most acquired/sent players
    - Top added/dropped players
    - FAAB spending and trading

    All player/manager names enriched with image URLs.

    Args:
        year: Season year (optional - defaults to all-time stats)
        manager: Manager name

    Returns:
        Dictionary with trades, adds, drops, and faab summaries
    """
    main_manager_cache = CACHE_MANAGER.get_manager_cache()
    manager_data = deepcopy(main_manager_cache[manager])

    transaction_summary = {"trades": {}, "adds": {}, "drops": {}, "faab": {}}

    # Get all-time stats by default, or single season stats if year specified
    trans_cache = manager_data["summary"]["transactions"]
    if year:
        trans_cache = manager_data["years"][year]["summary"]["transactions"]

    # Flatten FAAB player data to just total spent (if FAAB exists)
    if "faab" in trans_cache:
        players = trans_cache["faab"]["players"]
        for player in list(players):
            players[player] = players[player]["total_faab_spent"]

    trades = {
        "total": trans_cache["trades"]["total"],
        "top_trade_partners": extract_dict_data(
            deepcopy(trans_cache["trades"]["trade_partners"])
        ),
    }

    # ---- Trades Summary ----
    # Most Aquired Players
    trade_players_acquired = trans_cache["trades"]["trade_players_acquired"]
    most_acquired_players = extract_dict_data(deepcopy(trade_players_acquired))
    for player in most_acquired_players:
        player_details = deepcopy(trade_players_acquired[player["name"]])
        player["from"] = extract_dict_data(
            deepcopy(player_details.get("trade_partners", {})),
            cutoff=0,
        )
    trades["most_acquired_players"] = most_acquired_players

    # Most Sent Players
    trade_players_sent = trans_cache["trades"]["trade_players_sent"]
    most_sent_players = extract_dict_data(deepcopy(trade_players_sent))
    for player in most_sent_players:
        player_details = deepcopy(trade_players_sent.get(player["name"], {}))
        player["to"] = extract_dict_data(
            player_details.get("trade_partners", {}), cutoff=0
        )
    trades["most_sent_players"] = most_sent_players

    transaction_summary["trades"] = trades

    # ---- Adds Summary ----
    adds = {
        "total": trans_cache["adds"]["total"],
        "top_players_added": extract_dict_data(
            deepcopy(trans_cache["adds"]["players"])
        ),
    }
    transaction_summary["adds"] = adds

    # ---- Drops Summary ----
    drops = {
        "total": trans_cache["drops"]["total"],
        "top_players_dropped": extract_dict_data(
            deepcopy(trans_cache["drops"]["players"])
        ),
    }
    transaction_summary["drops"] = drops

    # ---- FAAB Summary ----
    # Handle cases where FAAB doesn't exist
    # (e.g., older years before FAAB was implemented)
    if trans_cache.get("faab"):
        faab = {
            "total_spent": abs(trans_cache["faab"]["total_lost_or_gained"]),
            "biggest_acquisitions": extract_dict_data(
                deepcopy(trans_cache["faab"]["players"]),
                value_name="amount",
            ),
        }

        # FAAB Traded
        sent = trans_cache["faab"]["traded_away"]["total"]
        received = trans_cache["faab"]["acquired_from"]["total"]
        net = received - sent
        faab["faab_traded"] = {"sent": sent, "received": received, "net": net}
    else:
        # FAAB not available for this year/manager
        faab = {
            "total_spent": 0,
            "biggest_acquisitions": [],
            "faab_traded": {"sent": 0, "received": 0, "net": 0},
        }
    transaction_summary["faab"] = faab

    # Return final transaction summary
    return deepcopy(transaction_summary)


def get_trade_history_between_two_managers(
    manager1: str,
    manager2: str,
    year: str | None = None,
) -> list[dict[str, Any]]:
    """Get complete trade history between two managers.

    Finds all trades involving both managers and returns formatted trade cards.

    Args:
        manager1: First manager name
        manager2: Second manager name
        year: Season year (optional - defaults to all-time if None)

    Returns:
        List of trade cards in reverse chronological order (newest first)
    """
    main_manager_cache = CACHE_MANAGER.get_manager_cache()
    manager_1_data = deepcopy(main_manager_cache.get(manager1, {}))

    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

    years = list(manager_1_data.get("years", {}).keys())
    if year:
        years = [year]

    # Gather all transaction IDs for manager_1
    transaction_ids = []
    for y in years:
        weeks = manager_1_data["years"][y]["weeks"]
        for w in weeks:
            weekly_trade_transaction_ids = (
                weeks.get(w, {})
                .get("transactions", {})
                .get("trades", {})
                .get("transaction_ids", [])
            )
            transaction_ids.extend(weekly_trade_transaction_ids)

    # Filter to only those involving both managers
    for tid in deepcopy(transaction_ids):
        if manager2 not in (
            transaction_ids_cache.get(tid, {}).get("managers_involved", [])
        ):
            transaction_ids.remove(tid)

    trades_between = []

    for t in transaction_ids:
        trades_between.append(get_trade_card(t))

    trades_between.reverse()
    return trades_between


def get_manager_transaction_history_from_cache(
    manager_name: str, year: str | None
) -> dict[str, Any]:
    """Get manager transaction history from cache.

    Args:
        manager_name: The name of the manager.
        year: Optional year to filter transactions. Defaults to all-time.

    Returns:
        Dictionary of transaction history.

    Raises:
        ValueError: If the manager or year is not found in the cache.
    """
    main_manager_cache = CACHE_MANAGER.get_manager_cache()

    if manager_name not in main_manager_cache:
        raise ValueError(f"Manager {manager_name} not found in cache.")

    manager_data = deepcopy(main_manager_cache[manager_name])

    if year and year not in main_manager_cache[manager_name]["years"]:
        raise ValueError(
            f"Year {year} not found for manager {manager_name} in cache."
        )

    years_to_get = list(manager_data.get("years", {}).keys())
    if year:
        years_to_get = [year]

    return_data = {
        manager_name: {"years": {}},
    }

    for y in years_to_get:
        return_data[manager_name]["years"][y] = {"weeks": {}}
        for w in list(manager_data["years"][y]["weeks"]):
            return_data[manager_name]["years"][y]["weeks"][w] = {
                "transactions": (
                    manager_data
                    ["years"]
                    [y]
                    ["weeks"]
                    [w]
                    ["transactions"]
                )
            }

    return deepcopy(return_data)


def get_transaction_from_ids_cache(transaction_id: str) -> dict[str, Any]:
    """Get transaction from transaction ID.

    Args:
        transaction_id: The ID of the transaction.

    Returns:
        Dictionary of transaction data.
    """
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

    return deepcopy(transaction_ids_cache.get(transaction_id, {}))
