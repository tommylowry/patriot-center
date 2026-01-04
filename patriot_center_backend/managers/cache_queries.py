"""
Cache query helpers for reading manager metadata.

All functions are read-only and query the manager cache to extract
specific views of data (matchups, transactions, rankings, etc.).
"""
from typing import Dict, List
from copy import deepcopy
from decimal import Decimal

from patriot_center_backend.managers.validators import validate_matchup_data
from patriot_center_backend.managers.formatters import get_trade_card, get_matchup_card
from patriot_center_backend.managers.utilities import extract_dict_data, get_image_url

from patriot_center_backend.constants import LEAGUE_IDS


def get_matchup_details_from_cache(cache: dict, manager: str, year: str = None) -> Dict:
    """
    Get matchup details for a manager from cache.
    
    Args:
        cache: Full manager cache (read-only)
        year: Season year
        manager: Manager name
    
    Returns:
        Matchup details dictionary
    """
    matchup_data = {
        "overall":        {},
        "regular_season": {},
        "playoffs":       {}
    }
        
    cached_matchup_data = deepcopy(cache[manager]["summary"]["matchup_data"])
    if year:
        cached_matchup_data = deepcopy(cache[manager]["years"][year]["summary"]["matchup_data"])

    for season_state in ["overall", "regular_season", "playoffs"]:
        
        # Handle no playoff appearances
        if season_state == "playoffs":
            playoff = True
            playoff_appearances = cache[manager]["summary"]["overall_data"]["playoff_appearances"]
            if len(playoff_appearances) == 0:
                playoff = False
            elif year is not None and year not in cache[manager]["years"]:
                playoff = False

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
        
        # Extract record components
        num_wins = cached_matchup_data[season_state]["wins"]["total"]
        num_losses = cached_matchup_data[season_state]["losses"]["total"]
        num_ties = cached_matchup_data[season_state]["ties"]["total"]

        matchup_data[season_state]["wins"] = num_wins
        matchup_data[season_state]["losses"] = num_losses
        matchup_data[season_state]["ties"] = num_ties

        # Calculate win percentage
        num_matchups = num_wins + num_losses + num_ties

        win_percentage = 0.0
        if num_matchups != 0:
            win_percentage = float(Decimal((num_wins / num_matchups * 100)).quantize(Decimal('0.1')))

        matchup_data[season_state]["win_percentage"] = win_percentage

        # Points for/against and averages
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


