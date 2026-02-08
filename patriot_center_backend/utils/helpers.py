"""Helper functions for the Patriot Center backend."""

from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


def get_user_id(manager_name: str) -> str | None:
    """Retrieve the user ID for a given manager name from the manager cache.

    Args:
        manager_name: The name of the manager.

    Returns:
        The user ID if found, otherwise None.
    """
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    return manager_cache.get(manager_name, {}).get("summary", {}).get("user_id")


def fetch_manager_scores(year: int, week: int) -> dict[str, dict[str, Any]]:
    """Fetch the starters for each position for a given week.

    Args:
        year (int): The NFL season year (e.g., 2024).
        week (int): The week number (1-17).

    Returns:
        A dictionary where keys are positions and values are dictionaries
        containing the total points and scores for each manager in list form.
    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()
    managers = valid_options_cache[str(year)][str(week)]["managers"]
    positions = valid_options_cache[str(year)][str(week)]["positions"]

    starters_cache = CACHE_MANAGER.get_starters_cache()
    weekly_starters = starters_cache[str(year)][str(week)]

    # Initialize scores with empty values from valid options
    scores = {}
    for position in positions:
        scores[position] = {
            "players": [],
            "scores": [],
            "managers": {
                manager: {"total_points": 0, "scores": []}
                for manager in managers
            },
        }

    for manager in managers:
        for position in positions:
            scores[position]["managers"][manager]["total_points"] = (
                weekly_starters[manager]["Total_Points"]
            )

        for player_id in weekly_starters[manager]:
            if player_id == "Total_Points":
                continue
            position = weekly_starters[manager][player_id]["position"]
            scores[position]["scores"].append(
                weekly_starters[manager][player_id]["points"]
            )
            scores[position]["managers"][manager]["scores"].append(
                weekly_starters[manager][player_id]["points"]
            )

    return scores
