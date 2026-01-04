"""
Validation functions for manager metadata processing.

Validates preconditions, matchup data, and transaction data.
"""
from typing import Dict, Optional


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_caching_preconditions(weekly_roster_ids: Dict[int, str],
                                  year: Optional[str],
                                  week: Optional[str]) -> None:
    """
    Validate that caching preconditions are met before processing week data.

    Ensures that:
    - At least one roster ID has been set
    - Even number of rosters exist (for matchup pairing)
    - Year and week are specified

    Args:
        weekly_roster_ids: Roster ID to manager mapping
        year: Current year being processed
        week: Current week being processed

    Raises:
        ValidationError: If any precondition is not met
    """
    if len(weekly_roster_ids) == 0:
        # No roster IDs cached yet; nothing to do
        raise ValidationError("No roster IDs cached. Cannot cache week data.")

    if len(weekly_roster_ids) % 2 == 1:
        # Sanity check: matchups require even number of teams
        raise ValidationError("Odd number of roster IDs cached, cannot process matchups.")

    if not year:
        raise ValidationError("Year not set. Cannot cache week data.")
    if not week:
        raise ValidationError("Week not set. Cannot cache week data.")


def validate_matchup_data(matchup_data: dict, cache: dict) -> None:
    """
    Validate matchup data structure and logical consistency.

    Checks that:
    - Opponent manager exists in cache
    - Points are positive values
    - Result matches point differential (win/loss/tie logic)

    Args:
        matchup_data: Matchup data containing opponent, result, and points
        cache: Manager cache for validating opponent existence

    Returns:
        Empty string if valid
        "Empty" if no matchup data (manager didn't play that week)
        Warning string if validation issues found
    """
    # No matchup data means manager didn't play that week (e.g., not in playoffs)
    if not matchup_data:
        return "Empty"

    opponent_manager = matchup_data.get("opponent_manager", "")
    result           = matchup_data.get("result", "")
    points_for       = matchup_data.get("points_for", 0.0)
    points_against   = matchup_data.get("points_against", 0.0)

    # Validate opponent manager
    if opponent_manager == "":
        return "Warning, no opponent_data in matchup_data"
    if opponent_manager not in list(cache.keys()):
        return f"Warning, {opponent_manager} is an invalid manager"

    # Validate points are positive
    if points_for <= 0.0:
        return f"Warning, invalid points_for {points_for} in matchup_data"
    if points_against <= 0.0:
        return f"Warning, invalid points_against {points_against} in matchup_data"

    # Validate result field
    if result == "":
        return "Warning, no result in matchup_data"
    if result not in ["win", "loss", "tie"]:
        return f"Warning, {result} is an invalid result in matchup_data"

    # Validate result matches point differential
    if result == "win" and points_for < points_against:
        return f"Warning, result is win but points_against {points_against} is more than points_for {points_for} in matchup_data"
    if result == "loss" and points_for > points_against:
        return f"Warning, result is loss but points_for {points_for} is more than points_against {points_against} in matchup_data"
    if result == "tie" and points_for != points_against:
        return f"Warning, result is tie but points_for {points_for} is not the same as points_against {points_against} in matchup_data"

    return ""


def validate_transaction(transaction: dict, transaction_type: str, process_transaction_type,
                          weekly_roster_ids: Dict[int, str]) -> bool:
    """
    Validate if transaction should be processed.

    Checks transaction status, type validity, and required fields.
    For trade transactions, validates multi-manager requirements.

    Args:
        transaction: Transaction data from Sleeper API
        transaction_type: Type of transaction ("trade" or "add_or_drop")
        process_transaction_type: Whether this transaction type should be processed
        weekly_roster_ids: Roster ID to manager mapping for the week

    Returns:
        True if transaction should be processed, False if it should be skipped
    """
    # Skip failed transactions
    if transaction.get("status", "") == "failed":
        return False

    # Only process completed transactions
    if transaction.get("status", "") != "complete":
        print("Unexpected transaction status:", transaction)
        return False

    # Validate transaction type
    if transaction_type not in {"trade", "add_or_drop"}:
        print("Unexpected transaction type:", transaction)
        return False

    # Check if processor exists for this type
    if not process_transaction_type:
        print("No processor for transaction type:", transaction)
        return False

    # Additional validation for trade transactions
    if transaction_type == "trade":
        # Trades must have transaction ID
        if "transaction_id" not in transaction:
            print("Invalid trade transaction (missing transaction_id):", transaction)
            return False

        # Trades must involve at least 2 rosters
        if "roster_ids" not in transaction or len(transaction["roster_ids"]) < 2:
            print("Invalid trade transaction (missing roster_ids):", transaction)
            return False

        # Trades must have adds and drops
        if "adds" not in transaction or "drops" not in transaction:
            print("Invalid trade transaction (missing adds/drops):", transaction)
            return False

        # At least one involved roster must be relevant to current caching session
        if not any(roster_id in weekly_roster_ids for roster_id in transaction["roster_ids"]):
            return False

    return True