def get_transaction_details_from_cache(cache: dict, year: str, manager: str,
                                       image_urls_cache: dict, players_cache: dict,
                                       player_ids: dict) -> Dict:
    """Get transaction details from cache."""
    transaction_summary = {
        "trades":      {},
        "adds":        {},
        "drops":       {},
        "faab":        {}
    }

    cached_transaction_data = deepcopy(cache[manager]["summary"]["transactions"])
    if year:
        cached_transaction_data = deepcopy(cache[manager]["years"][year]["summary"]["transactions"])

    if 'faab' in cached_transaction_data:
        for player in cached_transaction_data['faab']['players']:
            cached_transaction_data['faab']['players'][player] = cached_transaction_data['faab']['players'][player]['total_faab_spent']
    
    trades = {
        "total":              cached_transaction_data["trades"]["total"],
        "top_trade_partners": extract_dict_data(deepcopy(cached_transaction_data["trades"]["trade_partners"]),
                                                players_cache, player_ids, image_urls_cache, cache)
    }

    # ---- Trades Summary ----
    
    # Most Aquired Players
    trade_players_acquired = cached_transaction_data["trades"]["trade_players_acquired"]
    most_acquired_players = extract_dict_data(deepcopy(trade_players_acquired),
                                              players_cache, player_ids, image_urls_cache, cache)
    for player in most_acquired_players:
        player_details = deepcopy(trade_players_acquired[player["name"]])
        player["from"] = extract_dict_data(deepcopy(player_details.get("trade_partners", {})),
                                           players_cache, player_ids, image_urls_cache, cache, cutoff=0)
    trades["most_acquired_players"] = most_acquired_players

    # Most Sent Players
    trade_players_sent = cached_transaction_data["trades"]["trade_players_sent"]
    most_sent_players = extract_dict_data(deepcopy(trade_players_sent),
                                          players_cache, player_ids, image_urls_cache, cache)
    for player in most_sent_players:
        player_details = deepcopy(trade_players_sent.get(player["name"], {}))
        player["to"] = extract_dict_data(player_details.get("trade_partners", {}),
                                         players_cache, player_ids, image_urls_cache, cache, cutoff=0)
    trades["most_sent_players"] = most_sent_players

    transaction_summary["trades"] = trades


    # ---- Adds Summary ----
    adds = {
        "total":             cached_transaction_data["adds"]["total"],
        "top_players_added": extract_dict_data(deepcopy(cached_transaction_data["adds"]["players"]),
                                               players_cache, player_ids, image_urls_cache, cache)
    }
    transaction_summary["adds"] = adds
    

    # ---- Drops Summary ----
    drops = {
            "total":               cached_transaction_data["drops"]["total"],
            "top_players_dropped": extract_dict_data(deepcopy(cached_transaction_data["drops"]["players"]),
                                                     players_cache, player_ids, image_urls_cache, cache)
    }
    transaction_summary["drops"] = drops


    # ---- FAAB Summary ----
    # Handle cases where FAAB doesn't exist (e.g., older years before FAAB was implemented)
    if "faab" in cached_transaction_data and cached_transaction_data["faab"]:
        faab = {
            "total_spent": abs(cached_transaction_data["faab"]["total_lost_or_gained"]),
            "biggest_acquisitions": extract_dict_data(deepcopy(cached_transaction_data["faab"]["players"]),
                                                      players_cache, player_ids, image_urls_cache, cache,
                                                      value_name = "amount")
        }

        # FAAB Traded
        sent = cached_transaction_data["faab"]["traded_away"]["total"]
        received = cached_transaction_data["faab"]["acquired_from"]["total"]
        net = received - sent
        faab["faab_traded"] = {
            "sent":     sent,
            "received": received,
            "net":      net
        }
    else:
        # FAAB not available for this year/manager
        faab = {
            "total_spent": 0,
            "biggest_acquisitions": [],
            "faab_traded": {
                "sent": 0,
                "received": 0,
                "net": 0
            }
        }
    transaction_summary["faab"] = faab

    # Return final transaction summary
    return deepcopy(transaction_summary)


def get_overall_data_details_from_cache(cache: dict, year: str, manager: str) -> Dict:
    """Get overall yearly data from cache."""
    cached_overall_data = deepcopy(cache[manager]["summary"]["overall_data"])
        
    overall_data = {
        "playoff_appearances": len(cached_overall_data.get("playoff_appearances", []))
    }

    # ----- Other Overall Data -----
    placements = []
    for year in cached_overall_data.get("placement", {}):
        placement_item = {
            "year": year,
            "placement": cached_overall_data["placement"][year]
        }
        placements.append(placement_item)

    overall_data["placements"] = placements

    return deepcopy(overall_data)


def get_ranking_details_from_cache(cache: dict, manager: str, valid_options_cache: dict,
                                   manager_summary_usage: bool = False, active_only: bool = True,
                                   year: str = None) -> Dict:
    """Get ranking details from cache."""
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

    managers = valid_options_cache[current_year]["managers"]

    returning_dictionary["is_active_manager"] = True
    if manager not in managers:
        returning_dictionary["is_active_manager"] = False
        managers = list(cache.keys())
    
    if not active_only:
        managers = list(cache.keys())

    returning_dictionary["worst"] = len(managers)
    
    for m in managers:
        
        summary_section = deepcopy(cache.get(m, {}).get("summary", {}))
        if year:
            summary_section = deepcopy(cache.get(m, {}).get("years", {}).get(year, {}).get("summary", {}))

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
        num_playoffs = len(cache.get(m, {}).get("summary", {}).get("overall_data", {}).get("playoff_appearances", []))
        
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


