"""Data formatting and presentation helpers."""

import logging
from copy import deepcopy
from typing import Any

from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.helpers import get_user_id

logger = logging.getLogger(__name__)


def _get_top_three_and_lowest_scorers(
    year: str, week: str, starters: list[Player]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract top 3 and lowest scorers from matchup data for both managers.

    Uses insertion sort to maintain top 3 scorers while tracking the
    lowest scorer. Modifies matchup_data in-place to add scorer data.

    Args:
        year: Year of the matchup.
        week: Week of the matchup.
        starters: List of starters.

    Returns:
        Tuple containing top 3 scorers and lowest scorer.
    """
    # Initialize with high value to find minimum
    lowest_scorer = {"score": 10000.0}
    # Iterate over starters
    top_scorers = []

    for player in starters:
        player_score = player.get_points(year=year, week=week)

        player_dict = player.get_metadata()
        player_dict["score"] = player_score

        # Update lowest scorer
        if player_score < lowest_scorer["score"]:
            lowest_scorer = deepcopy(player_dict)

        # Maintain sorted top 3 list using insertion sort
        if len(top_scorers) == 0:
            top_scorers.append(player_dict)
        else:
            inserted = False
            # Find correct position in sorted list (highest to lowest)
            for i in range(0, len(top_scorers)):
                if player_score > top_scorers[i]["score"]:
                    top_scorers.insert(i, player_dict)
                    # Keep only top 3
                    if len(top_scorers) > 3:
                        top_scorers.pop()
                    inserted = True
                    break

            # If not inserted and we have fewer than 3, append to end
            if not inserted and len(top_scorers) < 3:
                top_scorers.append(player_dict)

    return top_scorers, lowest_scorer


def get_matchup_card(
    manager_1: Manager, manager_2: Manager, year: str, week: str
) -> dict[str, Any]:
    """Generate complete matchup card with scores, winner, and top performers.

    Creates a formatted matchup summary including both managers' scores,
    the winner determination, and top 3/lowest scorers for each team.

    Args:
        manager_1: First manager
        manager_2: Second manager
        year: Season year as string
        week: Week number as string

    Returns:
        Dictionary containing matchup details, scores, winner, and top
            performers. Empty dict if matchup data incomplete
    """
    manager_1_matchup_data = manager_1.get_matchup_data(
        year=year, week=week
    )
    manager_2_matchup_data = manager_2.get_matchup_data(
        year=year, week=week
    )

    manager_1_score = manager_1_matchup_data.get("points_for")
    manager_2_score = manager_2_matchup_data.get("points_for")

    if not manager_1_score or not manager_2_score:
        logger.warning(
            f"Incomplete matchup data for {manager_1.real_name} vs "
            f"{manager_2.real_name} in year {year}, week {week}."
        )
        return {}

    # Determine winner based on point differential
    if manager_1_score > manager_2_score:
        winner = manager_1
    elif manager_2_score > manager_1_score:
        winner = manager_2
    else:
        winner = "Tie"

    manager_1_top_3_scorers, manager_1_lowest_scorer = (
        _get_top_three_and_lowest_scorers(
            year, week, manager_1_matchup_data["starters"]
        )
    )
    manager_2_top_3_scorers, manager_2_lowest_scorer = (
        _get_top_three_and_lowest_scorers(
            year, week, manager_2_matchup_data["starters"]
        )
    )

    matchup = {
        "year": year,
        "week": week,
        "manager_1": manager_1.get_metadata(),
        "manager_2": manager_2.get_metadata(),
        "manager_1_score": manager_1_score,
        "manager_2_score": manager_2_score,
        "winner": winner,
        "manager_1_top_3_scorers": manager_1_top_3_scorers,
        "manager_1_lowest_scorer": manager_1_lowest_scorer,
        "manager_2_top_3_scorers": manager_2_top_3_scorers,
        "manager_2_lowest_scorer": manager_2_lowest_scorer,
    }

    return matchup


def extract_dict_data(
    data: dict[str, Any],
    item_type: type[Player] | type[Manager],
    key_name: str = "name",
    value_name: str = "count",
    cutoff: int = 3,
) -> list[dict[str, Any]]:
    """Extract top N items from a dictionary and format with image URLs.

    Handles tie-breaking logic to include all items tied for the cutoff
    position.
    - For example, if cutoff=3 and items 3-5 are tied, all will be included.

    Args:
        data: Raw data dictionary (may contain nested dicts with "total" keys)
        item_type: Type of item to extract (Player or Manager)
        key_name: Name of the key field in output (default: "name")
        value_name: Name of the value field in output (default: "count")
        cutoff: Number of top items to include (0 means all items)

    Returns:
        List of dictionaries with key_name, value_name, and image_url fields
    """
    # Flatten nested dictionaries by extracting "total" values
    for key in data:
        if not isinstance(data[key], dict):
            break
        data[key] = data[key]["total"]

    # Sort items by value in descending order
    sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)

    # If no cutoff, include all items
    if not cutoff:
        top_three = dict(sorted_items)
    else:
        # Handle ties at the cutoff position
        # Start at cutoff position (e.g., index 2 for top 3)
        i = min(cutoff - 1, len(sorted_items) - 1)
        # Extend cutoff to include all tied items
        for j in range(i, len(sorted_items) - 1):
            if sorted_items[j][1] != sorted_items[j + 1][1]:
                i = j
                break
            i = j + 1
        top_three = dict(sorted_items[: i + 1])

    # Build formatted output list with image URLs
    items = []
    for item in top_three:
        long_dict = {}
        long_dict[key_name] = item
        long_dict[value_name] = top_three[item]

        if item_type == Manager:
            user_id = get_user_id(item)
            if not user_id:
                raise ValueError(f"Manager {item} not found in cache.")
            long_dict["metadata"] = Manager(user_id).get_metadata()

        elif item_type == Player:
            long_dict["metadata"] = Player(item).get_metadata()

        items.append(deepcopy(long_dict))

    return deepcopy(items)
