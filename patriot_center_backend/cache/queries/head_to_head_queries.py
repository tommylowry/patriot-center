"""Cache query helpers for reading head to head related manager metadata."""

import logging
from copy import deepcopy
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import TOMMY_USER_ID, CODY_USER_ID
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
        List of matchup data between the two managers.
    """
    matchups = manager.get_matchup_data(year=year, opponent=opponent)
    for matchup in matchups:
        

def get_head_to_head_overall_from_cache(
    manager1_obj: Manager,
    manager2_obj: Manager,
    year: str | None = None,
    list_all_matchups: bool = False,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Get comprehensive head-to-head analysis between two managers.

    Iterates through all matchups to find:
    - Overall win/loss/tie record
    - Average margin of victory for each manager
    - Last win for each manager (most recent)
    - Biggest blowout for each manager

    Args:
        manager1_obj: First manager object
        manager2_obj: Second manager object
        year: Season year (optional - defaults to all-time if None)
        list_all_matchups: If True, returns list with all
            matchup cards instead of dict with head-to-head data

    Returns:
        - If list_all_matchups=True, List of all matchup cards
        - Otherwise: Dict with record, average margins, last wins,
        and biggest blowouts

    Raises:
        ValueError: If get_head_to_head_details_from_cache fails
            to return expected data type
    """
    # TODO: remove this once managers are stored in cache
    manager1 = manager1_obj.real_name
    manager2 = manager2_obj.real_name
    # END TODO
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    # Only for list_all_matchups = False
    head_to_head_overall = {}

    if list_all_matchups:
        years = list(manager_cache[manager1].get("years", {}).keys())
        if year:
            years = [year]
    else:
        head_to_head_data = get_head_to_head_details_for_opponent(
            manager1_obj, manager2_obj, year=year
        )

        if isinstance(head_to_head_data, list):
            raise ValueError(
                f"Unable to get head-to-head data between {manager1} and "
                f"{manager2} for year {year}, overall data expected as a "
                f"dict but received all data as a list."
            )

        head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_wins"] = (
            head_to_head_data.get("wins")
        )
        head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_wins"] = (
            head_to_head_data.get("losses")
        )
        head_to_head_overall["ties"] = head_to_head_data.get("ties")

        # Get average margin of victory, last win, biggest blowout
        years = list(manager_cache[manager1].get("years", {}).keys())

    # Only for list_all_matchups = True
    matchup_history = []

    # Only for list_all_matchups = False
    manager_1_victory_margins = []
    manager_1_last_win = {}
    manager_1_biggest_blowout = {}

    manager_2_victory_margins = []
    manager_2_last_win = {}
    manager_2_biggest_blowout = {}

    manager_1_points_for = (
        manager_cache[manager1]
        .get("summary", {})
        .get("matchup_data", {})
        .get("overall", {})
        .get("points_for", {})
        .get("opponents", {})
        .get(manager2, 0.0)
    )
    manager_2_points_for = (
        manager_cache[manager2]
        .get("summary", {})
        .get("matchup_data", {})
        .get("overall", {})
        .get("points_for", {})
        .get("opponents", {})
        .get(manager1, 0.0)
    )

    if year:
        years = [year]
        manager_1_points_for = (
            manager_cache[manager1]
            .get("years", {})
            .get(year, {})
            .get("summary", {})
            .get("matchup_data", {})
            .get("overall", {})
            .get("points_for", {})
            .get("opponents", {})
            .get(manager2, 0.0)
        )
        manager_2_points_for = (
            manager_cache[manager2]
            .get("years", {})
            .get(year, {})
            .get("summary", {})
            .get("matchup_data", {})
            .get("overall", {})
            .get("points_for", {})
            .get("opponents", {})
            .get(manager1, 0.0)
        )

    # Get average margin of victory
    for y in years:
        weeks = deepcopy(manager_cache[manager1]["years"][y]["weeks"])

        for w in weeks:
            matchup_data = deepcopy(weeks.get(w, {}).get("matchup_data", {}))

            # Manager didn't play that week but had transactions
            if matchup_data == {}:
                continue

            # Not the matchup we're looking for
            if manager2 != matchup_data.get("opponent_manager", ""):
                continue

            matchup_res = matchup_data.get("result", "")
            if matchup_res not in ["win", "loss", "tie"]:
                logger.warning(
                    f"Missing result for matchup between "
                    f"{manager1} and {manager2} in {y} week {w}"
                )
                continue

            matchup_card = get_matchup_card(manager1_obj, manager2_obj, y, w)

            if list_all_matchups:
                matchup_history.append(matchup_card)
                continue

            manager_1_score = matchup_data.get("points_for")
            manager_2_score = matchup_data.get("points_against")

            # Manager 1 won
            if matchup_res == "win":
                manager_1_last_win, manager_1_biggest_blowout = (
                    _evaluate_matchup(
                        manager_1_biggest_blowout,
                        manager_1_last_win,
                        matchup_card,
                        manager_1_score - manager_2_score,
                        manager_1_victory_margins,
                    )
                )
            else:
                manager_2_last_win, manager_2_biggest_blowout = (
                    _evaluate_matchup(
                        manager_2_biggest_blowout,
                        manager_2_last_win,
                        matchup_card,
                        manager_2_score - manager_1_score,
                        manager_2_victory_margins,
                    )
                )

    if list_all_matchups:
        matchup_history.reverse()
        return matchup_history

    if len(manager_1_victory_margins) == 0:
        logger.warning(
            f"No victories found for {manager1} against "
            f"{manager2}. Cannot compute average margin of victory."
        )
        manager_1_average_margin_of_victory = None
    else:
        avg = sum(manager_1_victory_margins) / len(manager_1_victory_margins)
        manager_1_average_margin_of_victory = float(
            Decimal(avg).quantize(Decimal("0.01"))
        )

    if len(manager_2_victory_margins) == 0:
        logger.warning(
            f"No victories found for {manager2} against {manager1}. "
            f"Cannot compute average margin of victory."
        )
        manager_2_average_margin_of_victory = None
    else:
        avg = sum(manager_2_victory_margins) / len(manager_2_victory_margins)
        manager_2_average_margin_of_victory = float(
            Decimal(avg).quantize(Decimal("0.01"))
        )

    m1 = manager1.lower().replace(" ", "_")
    m2 = manager2.lower().replace(" ", "_")

    # put all the data in
    head_to_head_overall[f"{m1}_points_for"] = manager_1_points_for
    head_to_head_overall[f"{m2}_points_for"] = manager_2_points_for

    head_to_head_overall[f"{m1}_average_margin_of_victory"] = (
        manager_1_average_margin_of_victory
    )
    head_to_head_overall[f"{m2}_average_margin_of_victory"] = (
        manager_2_average_margin_of_victory
    )

    head_to_head_overall[f"{m1}_last_win"] = manager_1_last_win
    head_to_head_overall[f"{m2}_last_win"] = manager_2_last_win

    head_to_head_overall[f"{m1}_biggest_blowout"] = manager_1_biggest_blowout
    head_to_head_overall[f"{m2}_biggest_blowout"] = manager_2_biggest_blowout

    return head_to_head_overall


def _evaluate_matchup(
    biggest_blowout: dict[str, Any],
    last_win: dict[str, Any],
    matchup_card: dict[str, Any],
    victory_margin: float,
    margins: list[float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Evaluate a single matchup card.

    Args:
        biggest_blowout: Matchup card of the biggest blowout
        last_win: Matchup card of the most recent win
        matchup_card: Current matchup card
        victory_margin: Margin of victory
        margins: List of victory margins

    Returns:
        Updated `last_win` and `biggest_blowout`
    """
    margins.append(victory_margin)

    if not last_win:
        last_win = matchup_card

        if not biggest_blowout:
            biggest_blowout = matchup_card
        return last_win, biggest_blowout

    y = int(matchup_card["year"])
    w = int(matchup_card["week"])

    # Determine if this is the most recent win
    if (y, w) > (int(last_win["year"]), int(last_win["week"])):
        last_win = matchup_card

    # Determine if this is the biggest blowout
    if victory_margin == max(margins):
        biggest_blowout = matchup_card

    return last_win, biggest_blowout

if __name__ == "__main__":
    s = get_head_to_head_overall_from_cache(Manager(TOMMY_USER_ID), Manager(CODY_USER_ID), list_all_matchups=True)

    print("")