def get_head_to_head_details_from_cache(cache: dict, manager: str,
                                        image_urls_cache: dict, players_cache: dict,
                                        player_ids: dict, year: str = None,
                                        opponent: str = None) -> Dict:
    """Get head-to-head matchup details from cache."""
    head_to_head_data = []
        
    cached_head_to_head_data = deepcopy(cache[manager]["summary"]["matchup_data"]["overall"])
    trade_data = deepcopy(cache[manager]["summary"]["transactions"]["trades"])
    if year:
        cached_head_to_head_data = deepcopy(cache[manager]["years"][year]["summary"]["matchup_data"]["overall"])
        trade_data = deepcopy(cache[manager]["years"][year]["summary"]["transactions"]["trades"])
    
    opponents = [opponent] if opponent else list(deepcopy(cached_head_to_head_data.get("points_for", {}).get("opponents", {})).keys())
    
    
    for opponent in opponents:

        opponent_data = {
            "opponent":           get_image_url(opponent, players_cache, player_ids, image_urls_cache, cache, dictionary=True),
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

def get_head_to_head_overall_from_cache(cache: dict, manager1: str, manager2: str, 
                                        players_cache: dict, player_ids: dict,
                                        image_urls_cache: dict,  starters_cache, year: str = None,
                                        list_all_matchups: bool = False) -> Dict:
    """Get overall head-to-head record between two managers."""
    if list_all_matchups:
        years = list(cache[manager1].get("years", {}).keys())
        if year:
            years = [year]
        matchup_history = []
    else:
        head_to_head_overall = {}

        head_to_head_data = get_head_to_head_details_from_cache(cache, manager1, image_urls_cache,
                                                                players_cache, player_ids,
                                                                year=year, opponent=manager2)

        head_to_head_overall[f"{manager1.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("wins")
        head_to_head_overall[f"{manager2.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("losses")
        head_to_head_overall[f"ties"] = head_to_head_data.get("ties")


        # Get average margin of victory, last win, biggest blowout
        years = list(cache[manager1].get("years", {}).keys())
        manager_1_points_for = cache[manager1].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager2, 0.0)
        manager_2_points_for = cache[manager2].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager1, 0.0)
        if year:
            years = [year]
            manager_1_points_for = cache[manager1].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager2, 0.0)
            manager_2_points_for = cache[manager2].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager1, 0.0)

        manager_1_victory_margins = []
        manager_1_last_win        = {}
        manager_1_biggest_blowout = {}

        manager_2_victory_margins = []
        manager_2_last_win        = {}
        manager_2_biggest_blowout = {}
    

    for y in years:
        
        weeks = deepcopy(cache[manager1]["years"][y]["weeks"])
        
        for w in weeks:
            matchup_data = deepcopy(weeks.get(w, {}).get("matchup_data", {}))

            # Manager didn't play that week but had transactions
            if matchup_data == {}:
                continue

            validation = validate_matchup_data(matchup_data, cache)
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
                        matchup_history.append(get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache))
                        continue


                    manager_1_victory_margin = manager_1_score - manager_2_score
                    manager_1_victory_margins.append(manager_1_victory_margin)


                    # see if this matchup is the latest win for manager_1
                    apply = False
                    if manager_1_last_win.get("year", "") == "": # initial
                        apply = True
                    elif int(manager_1_last_win["year"]) < int(y): # current year is more recent
                        apply = True
                    elif int(manager_1_last_win["year"]) == int(y) and int(manager_1_last_win["week"]) < int(w): # current year is same, week is more recent
                        apply = True
                    
                    if apply:
                        manager_1_last_win = get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache)

                    
                    
                    # see if this matchup is the biggest blowout for manager_1
                    apply = False
                    if manager_1_biggest_blowout.get("year", "") == "": # initial
                        apply = True
                    elif manager_1_victory_margin == sorted(manager_1_victory_margins, reverse = True)[0]: # current victory margin is largest
                        apply = True
                    
                    if apply:
                        manager_1_biggest_blowout = get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache)
                
                # manager_2 won
                if matchup_data.get("result", "") == "loss":
                    
                    if list_all_matchups:
                        matchup_history.append(get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache))
                        continue


                    manager_2_victory_margin = manager_2_score - manager_1_score
                    manager_2_victory_margins.append(manager_2_victory_margin)


                    # see if this matchup is the latest win for manager_1
                    apply = False
                    if manager_2_last_win.get("year", "") == "": # initial
                        apply = True
                    elif int(manager_2_last_win["year"]) < int(y): # current year is more recent
                        apply = True
                    elif int(manager_2_last_win["year"]) == int(y) and int(manager_2_last_win["week"]) < int(w): # current year is same, week is more recent
                        apply = True
                    
                    if apply:
                        manager_2_last_win = get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache)

                    
                    
                    # see if this matchup is the biggest blowout for manager_1
                    apply = False
                    if manager_2_biggest_blowout.get("year", "") == "": # initial
                        apply = True
                    elif manager_2_victory_margin == sorted(manager_2_victory_margins, reverse = True)[0]: # current victory margin is largest
                        apply = True
                    
                    if apply:
                        manager_2_biggest_blowout = get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache)
                
                else: # Tie
                    
                    if list_all_matchups:
                        matchup_history.append(get_matchup_card(cache, manager1, manager2, y, w, players_cache, player_ids, image_urls_cache, starters_cache))
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
    


