"""
Data formatting and presentation helpers.

Formats matchup cards, trade cards, and determines season state.
"""
from typing import Dict, List, Optional
from copy import deepcopy

from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.utilities import get_image_url

def get_season_state(week: str, year: str, playoff_week_start: Optional[int]) -> str:
    """
    Determine the current state of the season.
    
    Args:
        week: Current week number as string
        year: Current year as string
        playoff_week_start: Week when playoffs start (from league settings)
    
    Returns:
        "regular_season", "playoffs", or "offseason"
    """
    if not week or not year:
        raise ValueError("Week or Year not set. Cannot determine season state.")
    
    if not playoff_week_start:
        league_info = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")[0]
        playoff_week_start = league_info.get("settings", {}).get("playoff_week_start", None)
    
    if int(week) >= playoff_week_start:
        return "playoffs"
    return "regular_season"


def get_top_3_scorers_from_matchup_data(matchup_data: dict, manager_1: str, manager_2: str, players_cache: dict,
                                        player_ids: dict, image_urls_cache: dict, cache: dict, starters_cache: dict) -> List[Dict]:
    """
    Extract top 3 scorers from matchup data.
    
    Args:
        matchup_data: Matchup data dictionary
        players_cache: Player cache for lookups
        player_ids: Player ID mapping
        image_urls_cache: Cache of image URLs
    
    Returns:
        List of top 3 scorer dictionaries
    """
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
    
    if manager_1 not in starters_cache.get(matchup_data["year"], {}).get(matchup_data["week"], {}) or manager_2 not in starters_cache.get(matchup_data["year"], {}).get(matchup_data["week"], {}):
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


    manager_1_starters = deepcopy(starters_cache[matchup_data["year"]][matchup_data["week"]][manager_1])
    manager_2_starters = deepcopy(starters_cache[matchup_data["year"]][matchup_data["week"]][manager_2])
    manager_1_starters.pop("Total_Points")
    manager_2_starters.pop("Total_Points")
    
    manager_1_top_scorers = []
    manager_1_lowest_scorer = {"score": 10000.0}
    for player in manager_1_starters:
        player_dict = get_image_url(player, players_cache, player_ids, image_urls_cache, cache, dictionary=True)
        
        player_id =  players_cache[player]["player_id"]
        first_name = player_ids[player_id]['first_name']
        last_name =  player_ids[player_id]['last_name']
        
        player_dict.update(
            {
                "first_name": first_name,
                "last_name": last_name,
                "score": manager_1_starters[player]["points"],
                "position": manager_1_starters[player]["position"]
            }
        )

        if player_dict["score"] < manager_1_lowest_scorer["score"]:
            manager_1_lowest_scorer = deepcopy(player_dict)


        if len(manager_1_top_scorers) == 0:
            manager_1_top_scorers.append(player_dict)
        else:
            inserted = False
            for i in range(0, len(manager_1_top_scorers)):
                if manager_1_starters[player]["points"] > manager_1_top_scorers[i]["score"]:
                    manager_1_top_scorers.insert(i, player_dict)
                    if len(manager_1_top_scorers) > 3:
                        manager_1_top_scorers.pop()
                    inserted = True
                    break

            # If not inserted and we have fewer than 3, append to end
            if not inserted and len(manager_1_top_scorers) < 3:
                manager_1_top_scorers.append(player_dict)
    

    manager_2_top_scorers = []
    manager_2_lowest_scorer = {"score": 10000.0}
    for player in manager_2_starters:
        player_dict = get_image_url(player, players_cache, player_ids, image_urls_cache, cache, dictionary=True)
        
        player_id =  players_cache[player]["player_id"]
        first_name = player_ids[player_id]['first_name']
        last_name =  player_ids[player_id]['last_name']

        player_dict.update(
            {
                "first_name": first_name,
                "last_name": last_name,
                "score": manager_2_starters[player]["points"],
                "position": manager_2_starters[player]["position"]
            }
        )

        if player_dict["score"] < manager_2_lowest_scorer["score"]:
            manager_2_lowest_scorer = deepcopy(player_dict)

        if len(manager_2_top_scorers) == 0:
            manager_2_top_scorers.append(player_dict)
        else:
            inserted = False
            for i in range(0, len(manager_2_top_scorers)):
                if manager_2_starters[player]["points"] > manager_2_top_scorers[i]["score"]:
                    manager_2_top_scorers.insert(i, player_dict)
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


