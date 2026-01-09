"""
Cache query helpers for reading matchup related manager metadata.

All functions are read-only and query the manager cache to extract
the matchup view of data.
"""
from copy import deepcopy
from decimal import Decimal
from typing import Dict

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.formatters import get_matchup_card

MANAGER_CACHE = CACHE_MANAGER.get_manager_cache()


def get_matchup_details_from_cache(manager: str, year: str = None) -> Dict:
    """
    Get comprehensive matchup statistics broken down by season state.

    Extracts wins, losses, ties, win percentage, and point averages for:
    - Overall (all matchups)
    - Regular season only
    - Playoffs only

    Handles cases where manager has no playoff appearances.

    Args:
        manager: Manager name
        year: Season year (optional - defaults to all-time stats)

    Returns:
        Dictionary with matchup stats for overall, regular_season, and playoffs
    """
    matchup_data = {
        "overall":        {},
        "regular_season": {},
        "playoffs":       {}
    }

    # Get all-time stats by default, or single season stats if year specified
    cached_matchup_data = deepcopy(MANAGER_CACHE[manager]["summary"]["matchup_data"])
    if year:
        cached_matchup_data = deepcopy(MANAGER_CACHE[manager]["years"][year]["summary"]["matchup_data"])

    for season_state in ["overall", "regular_season", "playoffs"]:

        # Handle managers with no playoff appearances
        if season_state == "playoffs":
            playoff = True
            playoff_appearances = MANAGER_CACHE[manager]["summary"]["overall_data"]["playoff_appearances"]
            if len(playoff_appearances) == 0:
                playoff = False
            elif year is not None and year not in MANAGER_CACHE[manager]["years"]:
                playoff = False

            # Return zero stats if manager never made playoffs
            if playoff == False:
                matchup_data[season_state] = {
                    "wins":                       0,
                    "losses":                     0,
                    "ties":                       0,
                    "win_percentage":             0.0,
                    "average_points_for":         0.0,
                    "average_points_against":     0.0,
                    "average_point_differential": 0.0
                }
                continue

        # Extract win-loss-tie record
        num_wins = cached_matchup_data[season_state]["wins"]["total"]
        num_losses = cached_matchup_data[season_state]["losses"]["total"]
        num_ties = cached_matchup_data[season_state]["ties"]["total"]

        matchup_data[season_state]["wins"] = num_wins
        matchup_data[season_state]["losses"] = num_losses
        matchup_data[season_state]["ties"] = num_ties

        # Calculate win percentage (rounded to 1 decimal place)
        num_matchups = num_wins + num_losses + num_ties

        win_percentage = 0.0
        if num_matchups != 0:
            win_percentage = float(Decimal((num_wins / num_matchups * 100)).quantize(Decimal('0.1')))

        matchup_data[season_state]["win_percentage"] = win_percentage

        # Calculate point averages (rounded to 2 decimal places)
        total_points_for         = cached_matchup_data[season_state]["points_for"]["total"]
        total_points_against     = cached_matchup_data[season_state]["points_against"]["total"]
        total_point_differential = float(Decimal((total_points_for - total_points_against)).quantize(Decimal('0.01')))

        average_points_for         = 0.0
        average_points_against     = 0.0
        average_point_differential = 0.0
        if num_matchups != 0:
            average_points_for         = float(Decimal((total_points_for / num_matchups)).quantize(Decimal('0.01')))
            average_points_against     = float(Decimal((total_points_against / num_matchups)).quantize(Decimal('0.01')))
            average_point_differential = float(Decimal(((total_point_differential) / num_matchups)).quantize(Decimal('0.01')))
        

        matchup_data[season_state]["average_points_for"]         = average_points_for
        matchup_data[season_state]["average_points_against"]     = average_points_against
        matchup_data[season_state]["average_point_differential"] = average_point_differential

    return deepcopy(matchup_data)

def get_overall_data_details_from_cache(year: str, manager: str,
                                        image_urls: dict) -> Dict:
    """
    Get career achievements including playoff appearances and season placements.

    Args:
        year: Season year (not currently used in function)
        manager: Manager name
        image_urls: Dict of image urls

    Returns:
        Dictionary with playoff_appearances count and list of placements by year
    """
    cached_overall_data = deepcopy(MANAGER_CACHE[manager]["summary"]["overall_data"])
        
    overall_data = {
        "playoff_appearances": len(cached_overall_data.get("playoff_appearances", []))
    }

    # ----- Other Overall Data -----
    placements = []
    for year in cached_overall_data.get("placement", {}):
        
        week = '17'
        if int(year) <= 2020:
            week = '16'
         
        opponent = MANAGER_CACHE.get(manager, {}).get('years', {}).get(year, {}).get('weeks', {}).get(week, {}).get('matchup_data', {}).get('opponent_manager', "")
        
        matchup_card = {}
        if opponent == "":
            print(f"WARNING: unable to retreive opponent for matchup card for year {year} week {week}")
        else:
            matchup_card = get_matchup_card(manager, opponent, year, week, image_urls)
        
        placement_item = {
            "year": year,
            "placement": cached_overall_data["placement"][year],
            'matchup_card': matchup_card
        }
        placements.append(placement_item)

    overall_data["placements"] = placements

    return deepcopy(overall_data)