def get_trade_history_between_two_managers(cache: dict, manager1: str, manager2: str,
                                           transaction_ids_cache: dict,
                                           image_urls_cache: dict, players_cache: dict,
                                           player_ids: dict, year: str = None) -> List:
    """Get full trade history between two managers."""
    # Call get_trade_card from formatters
    years = list(cache[manager1].get("years", {}).keys())
    if year:
        years = [year]
    
    # Gather all transaction IDs for manager_1
    transaction_ids = []
    for y in years:
        weeks = deepcopy(cache[manager1]["years"][y]["weeks"])
        for w in weeks:
            weekly_trade_transaction_ids = deepcopy(cache.get(manager1, {}).get("years", {}).get(y, {}).get("weeks", {}).get(w, {}).get("transactions", {}).get("trades", {}).get("transaction_ids", []))
            transaction_ids.extend(weekly_trade_transaction_ids)


    # Filter to only those involving both managers
    for tid in deepcopy(transaction_ids):
        if manager2 not in transaction_ids_cache.get(tid, {}).get("managers_involved", []):
            transaction_ids.remove(tid)

    trades_between = []
    

    for t in transaction_ids:
        trades_between.append(get_trade_card(t, transaction_ids_cache, image_urls_cache, players_cache, player_ids, cache))
    
    trades_between.reverse()
    return trades_between


def get_manager_awards_from_cache(cache: dict, manager: str,
                                  players_cache: dict, player_ids: dict,
                                  image_urls_cache: dict) -> Dict:
    """Get manager awards from cache."""
    awards = {}

    cached_overall_data = deepcopy(cache[manager]["summary"]["overall_data"])
    
    # First/Second/Third Place Finishes
    placement_counts = {
        "first_place": 0,
        "second_place": 0,
        "third_place": 0
    }
    for year in cached_overall_data.get("placement", {}):
        placement = cached_overall_data["placement"][year]
        if placement == 1:
            placement_counts["first_place"] += 1
        elif placement == 2:
            placement_counts["second_place"] += 1
        elif placement == 3:
            placement_counts["third_place"] += 1
    awards.update(deepcopy(placement_counts))

    # Playoff Appearances
    awards["playoff_appearances"] = len(cached_overall_data.get("playoff_appearances", []))


    # Most Trades in a Year
    most_trades_in_year = {
        "count": 0,
        "year":  ""
    }
    for year in cache[manager].get("years", {}):
        num_trades = cache[manager]["years"][year]["summary"]["transactions"]["trades"]["total"]
        if num_trades > most_trades_in_year["count"]:
            most_trades_in_year["count"] = num_trades
            most_trades_in_year["year"] = year
    awards["most_trades_in_year"] = deepcopy(most_trades_in_year)


    # Biggest FAAB Bid
    biggest_faab_bid = {
        "player": "",
        "amount": 0,
        "year":   ""
    }
    # Check if FAAB data exists in summary before accessing
    if "faab" in cache[manager].get("summary", {}).get("transactions", {}) and cache[manager]["summary"]["transactions"]["faab"]:

        for year in cache[manager].get("years", {}):
            
            weeks = deepcopy(cache[manager]["years"][year]["weeks"])
            for week in weeks:
                
                weekly_faab_bids = deepcopy(weeks.get(week, {}).get("transactions", {}).get("faab", {}).get("players", {}))
                for player in weekly_faab_bids:
                    
                    bid_amount = weekly_faab_bids[player]["total_faab_spent"]
                    if bid_amount > biggest_faab_bid["amount"]:
                        biggest_faab_bid["player"] = get_image_url(player, players_cache, player_ids, image_urls_cache, cache, dictionary=True)
                        biggest_faab_bid["amount"] = bid_amount
                        biggest_faab_bid["year"]   = year
    
    awards["biggest_faab_bid"] = deepcopy(biggest_faab_bid)

    
    return deepcopy(awards)

