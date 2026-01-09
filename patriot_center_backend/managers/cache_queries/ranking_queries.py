"""
Cache query helpers for ranking related manager metadata.

All functions are read-only and query the manager cache to extract
the ranking of various views of data.
"""
from copy import deepcopy
from decimal import Decimal
from typing import Dict

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS


def get_ranking_details_from_cache(manager: str, manager_summary_usage: bool = False,
                                   active_only: bool = True, year: str|None = None) -> Dict:
    """
    Calculate manager rankings across all statistical categories.

    Compares manager against all active (or all) managers in 6 categories:
    - Win percentage
    - Average points for
    - Average points against
    - Average point differential
    - Total trades
    - Playoff appearances

    Handles ties properly - managers with same stat value get same rank.

    Args:
        manager: Manager to rank
        manager_summary_usage: If True, returns both values and ranks
        active_only: If True, only rank against active managers
        year: Season year (optional - defaults to all-time stats)

    Returns:
        Dictionary of rankings by category, or dict with 'values' and 'ranks' if manager_summary_usage=True
    """
    manager_cache       = CACHE_MANAGER.get_manager_cache()
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    returning_dictionary = {}
    
    manager_rankings = {
        "win_percentage": [],
        "average_points_for": [],
        "average_points_against": [],
        "average_points_differential": [],
        "trades": [],
        "playoffs": [],
    }

    eval_manager_values = {
        "win_percentage": 0.0,
        "average_points_for": 0.0,
        "average_points_against": 0.0,
        "average_points_differential": 0.0,
        "trades": 0,
        "playoffs": 0,
    }

    current_year = year
    if not year:
        current_year = str(max(LEAGUE_IDS.keys()))

    managers = deepcopy(valid_options_cache[current_year]["managers"])

    returning_dictionary["is_active_manager"] = True
    if manager not in managers:
        returning_dictionary["is_active_manager"] = False
        managers = list(manager_cache.keys())
    
    if not active_only:
        managers = list(manager_cache.keys())

    returning_dictionary["worst"] = len(managers)
    
    for m in managers:
        
        summary_section = deepcopy(manager_cache.get(m, {}).get("summary", {}))
        if year:
            summary_section = deepcopy(manager_cache.get(m, {}).get("years", {}).get(year, {}).get("summary", {}))

            # Extract record components
        num_wins = summary_section["matchup_data"]["overall"]["wins"]["total"]
        num_losses = summary_section["matchup_data"]["overall"]["losses"]["total"]
        num_ties = summary_section["matchup_data"]["overall"]["ties"]["total"]

        # Calculate win percentage
        num_matchups = num_wins + num_losses + num_ties

        win_percentage = 0.0
        if num_matchups != 0:
            win_percentage = float(Decimal((num_wins / num_matchups * 100)).quantize(Decimal('0.1')))

        # Points for/against and averages
        total_points_for         = summary_section["matchup_data"]["overall"]["points_for"]["total"]
        total_points_against     = summary_section["matchup_data"]["overall"]["points_against"]["total"]
        total_point_differential = float(Decimal((total_points_for - total_points_against)).quantize(Decimal('0.01')))
        
        average_points_for         = 0.0
        average_points_against     = 0.0
        average_point_differential = 0.0
        if num_matchups != 0:
            average_points_for         = float(Decimal((total_points_for / num_matchups)).quantize(Decimal('0.01')))
            average_points_against     = float(Decimal((total_points_against / num_matchups)).quantize(Decimal('0.01')))
            average_point_differential = float(Decimal(((total_point_differential) / num_matchups)).quantize(Decimal('0.01')))
        
        num_trades = summary_section["transactions"]["trades"]["total"]
        num_playoffs = len(manager_cache.get(m, {}).get("summary", {}).get("overall_data", {}).get("playoff_appearances", []))
        
        manager_rankings["win_percentage"].append({m: win_percentage})
        manager_rankings["average_points_for"].append({m: average_points_for})
        manager_rankings["average_points_against"].append({m: average_points_against})
        manager_rankings["average_points_differential"].append({m: average_point_differential})
        manager_rankings["trades"].append({m: num_trades})
        manager_rankings["playoffs"].append({m: num_playoffs})

        if m == manager:
            eval_manager_values["win_percentage"] = win_percentage
            eval_manager_values["average_points_for"] = average_points_for
            eval_manager_values["average_points_against"] = average_points_against
            eval_manager_values["average_points_differential"] = average_point_differential
            eval_manager_values["trades"] = num_trades
            eval_manager_values["playoffs"] = num_playoffs

    
    for k in manager_rankings:
        manager_rankings[k].sort(key=lambda item: list(item.values())[0], reverse=True)

        rank = 1
        manager_value = eval_manager_values[k]
        for item in manager_rankings[k]:
            value = item[list(item.keys())[0]]
            if value != manager_value:
                # If the value is different from the previous one, update the rank
                rank += 1
            else:
                returning_dictionary[k] = rank
                break
    
    if manager_summary_usage:
        return {
            "values": deepcopy(eval_manager_values),
            "ranks":  deepcopy(returning_dictionary)
        }
    
    return deepcopy(returning_dictionary)