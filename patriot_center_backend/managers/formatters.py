"""
Data formatting and presentation helpers.

Formats matchup cards, trade cards, and determines season state.
"""
from copy import deepcopy
from typing import Any, Dict, List, Optional

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.utilities import get_image_url
from patriot_center_backend.utils.helpers import fetch_sleeper_data

MANAGER_CACHE         = CACHE_MANAGER.get_manager_cache()
STARTERS_CACHE        = CACHE_MANAGER.get_starters_cache()
PLAYERS_CACHE         = CACHE_MANAGER.get_players_cache()
PLAYER_IDS_CACHE      = CACHE_MANAGER.get_player_ids_cache()
TRANSACTION_IDS_CACHE = CACHE_MANAGER.get_transaction_ids_cache()


def get_season_state(week: str, year: str, playoff_week_start: Optional[int]) -> str:
    """
    Determine the current state of the season (regular season or playoffs).

    Args:
        week: Current week number as string
        year: Current year as string
        playoff_week_start: Week when playoffs start (fetched from API if not provided)

    Returns:
        "regular_season" or "playoffs"

    Raises:
        ValueError: If week or year not provided
    """
    if not week or not year:
        raise ValueError("Week or Year not set. Cannot determine season state.")

    # Fetch playoff week start from league settings if not provided
    if not playoff_week_start:
        league_info = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")
        playoff_week_start = league_info.get("settings", {}).get("playoff_week_start", None)
    
    if int(week) >= playoff_week_start:
        return "playoffs"
    return "regular_season"

def get_top_3_scorers_from_matchup_data(matchup_data: dict, manager_1: str,
                                        manager_2: str, image_urls: dict) -> List[Dict]:
    """
    Extract top 3 and lowest scorers from matchup data for both managers.

    Uses insertion sort to maintain top 3 scorers while tracking the lowest scorer.
    Modifies matchup_data in-place to add scorer data.

    Args:
        matchup_data: Matchup data dictionary (modified in-place)
        manager_1: First manager name
        manager_2: Second manager name
        image_urls: Dict of image URLs

    Returns:
        Dictionary containing top 3 and lowest scorers for both managers
    """
    # Validate that year and week are present
    if "year" not in matchup_data or "week" not in matchup_data:
        print("WARNING: matchup_data missing year or week. Cannot get top 3 scorers.")
        
        matchup_data["manager_1_top_3_scorers"] = []
        matchup_data["manager_2_top_3_scorers"] = []
        matchup_data["manager_1_lowest_scorer"] = []
        matchup_data["manager_2_lowest_scorer"] = []
        return {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": [],
            "manager_2_lowest_scorer": []
        }
    
    # Validate that starter data exists for both managers
    if manager_1 not in STARTERS_CACHE.get(matchup_data["year"], {}).get(matchup_data["week"], {}) or manager_2 not in STARTERS_CACHE.get(matchup_data["year"], {}).get(matchup_data["week"], {}):
        print(f"WARNING: Starter data missing for week {matchup_data['week']}, year {matchup_data['year']}. Cannot get top 3 scorers for {manager_1} vs {manager_2}.")
        
        matchup_data["manager_1_top_3_scorers"] = []
        matchup_data["manager_2_top_3_scorers"] = []
        matchup_data["manager_1_lowest_scorer"] = []
        matchup_data["manager_2_lowest_scorer"] = []
        return {
            "manager_1_top_3_scorers": [],
            "manager_2_top_3_scorers": [],
            "manager_1_lowest_scorer": [],
            "manager_2_lowest_scorer": []
        }


    manager_1_starters = deepcopy(STARTERS_CACHE[matchup_data["year"]][matchup_data["week"]][manager_1])
    manager_2_starters = deepcopy(STARTERS_CACHE[matchup_data["year"]][matchup_data["week"]][manager_2])
    # Remove total points aggregate, we only want individual players
    manager_1_starters.pop("Total_Points")
    manager_2_starters.pop("Total_Points")

    # Process manager 1's starters
    manager_1_top_scorers = []
    manager_1_lowest_scorer = {"score": 10000.0}  # Initialize with high value to find minimum
    for player in manager_1_starters:
        player_dict = get_image_url(player, image_urls, dictionary=True)
        
        player_id =  PLAYERS_CACHE[player]["player_id"]
        first_name = PLAYER_IDS_CACHE[player_id]['first_name']
        last_name =  PLAYER_IDS_CACHE[player_id]['last_name']
        
        player_dict.update(
            {
                "first_name": first_name,
                "last_name": last_name,
                "score": manager_1_starters[player]["points"],
                "position": manager_1_starters[player]["position"]
            }
        )

        # Track lowest scorer
        if player_dict["score"] < manager_1_lowest_scorer["score"]:
            manager_1_lowest_scorer = deepcopy(player_dict)

        # Maintain sorted top 3 list using insertion sort
        if len(manager_1_top_scorers) == 0:
            manager_1_top_scorers.append(player_dict)
        else:
            inserted = False
            # Find correct position in sorted list (highest to lowest)
            for i in range(0, len(manager_1_top_scorers)):
                if manager_1_starters[player]["points"] > manager_1_top_scorers[i]["score"]:
                    manager_1_top_scorers.insert(i, player_dict)
                    # Keep only top 3
                    if len(manager_1_top_scorers) > 3:
                        manager_1_top_scorers.pop()
                    inserted = True
                    break

            # If not inserted and we have fewer than 3, append to end
            if not inserted and len(manager_1_top_scorers) < 3:
                manager_1_top_scorers.append(player_dict)


    # Process manager 2's starters (same logic as manager 1)
    manager_2_top_scorers = []
    manager_2_lowest_scorer = {"score": 10000.0}  # Initialize with high value to find minimum
    for player in manager_2_starters:
        player_dict = get_image_url(player, image_urls, dictionary=True)
        
        player_id =  PLAYERS_CACHE[player]["player_id"]
        first_name = PLAYER_IDS_CACHE[player_id]['first_name']
        last_name =  PLAYER_IDS_CACHE[player_id]['last_name']

        player_dict.update(
            {
                "first_name": first_name,
                "last_name": last_name,
                "score": manager_2_starters[player]["points"],
                "position": manager_2_starters[player]["position"]
            }
        )

        # Track lowest scorer
        if player_dict["score"] < manager_2_lowest_scorer["score"]:
            manager_2_lowest_scorer = deepcopy(player_dict)

        # Maintain sorted top 3 list using insertion sort
        if len(manager_2_top_scorers) == 0:
            manager_2_top_scorers.append(player_dict)
        else:
            inserted = False
            # Find correct position in sorted list (highest to lowest)
            for i in range(0, len(manager_2_top_scorers)):
                if manager_2_starters[player]["points"] > manager_2_top_scorers[i]["score"]:
                    manager_2_top_scorers.insert(i, player_dict)
                    # Keep only top 3
                    if len(manager_2_top_scorers) > 3:
                        manager_2_top_scorers.pop()
                    inserted = True
                    break

            # If not inserted and we have fewer than 3, append to end
            if not inserted and len(manager_2_top_scorers) < 3:
                manager_2_top_scorers.append(player_dict)
        

    matchup_data["manager_1_top_3_scorers"] = manager_1_top_scorers
    matchup_data["manager_2_top_3_scorers"] = manager_2_top_scorers
    matchup_data['manager_1_lowest_scorer'] = manager_1_lowest_scorer
    matchup_data['manager_2_lowest_scorer'] = manager_2_lowest_scorer
    return {
            "manager_1_top_3_scorers": manager_1_top_scorers,
            "manager_2_top_3_scorers": manager_2_top_scorers,
            "manager_1_lowest_scorer": manager_1_lowest_scorer,
            "manager_2_lowest_scorer": manager_2_lowest_scorer
        }

