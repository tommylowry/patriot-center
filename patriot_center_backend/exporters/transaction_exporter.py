"""Transaction exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.transaction_queries import (
    get_manager_transaction_history_from_cache,
    get_transaction_from_ids_cache,
)
from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.formatters import get_trade_card
from patriot_center_backend.utils.helpers import get_user_id


def get_manager_transactions(
    manager_name: str, year: str | None = None
) -> dict[str, Any]:
    """Get manager transaction history.

    Args:
        manager_name: The name of the manager.
        year: Optional year to filter transactions.

    Returns:
        dictionary with manager transaction history.
    """
    # TODO: remove this once managers are stored in cache
    user_id = get_user_id(manager_name)
    if not user_id:
        raise ValueError(f"Manager {manager_name} not found in cache.")
    manager_obj = Manager(user_id)
    # END TODO
    manager_transactions = get_manager_transaction_history_from_cache(
        manager_name, year
    )

    transaction_history = manager_obj.get_metadata()
    transaction_history["total_count"] = 0
    transaction_history["transactions"] = []

    # Gather transactions based on filters
    filtered_transactions = []
    years_to_check = list(manager_transactions[manager_name]["years"].keys())

    for yr in years_to_check:
        yearly_data = manager_transactions[manager_name]["years"][yr]
        for week in yearly_data.get("weeks", {}):
            weekly_transactions = deepcopy(
                yearly_data["weeks"][week]["transactions"]
            )

            # Trades
            trade_data = weekly_transactions.get("trades", {})
            transaction_ids = deepcopy(trade_data.get("transaction_ids", []))

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                trade_details = get_trade_card(transaction_id)

                trade_details["type"] = "trade"
                filtered_transactions.append(deepcopy(trade_details))

            # Adds
            adds_data = weekly_transactions.get("adds", {})
            transaction_ids = deepcopy(adds_data.get("transaction_ids", []))

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                # Only include adds portion of a
                #   transaction for "add" filter
                add_details = get_transaction_from_ids_cache(transaction_id)
                if add_details and "add" in add_details.get("types", []):
                    player = Player(add_details["add"])

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "add",
                        "player": player.get_metadata(),
                        # None if FAAB not implemented yet
                        #   or a free agent add
                        "faab_spent": add_details.get("faab_spent", None),
                        "transaction_id": transaction_id,
                    }
                    filtered_transactions.append(deepcopy(transaction_item))

            # Drops
            drops_data = weekly_transactions.get("drops", {})
            transaction_ids = deepcopy(drops_data.get("transaction_ids", []))

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                drop_details = get_transaction_from_ids_cache(transaction_id)
                if drop_details and "drop" in drop_details.get("types", []):
                    player = Player(drop_details["drop"])

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "drop",
                        "player": player.get_metadata(),
                        "transaction_id": transaction_id,
                    }
                    filtered_transactions.append(deepcopy(transaction_item))

            # Adds and Drops
            adds_data = weekly_transactions.get("adds", {})
            transaction_ids = deepcopy(adds_data.get("transaction_ids", []))

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                add_drop_details = get_transaction_from_ids_cache(
                    transaction_id
                )

                # Only include add_and_drop transactions
                types = add_drop_details.get("types", [])
                if types and "add" in types and "drop" in types:
                    added_player = Player(add_drop_details["add"])
                    dropped_player = Player(add_drop_details["drop"])

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "add_and_drop",
                        "added_player": added_player.get_metadata(),
                        "dropped_player": dropped_player.get_metadata(),
                        # None if FAAB not implemented yet
                        # or a free agent add/drop
                        "faab_spent": (
                            add_drop_details.get("faab_spent", None)
                        ),
                        "transaction_id": transaction_id,
                    }
                    filtered_transactions.append(deepcopy(transaction_item))

    # Set total count
    transaction_history["total_count"] = len(filtered_transactions)

    filtered_transactions.reverse()

    # Set transactions in output
    transaction_history["transactions"] = deepcopy(filtered_transactions)

    return deepcopy(transaction_history)
