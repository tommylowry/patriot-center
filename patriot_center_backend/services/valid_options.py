from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players
from patriot_center_backend.services.managers import fetch_starters
from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

def fetch_valid_options(arg1, arg2, arg3, arg4):
    
    default_response = {
        "year": list(LEAGUE_IDS.keys()),
        "week": list(range(1, 18)),
        "position": ["QB", "RB", "WR", "TE", "K", "DEF"],
        "manager": list(NAME_TO_MANAGER_USERNAME.keys())
    }
    
    year, week, position, manager, player = _parse_args(arg1, arg2, arg3, arg4)

    # If all arguments are None, return all options
    if year == None and week == None and position == None and manager == None and player == None:
        return default_response
    
    if year == None and week != None:
        raise ValueError("Week specified without a year.")
    
    starters_dict = fetch_starters(manager=manager, season=year, week=week)
    
    filtered_dict = _filter_year(year, starters_dict, default_response)
    filtered_dict = _filter_week(week, starters_dict, filtered_dict)
    filtered_dict = _filter_position(position, starters_dict, filtered_dict)
    # filtered_dict = _filter_manager(manager, starters_dict, filtered_dict)
    # filtered_dict = _filter_player(player, starters_dict, filtered_dict)

    return filtered_dict


def _parse_args(arg1, arg2, arg3, arg4):
    """
    Parse and validate input arguments for fetching valid options.

    Args:
        arg1, arg2, arg3, arg4: Input arguments that may represent year, week, position, manager, or player.

    Returns:
        tuple: Parsed values for year, week, position, manager, player.
    """
    year     = None
    week     = None
    position = None
    manager  = None
    player   = None

    players = fetch_players()

    args = [arg1, arg2, arg3, arg4]
    for arg in args:
        if arg == None:
            continue

        if isinstance(arg, int):
            
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if year != None:
                    raise ValueError("Multiple year arguments provided.")
                year = arg
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if week != None:
                    raise ValueError("Multiple week arguments provided.")
                week = arg
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        elif isinstance(arg, str):
            
            # Check if arg is a valid position
            if arg.upper() in {"QB", "RB", "WR", "TE", "K", "DEF"}:
                if position != None:
                    raise ValueError("Multiple position arguments provided.")
                position = arg.upper()

            # Check if arg is a manager
            elif arg in NAME_TO_MANAGER_USERNAME:
                if manager != None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
            
            # Check if arg is a player
            elif arg in players:
                if player != None:
                    raise ValueError("Multiple player arguments provided.")
                player = arg
            else:
                raise ValueError(f"Unrecognized argument: {arg}")
        
        else:
            raise TypeError(f"Argument of unsupported type: {type(arg)}")

    return year, week, position, manager, player

def _filter_year(year, starters_dict, filtered_dict):
    if year == None:
        return filtered_dict
    
    # Filter weeks for seasons with fewer weeks
    starters_dict
    
    managers = []
    for year_key, week_dict in starters_dict.items():
        for week_key, manager_dict in week_dict.items():
            for manager_key, _ in manager_dict.items():
                if manager_key not in managers:
                    managers.append(manager_key)
    filtered_dict["manager"] = managers

    return filtered_dict

def _filter_week(week, starters_dict, filtered_dict):
    if week == None:
        return filtered_dict
    
    filtered_dict["week"] = [week]

    managers = []
    for year_key, week_dict in starters_dict.items():
        for week_key, manager_dict in week_dict.items():
            if str(week) != week_key:
                continue
            for manager_key, _ in manager_dict.items():
                if manager_key not in managers:
                    managers.append(manager_key)
    filtered_dict["manager"] = managers

    return filtered_dict

def _filter_position(position, starters_dict, filtered_dict):
    if position == None:
        return filtered_dict
    
    filtered_dict["position"] = [position]

    filter_year = True
    if len(filtered_dict["year"]) == 1:
        filter_year = False
    else:
        years = []

    filter_week["week"] = True
    if len(filtered_dict["week"]) == 1:
        filter_week = False
    else:
        weeks = []


    managers = []
    for year_key, week_dict in starters_dict.items():
        for week_key, manager_dict in week_dict.items():
            for manager_key, player_dict in manager_dict.items():
                for player_key, player_data in player_dict.items():
                    if player_key == "Total_Points":
                        continue
                    if player_data["position"] == position:
                        if filter_year and year_key not in years:
                            years.append(year_key)
                        if filter_week and week_key not in weeks:
                            weeks.append(week_key)
                        if manager_key not in managers:
                            managers.append(manager_key)
                        
    
    filtered_dict["player"] = list(players_set)

    return filtered_dict

dict = fetch_valid_options(2023, 11, None, None)
print(dict)