def get_matchup_card(manager_1: str, manager_2: str, year: str, week: str,
                     image_urls: dict) -> Dict[str, Any]:
    """
    Generate complete matchup card with scores, winner, and top performers.

    Creates a formatted matchup summary including both managers' scores,
    the winner determination, and top 3/lowest scorers for each team.

    Args:
        manager_1: First manager name
        manager_2: Second manager name
        year: Season year as string
        week: Week number as string
        image_urls: Image URL cache

    Returns:
        Dictionary containing matchup details, scores, winner, and top performers
        Empty dict if matchup data incomplete
    """
    matchup_data = MANAGER_CACHE[manager_1]["years"].get(year, {}).get("weeks", {}).get(week, {}).get("matchup_data", {})
    manager_1_score = matchup_data.get("points_for", 0.0)
    manager_2_score = matchup_data.get("points_against", 0.0)

    if manager_1_score == 0.0 or manager_2_score == 0.0:
        print(f"WARNING: Incomplete matchup data for {manager_1} vs {manager_2} in year {year}, week {week}.")
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
        "manager_1": {"name": manager_1, "image_url": get_image_url(manager_1, image_urls)},
        "manager_2": {"name": manager_2, "image_url": get_image_url(manager_2, image_urls)},
        "manager_1_score": manager_1_score,
        "manager_2_score": manager_2_score,
        "winner": winner
    }

    get_top_3_scorers_from_matchup_data(matchup, manager_1, manager_2, image_urls)

    return deepcopy(matchup)

def get_trade_card(transaction_id: str, image_urls: dict) -> Dict[str, Any]:
    """
    Generate formatted trade card showing all players/assets exchanged.

    Creates a structured trade summary with managers involved and
    items sent/received by each party. Handles multi-party trades.

    Args:
        transaction_id: Transaction ID to look up
        image_urls: Dict of image URLs

    Returns:
        Trade card dictionary with year, week, managers, and items exchanged
    """
    trans =  TRANSACTION_IDS_CACHE[transaction_id]
    trade_item = {
        "year": trans["year"],
        "week": trans["week"],
        "managers_involved": []
    }

    # Create sent/received arrays for each manager involved
    for m in trans["managers_involved"]:
        trade_item[f"{m.lower().replace(' ', '_')}_received"] = []
        trade_item[f"{m.lower().replace(' ', '_')}_sent"] = []
        trade_item["managers_involved"].append(get_image_url(m, image_urls, dictionary=True))

    # Populate sent/received arrays with players/assets
    for player in trans['trade_details']:
        old_manager = trans['trade_details'][player]['old_manager'].lower().replace(' ', '_')
        new_manager = trans['trade_details'][player]['new_manager'].lower().replace(' ', '_')

        player_dict = get_image_url(player, image_urls, dictionary=True)

        trade_item[f"{old_manager}_sent"].append(deepcopy(player_dict))
        trade_item[f"{new_manager}_received"].append(deepcopy(player_dict))
    
    trade_item["transaction_id"] = transaction_id

    return deepcopy(trade_item)