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
    
    Args:
        weekly_roster_ids: Roster ID to manager mapping
        year: Current year being processed
        week: Current week being processed
    
    Raises:
        ValidationError: If preconditions not met
    """
    if len(weekly_roster_ids) == 0:
        # No roster IDs cached yet; nothing to do
        raise ValidationError("No roster IDs cached. Cannot cache week data.")
    
    if len(weekly_roster_ids) % 2 == 1:
        # Sanity check: expect even number of rosters for matchups
        raise ValidationError("Odd number of roster IDs cached, cannot process matchups.")
    
    if not year:
        raise ValidationError("Year not set. Cannot cache week data.")
    if not week:
        raise ValidationError("Week not set. Cannot cache week data.")


def validate_matchup_data(matchup_data: dict, cache: dict) -> None:
    """
    Validate matchup data structure.
    
    Args:
        matchup_data: Matchup data from API
        cache: Manager cache for lookup
    
    Returns:
        "" if valid, Warning if there is a warning and "Empty" if no matchup
        
    """
    if not matchup_data: # No data, Manager didn't play that week
        return "Empty"
        
    opponent_manager = matchup_data.get("opponent_manager", "")
    result           = matchup_data.get("result", "")
    points_for       = matchup_data.get("points_for", 0.0)
    points_against   = matchup_data.get("points_against", 0.0)
    
    if opponent_manager == "":
        return "Warning, no opponent_data in matchup_data"
    if opponent_manager not in list(cache.keys()):
        return f"Warning, {opponent_manager} is an invalid manager"
    
    if points_for <= 0.0:
        return f"Warning, invalid points_for {points_for} in matchup_data"
    if points_against <= 0.0:
        return f"Warning, invalid points_against {points_against} in matchup_data"

    if result == "":
        return "Warning, no result in matchup_data"
    if result not in ["win", "loss", "tie"]:
        return f"Warning, {result} is an invalid result in matchup_data"
    
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
    
    Args:
        transaction: Transaction data from API
        weekly_roster_ids: Roster ID to manager mapping
    
    Returns:
        True if transaction is valid, False otherwise
    """
    if transaction.get("status", "") == "failed":
        return False
    
    if transaction.get("status", "") != "complete":
        print("Unexpected transaction status:", transaction)
        return False
    
    

    # Validate transaction type
    if transaction_type not in {"trade", "add_or_drop"}:
        print("Unexpected transaction type:", transaction)
        return False
    
    if not process_transaction_type:
        print("No processor for transaction type:", transaction)
        return False
    
    if transaction_type == "trade":
        # Validate trade transaction specifics

        if "transaction_id" not in transaction:
            print("Invalid trade transaction (missing transaction_id):", transaction)
            return False

        if "roster_ids" not in transaction or len(transaction["roster_ids"]) < 2:
            print("Invalid trade transaction (missing roster_ids):", transaction)
            return False
        
        if "adds" not in transaction or "drops" not in transaction:
            print("Invalid trade transaction (missing adds/drops):", transaction)
            return False
        
        if not any(roster_id in weekly_roster_ids for roster_id in transaction["roster_ids"]):
            # No involved roster IDs are relevant to this caching session
            return False
    
    return True