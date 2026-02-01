"""Transaction exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.transaction_queries import (
    get_manager_transaction_history_from_cache,
    get_transaction_from_ids_cache,
)
from patriot_center_backend.utils.formatters import get_trade_card
from patriot_center_backend.utils.image_url_handler import get_image_url


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
    manager_transactions = get_manager_transaction_history_from_cache(
        manager_name, year
    )

    transaction_history = {
        "name": get_image_url(
            manager_name, dictionary=True
        ),

        "total_count": 0,
        "transactions": []
    }

    # Gather transactions based on filters
    filtered_transactions = []
    years_to_check = list(manager_transactions[manager_name]["years"].keys())

    for yr in years_to_check:
        yearly_data = manager_transactions[manager_name]["years"][yr]
        for week in yearly_data.get("weeks", {}):
            weekly_transactions = deepcopy(
                yearly_data["weeks"][week]["transactions"])

            # Trades
            trade_data = weekly_transactions.get("trades", {})
            transaction_ids = deepcopy(
                trade_data.get("transaction_ids", [])
            )

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                trade_details = get_trade_card(transaction_id)

                trade_details["type"] = "trade"
                filtered_transactions.append(deepcopy(trade_details))

            # Adds
            adds_data = weekly_transactions.get("adds", {})
            transaction_ids = deepcopy(
                adds_data.get("transaction_ids", [])
            )

            transaction_ids.reverse()
            for transaction_id in transaction_ids:

                # Only include adds portion of a
                #   transaction for "add" filter
                add_details = get_transaction_from_ids_cache(transaction_id)
                if add_details and "add" in add_details.get("types", []):

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "add",
                        "player": get_image_url(
                            add_details.get("add", ""),
                            dictionary=True
                        ),

                        # None if FAAB not implemented yet
                        #   or a free agent add
                        "faab_spent": add_details.get(
                            "faab_spent", None
                        ),

                        "transaction_id": transaction_id
                    }
                    filtered_transactions.append(deepcopy(transaction_item))

            # Drops
            drops_data = weekly_transactions.get("drops", {})
            transaction_ids = deepcopy(
                drops_data.get("transaction_ids", [])
            )

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                drop_details = get_transaction_from_ids_cache(transaction_id)
                if drop_details and "drop" in drop_details.get("types", []):

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "drop",
                        "player": get_image_url(
                            drop_details.get("drop", ""),
                            dictionary=True
                        ),

                        "transaction_id": transaction_id
                    }
                    filtered_transactions.append(deepcopy(transaction_item))

            # Adds and Drops
            adds_data = weekly_transactions.get("adds", {})
            transaction_ids = deepcopy(
                adds_data.get("transaction_ids", [])
            )

            transaction_ids.reverse()
            for transaction_id in transaction_ids:
                add_drop_details = get_transaction_from_ids_cache(
                    transaction_id
                )

                # Only include add_and_drop transactions
                types = add_drop_details.get("types", [])
                if types and "add" in types and "drop" in types:

                    transaction_item = {
                        "year": yr,
                        "week": week,
                        "type": "add_and_drop",
                        "added_player": get_image_url(
                            add_drop_details.get("add", ""),
                            dictionary=True
                        ),

                        "dropped_player": get_image_url(
                            add_drop_details.get("drop", ""),
                            dictionary=True
                        ),

                        # None if FAAB not implemented yet
                        # or a free agent add/drop
                        "faab_spent": (
                            add_drop_details.get("faab_spent", None)
                        ),

                        "transaction_id": transaction_id
                    }
                    filtered_transactions.append(
                        deepcopy(transaction_item)
                    )

    # Set total count
    transaction_history["total_count"] = len(filtered_transactions)

    filtered_transactions.reverse()

    # Set transactions in output
    transaction_history["transactions"] = deepcopy(filtered_transactions)

    return deepcopy(transaction_history)
