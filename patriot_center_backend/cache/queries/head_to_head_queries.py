"""Cache query helpers for reading head to head related manager metadata."""

import logging
from typing import Any

from patriot_center_backend.models import Manager, Transaction
from patriot_center_backend.models.transaction import TransactionType
from patriot_center_backend.utils.formatters import get_matchup_card

logger = logging.getLogger(__name__)


def get_head_to_head_details_for_opponent(
    manager: Manager, opponent: Manager, year: str | None = None
) -> dict[str, Any]:
    """Get head-to-head record(s) for a manager against opponent(s).

    Args:
        manager: Manager name
        opponent: Specific opponent
        year: Season year (optional - defaults to all-time if None)

    Returns:
        Single opponent dict.
    """
    details: dict[str, Any] = manager.get_matchup_data_summary(
        year=year, opponent=opponent
    )
    if details:
        trades = Transaction.get_transactions(
            year=year,
            transaction_type=TransactionType.TRADE,
            managers_involved=[manager, opponent],
        )

        details["num_trades_between"] = len(trades)
        details["opponent"] = opponent.get_metadata()
        return details
    else:
        return {}


def get_head_to_head_details_for_opponents(
    manager: Manager, year: str | None = None
) -> list[dict[str, Any]]:
    """Get head-to-head record(s) for a manager against opponent(s).

    Args:
        manager: Manager name
        year: Season year (optional - defaults to all-time if None)

    Returns:
        All opponent dicts.
    """
    opponents = manager.get_opponents(year=year)
    matchup_data = []
    for opponent in opponents:
        matchup_data.append(
            get_head_to_head_details_for_opponent(manager, opponent, year=year)
        )
    return matchup_data


def list_matchups_between_two_managers(
    manager: Manager, opponent: Manager, year: str | None = None
) -> list[dict[str, Any]]:
    """Get all matchup data between two managers.

    Args:
        manager: Manager name
        opponent: Specific opponent
        year: Season year (optional - defaults to all-time if None)

    Returns:
        List of matchup cards between the two managers.
    """
    matchups = manager.get_matching_matchup_data(year=year, opponent=opponent)

    matchup_cards = []
    for matchup in matchups:
        get_matchup_card(manager, opponent, matchup["year"], matchup["week"])

    return matchup_cards


def get_head_to_head_overall(
    manager1: Manager,
    manager2: Manager,
    year: str | None = None,
) -> dict[str, Any]:
    """Get comprehensive head-to-head analysis between two managers.

    Iterates through all matchups to find:
    - Overall win/loss/tie record
    - Average margin of victory for each manager
    - Last win for each manager (most recent)
    - Biggest blowout for each manager

    Args:
        manager1: First manager name
        manager2: Second manager name
        year: Season year (optional - defaults to all-time)

    Returns:
        dictionary with all head-to-head data, including overall data,
            and matchup data.
    """
    ret_dict = {
        str(manager1): manager1.get_matchup_data_summary(
            year=year, opponent=manager2
        ),
        str(manager2): manager2.get_matchup_data_summary(
            year=year, opponent=manager1
        ),
    }
    del ret_dict[str(manager1)]["opponent"]
    del ret_dict[str(manager2)]["opponent"]

    manager_1_wins = manager1.get_matching_matchup_data(
        year=year, result="win", opponent=manager2
    )
    manager_2_wins = manager2.get_matching_matchup_data(
        year=year, result="win", opponent=manager1
    )

    if not manager_1_wins:
        ret_dict[str(manager1)]["last_win"] = None
        ret_dict[str(manager1)]["biggest_blowout"] = None
    else:
        ret_dict[str(manager1)]["last_win"] = get_matchup_card(
            manager1,
            manager2,
            manager_1_wins[-1]["year"],
            manager_1_wins[-1]["week"],
        )
        manager_1_biggest_blowout = _get_biggest_blowout(manager_1_wins)
        ret_dict[str(manager1)]["biggest_blowout"] = get_matchup_card(
            manager1,
            manager2,
            manager_1_biggest_blowout["year"],
            manager_1_biggest_blowout["week"],
        )
    if not manager_2_wins:
        ret_dict[str(manager2)]["last_win"] = None
        ret_dict[str(manager2)]["biggest_blowout"] = None
    else:
        ret_dict[str(manager2)]["last_win"] = get_matchup_card(
            manager2,
            manager1,
            manager_2_wins[-1]["year"],
            manager_2_wins[-1]["week"],
        )
        manager_2_biggest_blowout = _get_biggest_blowout(manager_2_wins)
        ret_dict[str(manager2)]["biggest_blowout"] = get_matchup_card(
            manager2,
            manager1,
            manager_2_biggest_blowout["year"],
            manager_2_biggest_blowout["week"],
        )
    return ret_dict


def _get_biggest_blowout(matchup_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Get the biggest blowout for a manager.

    Args:
        matchup_data: Matchup data.

    Returns:
        Matchup data with biggest blowout.
    """
    if not matchup_data:
        return {}

    return max(
        matchup_data, key=lambda x: x["points_for"] - x["points_against"]
    )
