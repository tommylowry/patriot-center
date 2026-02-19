"""Process transactions for a given week."""

import logging

from patriot_center_backend.models import Transaction
from patriot_center_backend.models.transaction import TransactionType
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_transactions,
)

logger = logging.getLogger(__name__)


def update_transactions(year: int, week: int) -> None:
    """Process all transactions for a given week.

    Args:
        year: The year for which to process transactions.
        week: The week for which to process transactions.
    """
    transactions = fetch_transactions(year, week)

    weekly_transactions = []
    for raw_transaction in transactions:
        if "transaction_id" not in raw_transaction:
            logger.warning(
                f"Transaction {raw_transaction} missing transaction_id"
            )
            continue

        transaction_id = raw_transaction["transaction_id"]

        transaction = Transaction(transaction_id)
        if transaction.apply_transaction(str(year), str(week), raw_transaction):
            weekly_transactions.append(transaction)

    _check_for_reverse_transactions(weekly_transactions)


def _check_for_reverse_transactions(transactions: list[Transaction]) -> None:
    """Detect and revert transactions (joke trades or accidental transactions).

    Compares all weekly transactions to find pairs that undo each other:
    - Same managers involved
    - Same players involved
    - Opposite directions (player moved from A→B then B→A)

    Reverted transactions are removed from cache.

    Handles two cases:
    1. Commissioner add/drop reversals (accident correction)
    2. Trade reversals (joke trades or mistakes)

    Args:
        transactions: List of transactions to evaluate.
    """
    while len(transactions) > 1:
        transaction_a = transactions.pop()

        for transaction_b in transactions:
            is_reversal = (
                transaction_a.gained == transaction_b.lost
                or transaction_a.lost == transaction_b.gained
            )
            is_commish = (
                transaction_a.commish_action or transaction_b.commish_action
            )
            is_trade_pair = (
                TransactionType.TRADE in transaction_a.transaction_types
                and TransactionType.TRADE in transaction_b.transaction_types
            )

            if is_reversal and (is_commish or is_trade_pair):
                transaction_a.delete()
                transaction_b.delete()
                transactions.remove(transaction_b)
                break
