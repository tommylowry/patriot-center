"""
Cache query helpers for reading head to head related manager metadata.

All functions are read-only and query the manager cache to extract
the head to head view of data.
"""
from copy import deepcopy
from decimal import Decimal
from typing import Dict

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.managers.formatters import get_matchup_card
from patriot_center_backend.managers.utilities import get_image_url
from patriot_center_backend.managers.validators import validate_matchup_data

CACHE_MANAGER = get_cache_manager()

MANAGER_CACHE = CACHE_MANAGER.get_manager_cache()


def get_head_to_head_overall_from_cache(manager1: str, manager2: str,
                                        image_urls: dict, year: str|None = None,
                                        list_all_matchups: bool = False) -> Dict:
    """
    Get comprehensive head-to-head analysis between two managers.

    Iterates through all matchups to find:
    - Overall win/loss/tie record
    - Average margin of victory for each manager
    - Last win for each manager (most recent)
    - Biggest blowout for each manager

    Args:
        manager1: First manager name
        manager2: Second manager name
        image_urls: Dict of image URLs
        year: Season year (optional - defaults to all-time)
        list_all_matchups: If True, returns list of all matchup cards instead of summary stats

    Returns:
        If list_all_matchups=True: List of all matchup cards
        Otherwise: Dict with record, average margins, last wins, and biggest blowouts
    """
    if list_all_matchups:
        years = list(MANAGER_CACHE[manager1].get("years", {}).keys())
        if year:
            years = [year]
        matchup_history = []
    else:
        head_to_head_overall = {}

        head_to_head_data = get_head_to_head_details_from_cache(manager1, image_urls,
                                                                year=year, opponent=manager2)

        head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("wins")
        head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("losses")
        head_to_head_overall[f"ties"] = head_to_head_data.get("ties")


        # Get average margin of victory, last win, biggest blowout
        years = list(MANAGER_CACHE[manager1].get("years", {}).keys())
        manager_1_points_for = MANAGER_CACHE[manager1].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager2, 0.0)
        manager_2_points_for = MANAGER_CACHE[manager2].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager1, 0.0)
        if year:
            years = [year]
            manager_1_points_for = MANAGER_CACHE[manager1].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager2, 0.0)
            manager_2_points_for = MANAGER_CACHE[manager2].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager1, 0.0)

        manager_1_victory_margins = []
        manager_1_last_win        = {}
        manager_1_biggest_blowout = {}

        manager_2_victory_margins = []
        manager_2_last_win        = {}
        manager_2_biggest_blowout = {}
    

    for y in years:
        
        weeks = deepcopy(MANAGER_CACHE[manager1]["years"][y]["weeks"])
        
        for w in weeks:
            matchup_data = deepcopy(weeks.get(w, {}).get("matchup_data", {}))

            # Manager didn't play that week but had transactions
            if matchup_data == {}:
                continue

            validation = validate_matchup_data(matchup_data)
            if "Warning" in validation:
                print(f"{validation} {manager1}, year {y}, week {w}")
                continue
            if validation == "Empty":
                continue

            # we got our matchup
            if manager2 == matchup_data.get("opponent_manager", ""):

                manager_1_score = matchup_data.get("points_for")
                manager_2_score = matchup_data.get("points_against")
                
                # manager 1 won
                if matchup_data.get("result", "") == "win":

                    if list_all_matchups:
                        matchup_history.append(get_matchup_card(manager1, manager2, y, w, image_urls))
                        continue


                    manager_1_victory_margin = manager_1_score - manager_2_score
                    manager_1_victory_margins.append(manager_1_victory_margin)

                    # Determine if this is manager_1's most recent win
                    apply = False
                    if manager_1_last_win.get("year", "") == "": # First win found
                        apply = True
                    elif int(manager_1_last_win["year"]) < int(y): # More recent year
                        apply = True
                    elif int(manager_1_last_win["year"]) == int(y) and int(manager_1_last_win["week"]) < int(w): # Same year, later week
                        apply = True

                    if apply:
                        manager_1_last_win = get_matchup_card(manager1, manager2, y, w, image_urls)

                    # Determine if this is manager_1's biggest blowout
                    apply = False
                    if manager_1_biggest_blowout.get("year", "") == "": # First win found
                        apply = True
                    elif manager_1_victory_margin == sorted(manager_1_victory_margins, reverse = True)[0]: # Largest margin so far
                        apply = True

                    if apply:
                        manager_1_biggest_blowout = get_matchup_card(manager1, manager2, y, w, image_urls)
                
                # manager_2 won
                if matchup_data.get("result", "") == "loss":
                    
                    if list_all_matchups:
                        matchup_history.append(get_matchup_card(manager1, manager2, y, w, image_urls))
                        continue


                    manager_2_victory_margin = manager_2_score - manager_1_score
                    manager_2_victory_margins.append(manager_2_victory_margin)

                    # Determine if this is manager_2's most recent win
                    apply = False
                    if manager_2_last_win.get("year", "") == "": # First win found
                        apply = True
                    elif int(manager_2_last_win["year"]) < int(y): # More recent year
                        apply = True
                    elif int(manager_2_last_win["year"]) == int(y) and int(manager_2_last_win["week"]) < int(w): # Same year, later week
                        apply = True

                    if apply:
                        manager_2_last_win = get_matchup_card(manager1, manager2, y, w, image_urls)

                    # Determine if this is manager_2's biggest blowout
                    apply = False
                    if manager_2_biggest_blowout.get("year", "") == "": # First win found
                        apply = True
                    elif manager_2_victory_margin == sorted(manager_2_victory_margins, reverse = True)[0]: # Largest margin so far
                        apply = True

                    if apply:
                        manager_2_biggest_blowout = get_matchup_card(manager1, manager2, y, w, image_urls)
                
                else: # Tie
                    
                    if list_all_matchups:
                        matchup_history.append(get_matchup_card(manager1, manager2, y, w, image_urls))
                        continue
    
    if list_all_matchups:
        matchup_history.reverse()
        return deepcopy(matchup_history)


    if len(manager_1_victory_margins) == 0:
        print(f"WARNING: No victories found for {manager1} against {manager2}. Cannot compute average margin of victory.")
        manager_1_average_margin_of_victory = None
    else:
        manager_1_average_margin_of_victory =  float(Decimal(sum(manager_1_victory_margins) / len(manager_1_victory_margins)).quantize(Decimal('0.01')))
    
    
    if len(manager_2_victory_margins) == 0:
        print(f"WARNING: No victories found for {manager2} against {manager1}. Cannot compute average margin of victory.")
        manager_2_average_margin_of_victory = None
    else:
        manager_2_average_margin_of_victory =  float(Decimal(sum(manager_2_victory_margins) / len(manager_2_victory_margins)).quantize(Decimal('0.01')))

    
    # put all the data in
    head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_points_for"]                = manager_1_points_for
    head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_average_margin_of_victory"] = manager_1_average_margin_of_victory
    head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_points_for"]                = manager_2_points_for
    head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_average_margin_of_victory"] = manager_2_average_margin_of_victory

    head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_last_win"]        = deepcopy(manager_1_last_win)
    head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_last_win"]        = deepcopy(manager_2_last_win)
    head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_biggest_blowout"] = deepcopy(manager_1_biggest_blowout)
    head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_biggest_blowout"] = deepcopy(manager_2_biggest_blowout)
    

    return deepcopy(head_to_head_overall)

