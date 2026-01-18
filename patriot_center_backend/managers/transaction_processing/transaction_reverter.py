"""Process reversed transactions (joke trades or accidental transactions)."""

from copy import deepcopy

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.transaction_processing.add_drop_processor import (  # noqa: E501
    revert_add_drop_transaction,
)
from patriot_center_backend.managers.transaction_processing.trade_processor import (  # noqa: E501
    revert_trade_transaction,
)


def check_for_reverse_transactions(transaction_ids: list[str]) -> None:
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
        transaction_ids: List of transaction ids to evaluate.
            NOTE: This list will be empty after this method is called.
    """
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

    while len(transaction_ids) > 1:
        transaction_ids = deepcopy(transaction_ids)

        transaction_id1 = transaction_ids.pop()
        transaction1 = transaction_ids_cache[transaction_id1]

        for transaction_id2 in transaction_ids:
            transaction2 = transaction_ids_cache[transaction_id2]

            # Skip if different managers involved
            if (
                sorted(transaction1['managers_involved'])
                != sorted(transaction2['managers_involved'])
            ):
                continue

            # Check for commissioner add/drop reversals
            # If commissioner adds/drops a player, then opposite action occurs,
            # this was likely an accident - revert both transactions
            if transaction1["commish_action"]:

                if (
                    transaction1.get("add")
                    and transaction1["add"] == transaction2.get("drop")
                ):
                    trans_1_removed = revert_add_drop_transaction(
                        transaction_id1, "add", transaction_ids
                    )
                    trans_2_removed = revert_add_drop_transaction(
                        transaction_id2, "drop", transaction_ids
                    )

                    # no more transaction 1, so move on
                    # to another transaction to evaluate
                    if trans_1_removed:
                        break

                    # no more transaction 2, so move on
                    # to the next transaction for transaction 1 to evaluate
                    if trans_2_removed:
                        continue

                if (
                    transaction1.get("drop")
                    and transaction1["drop"] == transaction2.get("add")
                ):
                    trans_1_removed = revert_add_drop_transaction(
                        transaction_id1, "drop", transaction_ids
                    )
                    trans_2_removed = revert_add_drop_transaction(
                        transaction_id2, "add", transaction_ids
                    )

                    if trans_1_removed:
                        break
                    if trans_2_removed:
                        continue

            if transaction2["commish_action"]:
                if (
                    transaction2.get("add")
                    and transaction2["add"] == transaction1.get("drop")
                ):
                    trans_1_removed = revert_add_drop_transaction(
                        transaction_id1, "drop", transaction_ids
                    )
                    trans_2_removed = revert_add_drop_transaction(
                        transaction_id2, "add", transaction_ids
                    )

                    if trans_1_removed:
                        break
                    if trans_2_removed:
                        continue

                if (
                    transaction2.get("drop")
                    and transaction2["drop"] == transaction1.get("add")
                ):
                    trans_1_removed = revert_add_drop_transaction(
                        transaction_id1, "add", transaction_ids
                    )
                    trans_2_removed = revert_add_drop_transaction(
                        transaction_id2, "drop", transaction_ids
                    )

                    if trans_1_removed:
                        break
                    if trans_2_removed:
                        continue

            # Check for trade reversals (joke trades or immediate regret)
            # Both must be trades with same players, but opposite directions
            if (
                "trade" not in transaction1["types"]
                or "trade" not in transaction2["types"]
            ):
                continue

            if (
                sorted(transaction1['players_involved'])
                != sorted(transaction2['players_involved'])
            ):
                continue

            # If same players and trade details match
            # (opposite directions), it's a reversal
            if (
                sorted(transaction1['trade_details'].keys())
                == sorted(transaction2['trade_details'].keys())
            ):

                invalid_transaction = True
                for plyr in transaction1['trade_details']:
                    t1_old = transaction1['trade_details'][plyr]['old_manager']
                    t1_new = transaction1['trade_details'][plyr]['new_manager']
                    t2_old = transaction2['trade_details'][plyr]['old_manager']
                    t2_new = transaction2['trade_details'][plyr]['new_manager']

                    if t1_old != t2_new or t1_new != t2_old:
                        invalid_transaction = False
                        break

                if not invalid_transaction:
                    continue

            # continue wasnt called so the trade is invalid, remove it
            revert_trade_transaction(
                transaction_id1, transaction_id2, transaction_ids
            )
            break

        if transaction_id1 in transaction_ids:
            transaction_ids.remove(transaction_id1)
