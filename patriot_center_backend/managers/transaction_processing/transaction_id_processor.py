"""Process transaction IDs for deduplication and reversal detection."""

from patriot_center_backend.cache import CACHE_MANAGER


def add_to_transaction_ids(
    year: str,
    week: str,
    transaction_info: dict,
    weekly_transaction_ids: list[str],
    commish_action: bool,
    use_faab: bool
) -> None:
    """Add transaction to global transaction IDs cache.

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
        year: year of the transaciton
        week: week of the transaction
        transaction_info: Dict with transaction details (type, manager, etc.)
        weekly_transaction_ids: list of transaciton ids that have been added
            to the cache
        commish_action: Whether this is a commissioner action
        use_faab: Whether faab was used that season

    Raises:
        ValueError: If required fields missing from transaction_info
    """
    transaction_type = transaction_info.get("type")
    if not transaction_type:
        raise ValueError(
            f"Transaction type not found in "
            f"transaction_info: {transaction_info}"
        )

    transaction_id = transaction_info.get("transaction_id")
    if not transaction_id:
        raise ValueError(
            f"Transaction transaction_id not found in "
            f"transaction_info: {transaction_info}"
        )

    manager = transaction_info.get("manager")
    if not manager:
        raise ValueError(
            f"Transaction manager not found in "
            f"transaction_info: {transaction_info}"
        )

    valid_add_or_drop_types = ["add", "drop", "commissioner"]
    if transaction_type == "add_or_drop":
        transaction_type = transaction_info.get("free_agent_type")
        if (
            not transaction_type
            or transaction_type not in valid_add_or_drop_types
        ):
            raise ValueError(
                f"Transaction type {transaction_info.get('type') } "
                f"is not a valid 'add_or_drop' type, needs to be one "
                f"of: {valid_add_or_drop_types}"
            )

    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

    # If transaction not in cache, make a new object
    if transaction_id not in transaction_ids_cache:
        transaction_ids_cache[transaction_id] = {
            "year": year,
            "week": week,
            "commish_action": commish_action,
            "managers_involved": [],
            "types": [],
            "players_involved": []
        }
    transaction_info_to_cache = transaction_ids_cache[transaction_id]

    if manager not in transaction_info_to_cache["managers_involved"]:
        transaction_info_to_cache["managers_involved"].append(manager)
    if transaction_type not in transaction_info_to_cache["types"]:
        transaction_info_to_cache["types"].append(transaction_type)

    # Add/Drop transactions
    if transaction_type in valid_add_or_drop_types:
        player_name = transaction_info.get("player_name")
        if not player_name:
            raise ValueError(
                f"player_name not found for "
                f"{transaction_type} with info: {transaction_info}"
            )

        transaction_info_to_cache["players_involved"].append(
            player_name
        )

        if transaction_type in transaction_info_to_cache:
            raise ValueError(
                "Can only add or drop one player per transaction."
            )

        transaction_info_to_cache[transaction_type] = player_name
        bid = transaction_info.get("waiver_bid")
        if transaction_type == "add" and use_faab and bid:
            transaction_info_to_cache["faab_spent"] = bid

    # Trade transaction
    elif transaction_type == "trade":

        # Get players acquired and players sent
        players_acquired = transaction_info.get("acquired", {})
        players_sent = transaction_info.get("sent", {})

        # Initialize trade details if not already in cache
        if not transaction_info_to_cache.get("trade_details"):
            transaction_info_to_cache["trade_details"] = {}

        # Add all managers involved if not already in list
        for partner in transaction_info.get("trade_partners", []):
            managers_involved = transaction_info_to_cache["managers_involved"]
            if partner and partner not in managers_involved:
                managers_involved.append(partner)

        # Adding player from players_acquired into players_involved and into
        # the trade details if not already in cache
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

        # Adding player from players_sent into players_involved and into
        # the trade details if not already in cache
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

    if transaction_id not in weekly_transaction_ids:
        weekly_transaction_ids.append(transaction_id)
