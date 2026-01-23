"""Data formatting and presentation helpers."""

import logging
from copy import deepcopy
from typing import Any, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.image_url_updater import (
    get_image_url,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


def get_season_state(
    week: str, year: str, playoff_week_start: int | None = None
) -> Literal["regular_season", "playoffs"]:
    """Determine the current state of the season (regular season or playoffs).

    Args:
        week: Current week number as string
        year: Current year as string
        playoff_week_start: Week when playoffs start
            (fetched from API if not provided)

    Returns:
        "regular_season" or "playoffs"

    Raises:
        ValueError: If week or year not provided
            or if Sleeper API call fails to retrieve what is expected
    """
    if not week or not year:
        raise ValueError("Week or Year not set. Cannot determine season state.")

    # Fetch playoff week start from league settings if not provided
    if not playoff_week_start:
        league_info = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")

        if not isinstance(league_info, dict):
            raise ValueError(
                f"Sleeper API call failed to retrieve "
                f"league info for year {year}"
            )

        playoff_week_start = (
            league_info.get("settings", {}).get("playoff_week_start")
        )

        if not playoff_week_start:
            raise ValueError(
                f"Sleeper API call failed to retrieve "
                f"playoff_week_start for year {year}"
            )

    if int(week) >= playoff_week_start:
        return "playoffs"
    return "regular_season"


def get_top_3_scorers_from_matchup_data(
    matchup_data: dict[str, Any],
    manager_1: str,
    manager_2: str,
) -> None:
    """Extract top 3 and lowest scorers from matchup data for both managers.

    Uses insertion sort to maintain top 3 scorers while tracking the
    lowest scorer. Modifies matchup_data in-place to add scorer data.

    Args:
        matchup_data: Matchup data dictionary (modified in-place)
        manager_1: First manager name
        manager_2: Second manager name

    Raises:
        ValueError: If get_image_url fails to retrieve output in dict form
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    players_cache = CACHE_MANAGER.get_players_cache()
    starters_cache = CACHE_MANAGER.get_starters_cache()

    matchup_data["manager_1_top_3_scorers"] = []
    matchup_data["manager_2_top_3_scorers"] = []
    matchup_data["manager_1_lowest_scorer"] = []
    matchup_data["manager_2_lowest_scorer"] = []

    week = matchup_data.get("week")
    year = matchup_data.get("year")

    # Validate that year and week are present
    if not year or not week:
        logger.warning(
            "matchup_data missing year or week. Cannot get top 3 scorers."
        )
        return

    # Validate that starter data exists for both managers
    year_data = starters_cache.get(year, {})
    week_data = year_data.get(week, {})
    if manager_1 not in week_data or manager_2 not in week_data:
        logger.warning(
            f"WARNING: Starter data missing for week {week}, year {year}. "
            f"Cannot get top 3 scorers for {manager_1} vs {manager_2}."
        )
        return

    var_map = {manager_1: "manager_1", manager_2: "manager_2"}
    for manager in [manager_1, manager_2]:
        manager_starters = deepcopy(week_data[manager])
        # Remove total points aggregate, we only want individual players
        if "Total_Points" in manager_starters:
            manager_starters.pop("Total_Points")

        # Initialize with high value to find minimum
        lowest_scorer = {"score": 10000.0}

        # Iterate over starters
        top_scorers = []
        for player in manager_starters:
            player_dict = get_image_url(player, dictionary=True)

            if not isinstance(player_dict, dict):
                raise ValueError(
                    f"Dict expected from get_image_url for player {player}, "
                    f"dictionary was set to True, but got {type(player_dict)}"
                )

            player_id = players_cache[player]["player_id"]
            if not player_id:
                logger.warning(
                    f"WARNING: Player ID missing for player {player}. "
                    f"Cannot get top 3 scorers for {manager_1} vs {manager_2}."
                )
                return

            first_name = player_ids_cache[player_id]["first_name"]
            last_name = player_ids_cache[player_id]["last_name"]

            player_dict.update(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "score": manager_starters[player]["points"],
                    "position": manager_starters[player]["position"],
                }
            )

            player_score = player_dict.get("score")

            # Track lowest scorer
            if not isinstance(player_score, float):
                logger.warning(
                    f"Player score not float for player {player}. "
                    f"For {year}, week {week}."
                )
                continue

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

            matchup_data[f"{var_map[manager]}_top_3_scorers"] = top_scorers
            matchup_data[f"{var_map[manager]}_lowest_scorer"] = lowest_scorer


def get_matchup_card(
    manager_1: str,
    manager_2: str,
    year: str,
    week: str,
) -> dict[str, Any]:
    """Generate complete matchup card with scores, winner, and top performers.

    Creates a formatted matchup summary including both managers' scores,
    the winner determination, and top 3/lowest scorers for each team.

    Args:
        manager_1: First manager name
        manager_2: Second manager name
        year: Season year as string
        week: Week number as string

    Returns:
        Dictionary containing matchup details, scores, winner, and top
            performers. Empty dict if matchup data incomplete
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    years_level = manager_cache.get(manager_1, {}).get("years", {})
    weeks_level = years_level.get(year, {}).get("weeks", {})
    matchup_data = weeks_level.get(week, {}).get("matchup_data", {})

    manager_1_score = matchup_data.get("points_for")
    manager_2_score = matchup_data.get("points_against")

    if not manager_1_score or not manager_2_score:
        logger.warning(
            f"Incomplete matchup data for {manager_1} vs "
            f"{manager_2} in year {year}, week {week}."
        )
        return {}

    # Determine winner based on point differential
    if manager_1_score > manager_2_score:
        winner = manager_1
    elif manager_2_score > manager_1_score:
        winner = manager_2
    else:
        winner = "Tie"

    matchup = {
        "year": year,
        "week": week,
        "manager_1": {
            "name": manager_1,
            "image_url": get_image_url(manager_1),
        },
        "manager_2": {
            "name": manager_2,
            "image_url": get_image_url(manager_2),
        },
        "manager_1_score": manager_1_score,
        "manager_2_score": manager_2_score,
        "winner": winner,
    }

    get_top_3_scorers_from_matchup_data(
        matchup, manager_1, manager_2
    )

    return deepcopy(matchup)


def get_trade_card(transaction_id: str) -> dict[str, Any]:
    """Generate formatted trade card showing all players/assets exchanged.

    Creates a structured trade summary with managers involved and
    items sent/received by each party. Handles multi-party trades.

    Args:
        transaction_id: Transaction ID to look up

    Returns:
        Trade card dictionary with year, week, managers, and items exchanged
    """
    transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

    trans = transaction_ids_cache.get(transaction_id)
    if not trans:
        logger.warning(
            f"Transaction {transaction_id} not found in trade cache."
        )
        return {}

    year = trans.get("year")
    week = trans.get("week")
    if not year or not week:
        logger.warning(
            f"Missing year or week for transaction {transaction_id}."
        )
        return {}

    managers_involved = trans.get("managers_involved")
    if not managers_involved:
        logger.warning(
            f"Missing managers involved for transaction {transaction_id}."
        )
        return {}

    trade_item = {"year": year, "week": week, "managers_involved": []}

    # Create sent/received arrays for each manager involved
    for m in managers_involved:
        if not isinstance(m, str):
            logger.warning(
                f"Manager {m} in transaction {transaction_id} is not a string."
            )

        trade_item[f"{m.lower().replace(' ', '_')}_received"] = []
        trade_item[f"{m.lower().replace(' ', '_')}_sent"] = []
        trade_item["managers_involved"].append(
            get_image_url(m, dictionary=True)
        )

    # Populate sent/received arrays with players/assets
    for player in trans['trade_details']:
        trade_details_player_details = (
            trans.get('trade_details', {}).get(player, {})
        )
        old_manager = trade_details_player_details.get("old_manager", "")
        new_manager = trade_details_player_details.get("new_manager", "")

        if not old_manager or not new_manager:
            logger.warning(f"Missing trade details for player {player}")
            continue

        old_manager = old_manager.lower().replace(" ", "_")
        new_manager = new_manager.lower().replace(" ", "_")

        player_dict = get_image_url(player, dictionary=True)

        trade_item[f"{old_manager}_sent"].append(deepcopy(player_dict))
        trade_item[f"{new_manager}_received"].append(deepcopy(player_dict))

    trade_item["transaction_id"] = transaction_id

    return deepcopy(trade_item)


def extract_dict_data(
    data: dict[str, Any],
    key_name: str = "name",
    value_name: str = "count",
    cutoff: int = 3,
) -> list:
    """Extract top N items from a dictionary and format with image URLs.

    Handles tie-breaking logic to include all items tied for the cutoff
    position.
    - For example, if cutoff=3 and items 3-5 are tied, all will be included.

    Args:
        data: Raw data dictionary (may contain nested dicts with "total" keys)
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
        top_three = dict(sorted_items[:i + 1])

    # Build formatted output list with image URLs
    items = []
    for item in top_three:
        long_dict = {}
        long_dict[key_name] = item
        long_dict[value_name] = top_three[item]
        long_dict["image_url"] = get_image_url(item)
        items.append(deepcopy(long_dict))

    return deepcopy(items)


def draft_pick_decipher(
    draft_pick_dict: dict[str, Any], weekly_roster_ids: dict[int, str]
) -> str:
    """Decipher draft pick string to manager name.

    Args:
        draft_pick_dict: Sleeper traded draft pick data with keys:
            season, round, roster_id, previous_owner_id, owner_id
        weekly_roster_ids: Mapping of roster IDs to manager names

    Returns:
        Manager name or "Unknown Manager"

    Example:
        >>> draft_pick = {
        ...     "season": "2019",
        ...     "round": 5,
        ...     "roster_id": 1,
        ...     "previous_owner_id": 1,
        ...     "owner_id": 2,
        ... }
    """
    season = draft_pick_dict.get("season", "unknown_year")
    round_num = draft_pick_dict.get("round", "unknown_round")

    origin_team = draft_pick_dict.get("roster_id", "unknown_team")
    origin_manager = weekly_roster_ids.get(origin_team, "unknown_manager")

    return f"{origin_manager}'s {season} Round {round_num} Draft Pick"
