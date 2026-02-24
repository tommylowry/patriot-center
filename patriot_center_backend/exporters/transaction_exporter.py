"""Transaction exporter for manager metadata."""

from typing import Any

from patriot_center_backend.constants import TOMMY_USER_ID

from patriot_center_backend.models import Manager, Transaction
from patriot_center_backend.models.transaction import TransactionType


def get_manager_transactions(
    manager: Manager, year: str | None = None
) -> dict[str, Any]:
    """Get manager transaction history.

    Args:
        manager: The manager object.
        year: Optional year to filter transactions.

    Returns:
        dictionary with manager transaction history.
    """
    transaction_objs: list[Transaction] = Transaction.get_transactions(
        year=year, manager_involved=manager
    )
    transaction_history: dict[str, Any] = {
        "metadata": manager.get_metadata(),
        "total_count": len(transaction_objs),
    }

    transactions: list[dict[str, Any]] = []
    for transaction in transaction_objs:
        if transaction.transaction_types == {TransactionType.TRADE}:
            transactions.append(transaction.to_dict())
            continue

        transaction_item = {
            "year": transaction.year,
            "week": transaction.week,
        }
        if transaction.transaction_types == {TransactionType.DROP}:
            transaction_item["type"] = "drop"
            transaction_item["player"] = next(  # Only one player in set
                iter(transaction.lost[manager])
            ).get_metadata()
            transactions.append(transaction_item)
            continue

        if transaction.transaction_types == {TransactionType.ADD}:
            transaction_item["type"] = "add"
            transaction_item["player"] = next(
                iter(transaction.gained[manager])
            ).get_metadata()
            transaction_item["faab_spent"] = transaction.faab_spent
            transactions.append(transaction_item)
            continue

        # Only other possibility is add 
        transaction_item["type"] = "add_and_drop"
        transaction_item["added_player"] = next(
            iter(transaction.gained[manager])
        ).get_metadata()
        transaction_item["dropped_player"] = next(
            iter(transaction.lost[manager])
        ).get_metadata()
        transaction_item["faab_spent"] = transaction.faab_spent
        transactions.append(transaction_item)

    transaction_history["transactions"] = transactions
    return transaction_history


if __name__ == "__main__":
    d = get_manager_transactions(Manager(TOMMY_USER_ID))
    print("")