def get_manager_score_awards_from_cache(cache: dict, manager: str, players_cache: dict,
                                        player_ids: dict, image_urls_cache: dict,
                                        starters_cache: dict) -> Dict:
    """Get manager scoring awards from cache."""
    score_awards = {}

    highest_weekly_score = {}
    lowest_weekly_score = {}
    biggest_blowout_win = {}
    biggest_blowout_loss = {}


    for year in cache[manager].get("years", {}):
        weeks = deepcopy(cache[manager]["years"][year]["weeks"])
        for week in weeks:
            matchup_data = deepcopy(weeks.get(week, {}).get("matchup_data", {}))

            validation = validate_matchup_data(matchup_data, cache)
            if "Warning" in validation:
                print(f"{validation} {manager}, year {year}, week {week}")
                continue
            if validation == "Empty":
                continue

            points_for         = matchup_data.get("points_for", 0.0)
            points_against     = matchup_data.get("points_against", 0.0)
            point_differential = float(Decimal((points_for - points_against)).quantize(Decimal('0.01')))

            # Highest Weekly Score
            if points_for > highest_weekly_score.get("manager_1_score", 0.0):
                highest_weekly_score = get_matchup_card(cache, manager, matchup_data.get("opponent_manager", ""), year, week,
                                                        players_cache, player_ids, image_urls_cache, starters_cache)

            # Lowest Weekly Score
            if points_for < lowest_weekly_score.get("manager_1_score", float('inf')):
                lowest_weekly_score = get_matchup_card(cache, manager, matchup_data.get("opponent_manager", ""), year, week,
                                                       players_cache, player_ids, image_urls_cache, starters_cache)

            # Biggest Blowout Win
            if point_differential > biggest_blowout_win.get("differential", 0.0):
                biggest_blowout_win = get_matchup_card(cache, manager, matchup_data.get("opponent_manager", ""), year, week,
                                                       players_cache, player_ids, image_urls_cache, starters_cache)
                biggest_blowout_win["differential"] = point_differential
                

            # Biggest Blowout Loss
            if point_differential < biggest_blowout_loss.get("differential", 0.0):
                biggest_blowout_loss = get_matchup_card(cache, manager, matchup_data.get("opponent_manager", ""), year, week,
                                                        players_cache, player_ids, image_urls_cache, starters_cache)
                biggest_blowout_loss["differential"] = point_differential

    score_awards["highest_weekly_score"] = deepcopy(highest_weekly_score)
    score_awards["lowest_weekly_score"]  = deepcopy(lowest_weekly_score)
    score_awards["biggest_blowout_win"]  = deepcopy(biggest_blowout_win)
    score_awards["biggest_blowout_loss"] = deepcopy(biggest_blowout_loss)

    return deepcopy(score_awards)