def get_matchup_card(cache: dict, manager_1: str, manager_2: str, year: str, week: str,
                    players_cache: dict, player_ids: dict, 
                    image_urls_cache: dict, starters_cache: dict) -> Dict:
    """
    Generate matchup card for a manager.
    
    Args:
        cache: Full manager cache
        year: Season year
        week: Week number
        manager: Manager name
        players_cache: Player cache
        player_ids: Player ID mapping
        image_urls_cache: Image URL cache
    
    Returns:
        Matchup card dictionary
    """
    matchup_data = cache[manager_1]["years"].get(year, {}).get("weeks", {}).get(week, {}).get("matchup_data", {})
    manager_1_score = matchup_data.get("points_for", 0.0)
    manager_2_score = matchup_data.get("points_against", 0.0)

    if manager_1_score == 0.0 or manager_2_score == 0.0:
        print(f"WARNING: Incomplete matchup data for {manager_1} vs {manager_2} in year {year}, week {week}.")
        return {}
    
    if manager_1_score > manager_2_score:
        winner = manager_1
    elif manager_2_score > manager_1_score:
        winner = manager_2
    else:
        winner = "Tie"
    

    matchup = {
        "year": year,
        "week": week,
        "manager_1": {"name": manager_1, "image_url": get_image_url(manager_1, players_cache, player_ids, image_urls_cache, cache)},
        "manager_2": {"name": manager_2, "image_url": get_image_url(manager_2, players_cache, player_ids, image_urls_cache, cache)},
        "manager_1_score": manager_1_score,
        "manager_2_score": manager_2_score,
        "winner": winner
    }

    get_top_3_scorers_from_matchup_data(matchup, manager_1, manager_2, players_cache, player_ids, image_urls_cache, cache, starters_cache)

    return deepcopy(matchup)


def get_trade_card(transaction_id: str, transaction_ids_cache: dict,
                  image_urls_cache: dict, players_cache: dict,
                  player_ids: dict, cache: dict) -> Dict:
    """
    Generate trade card from transaction ID.
    
    Args:
        transaction_id: Transaction ID to look up
        transaction_ids_cache: Cache of transactions
        image_urls_cache: Image URL cache
        players_cache: Player cache
        player_ids: Player ID mapping
    
    Returns:
        Trade card dictionary
    """
    # PASTE LINES 2255-2281 HERE
    # Use parameters instead of self._*

    trans =  transaction_ids_cache[transaction_id]
    trade_item = {
        "year": trans["year"],
        "week": trans["week"],
        "managers_involved": []
    }

    for m in trans["managers_involved"]:
        trade_item[f"{m.lower().replace(' ', '_')}_received"] = []
        trade_item[f"{m.lower().replace(' ', '_')}_sent"] = []
        trade_item["managers_involved"].append(get_image_url(m, players_cache, player_ids, image_urls_cache, cache, dictionary=True))
    
    for player in trans['trade_details']:
        old_manager = trans['trade_details'][player]['old_manager'].lower().replace(' ', '_')
        new_manager = trans['trade_details'][player]['new_manager'].lower().replace(' ', '_')

        player_dict = get_image_url(player, players_cache, player_ids, image_urls_cache, cache, dictionary=True)

        trade_item[f"{old_manager}_sent"].append(deepcopy(player_dict))
        trade_item[f"{new_manager}_received"].append(deepcopy(player_dict))
    
    trade_item["transaction_id"] = transaction_id

    return deepcopy(trade_item)