def get_head_to_head_details_from_cache(manager: str, image_urls: dict,
                                        year: str|None = None,
                                        opponent: str|None = None) -> Dict:
    """
    Get head-to-head record(s) for a manager against opponent(s).

    If opponent specified, returns single H2H record.
    If no opponent, returns list of H2H records against all opponents.

    Args:
        manager: Manager name
        image_urls: Dict of image URLs
        year: Season year (optional - defaults to all-time)
        opponent: Specific opponent (optional - defaults to all opponents)

    Returns:
        Single opponent dict if opponent specified, otherwise list of all opponent dicts
    """
    head_to_head_data = []
        
    cached_head_to_head_data = deepcopy(MANAGER_CACHE[manager]["summary"]["matchup_data"]["overall"])
    trade_data = deepcopy(MANAGER_CACHE[manager]["summary"]["transactions"]["trades"])
    if year:
        cached_head_to_head_data = deepcopy(MANAGER_CACHE[manager]["years"][year]["summary"]["matchup_data"]["overall"])
        trade_data = deepcopy(MANAGER_CACHE[manager]["years"][year]["summary"]["transactions"]["trades"])
    
    opponents = [opponent] if opponent else list(deepcopy(cached_head_to_head_data.get("points_for", {}).get("opponents", {})).keys())
    
    
    for opponent in opponents:

        opponent_data = {
            "opponent":           get_image_url(opponent, image_urls, dictionary=True),
            "wins":               cached_head_to_head_data["wins"]["opponents"].get(opponent, 0),
            "losses":             cached_head_to_head_data["losses"]["opponents"].get(opponent, 0),
            "ties":               cached_head_to_head_data["ties"]["opponents"].get(opponent, 0),
            "points_for":         cached_head_to_head_data["points_for"]["opponents"].get(opponent, 0.0),
            "points_against":     cached_head_to_head_data["points_against"]["opponents"].get(opponent, 0.0),
            "num_trades_between": trade_data["trade_partners"].get(opponent, 0)
        }
        head_to_head_data.append(deepcopy(opponent_data))
    
    if len(head_to_head_data) == 1:
        return deepcopy(head_to_head_data[0])
    
    return deepcopy(head_to_head_data)