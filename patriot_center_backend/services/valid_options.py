import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME, CURRENT_OPTIONS_SELECTION_FILE
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache
from patriot_center_backend.utils.cache_utils import load_cache, save_cache

VALID_OPTIONS_CACHE = fetch_valid_options_cache()
PLAYERS_DATA = fetch_players()

class ValidOptionsService:
    def __init__(self, arg1, arg2, arg3, arg4):
        
        self.default_response = {
            "years": list(LEAGUE_IDS.keys()),
            "weeks": list(range(1, 18)),
            "positions": list(["QB", "RB", "WR", "TE", "K", "DEF"]),
            "managers": list(NAME_TO_MANAGER_USERNAME.keys())
        }

        self.year = Year(None)
        self.week = Week(None)
        self.manager = Manager(None)
        self.player = Player(None)
        self.position = Position(None)

        self._parse_arg(arg1)
        self._parse_arg(arg2)
        self._parse_arg(arg3)
        self._parse_arg(arg4)


    def _parse_arg(self, arg):
        if arg == None:
            return

        if isinstance(arg, int) or arg.isnumeric():
            arg = int(arg)
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if self.year.selected():
                    raise ValueError("Multiple year arguments provided.")
                self.year = Year(arg)
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if self.week.selected():
                    raise ValueError("Multiple week arguments provided.")
                self.week = Week(arg)
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if self.manager.selected():
                    raise ValueError("Multiple manager arguments provided.")
                self.manager = Manager(arg)
            
            # Check if arg is a player
            elif arg.replace("_", " ").replace("%27", "'") in PLAYERS_DATA:
                
                if self.player.selected():
                    raise ValueError("Multiple player arguments provided.")
                self.player = Player(arg)
            
            elif arg in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if self.position.selected():
                    raise ValueError("Multiple position arguments provided.")
                self.position = Position(arg)
            
            else:
                raise ValueError(f"Unrecognized argument: {arg}")

class Year:
    def __init__(self, year):
        self.year = year
    
    def __str__(self):
        return str(self.year)
    
    def __call__(self):
        return str(self.year)
    
    def selected(self):
        return False if self.year == None else True
    
    def get_weeks(self):
        if not self.selected():
            raise ValueError("Year not selected; cannot get week list.")
        
        weeks = VALID_OPTIONS_CACHE[str(self.year)].get("weeks", [])
        if weeks == []:
            raise ValueError(f"No weeks found for year {self.year}.")
        
        return list(weeks).sort()
    
    def get_managers(self):
        if not self.selected():
            raise ValueError("Year not selected; cannot get manager list.")
        
        managers = VALID_OPTIONS_CACHE[str(self.year)].get("managers", [])
        if managers == []:
            raise ValueError(f"No managers found for year {self.year}.")
        
        return list(managers).sort()
    
    def get_positions(self):
        if not self.selected():
            raise ValueError("Year not selected; cannot get position list.")
        
        positions = VALID_OPTIONS_CACHE[str(self.year)].get("positions", [])
        if positions == []:
            raise ValueError(f"No positions found for year {self.year}.")
        
        return list(positions)

class Week:
    def __init__(self, week):
        self.week = week
    
    def __str__(self):
        return str(self.week)
    
    def __call__(self):
        return str(self.week)
    
    def selected(self):
        return False if self.week == None else True
    
    def get_years(self):
        if not self.selected():
            raise ValueError("Week not selected; cannot get year list.")
        
        years = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.week in data.get("weeks", []):
                if year not in years:
                    years.append(int(year))
        
        if years == []:
            raise ValueError(f"No years found for week {self.week}.")
        
        return list(years).sort()
    
    def get_managers(self):
        if not self.selected():
            raise ValueError("Week not selected; cannot get manager list.")
        
        managers = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.week in data.get("weeks", []):
                for manager in data.get(self.week, []).get("managers", []):
                    if manager not in managers:
                        managers.append(manager)

        if managers == []:
            raise ValueError(f"No managers found for week {self.week}.")

        managers = list(managers).sort()
    
    def get_positions(self):
        if not self.selected():
            raise ValueError("Week not selected; cannot get position list.")
        
        positions = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.week in data.get("weeks", []):
                for position in data.get(self.week, []).get("positions", []):
                    if position not in positions:
                        positions.append(position)
        
        if positions == []:
            raise ValueError(f"No positions found for week {self.week}.")
        
        return list(positions)

class Manager:
    def __init__(self, manager):
        self.manager = manager
    
    def __str__(self):
        self.manager
    
    def __call__(self):
        return self.manager
    
    def selected(self):
        return False if self.manager == None else True
    
    def get_years(self):
        if not self.selected():
            raise ValueError("Manager not selected; cannot get year list.")
        
        years = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.manager in data.get("managers", []):
                if year not in years:
                    years.append(int(year))
        
        if years == []:
            raise ValueError(f"No years found for manager {self.manager}.")
        
        return list(years).sort()
    
    def get_weeks(self):
        if not self.selected():
            raise ValueError("Manager not selected; cannot get week list.")
        
        weeks = []
        for year, data in VALID_OPTIONS_CACHE.items():
            for week in data.get("weeks", []):
                if self.manager in data.get(week, {}).get("managers", []):
                    if week not in weeks:
                        weeks.append(week)
        
        if weeks == []:
            raise ValueError(f"No weeks found for manager {self.manager}.")
        
        return list(weeks).sort()

    def get_positions(self):
        if not self.selected():
            raise ValueError("Manager not selected; cannot get position list.")
        
        positions = []
        for year, data in VALID_OPTIONS_CACHE.items():
            for week in data.get("weeks", []):
                for position in data.get(week, {}).get("positions", []):
                    if self.manager in data.get(week, {}).get("managers", []):
                        if position not in positions:
                            positions.append(position)
        
        if positions == []:
            raise ValueError(f"No positions found for manager {self.manager}.")
        
        return list(positions)

class Player:
    def __init__(self, player):
        if player == None:
            self.player = None
        else:
            self.player = player.replace("_", " ").replace("%27", "'")
    
    def __str__(self):
        return self.player
    
    def __call__(self):
        return self.player
    
    def selected(self):
        return False if self.player == None else True
    
    def get_years(self):
        if not self.selected():
            raise ValueError("Player not selected; cannot get year list.")
        
        years = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.player in data.get("players", []):
                if year not in years:
                    years.append(int(year))
        
        if years == []:
            raise ValueError(f"No years found for player {self.player}.")
        
        return list(years).sort()
    
    def get_weeks(self):
        if not self.selected():
            raise ValueError("Player not selected; cannot get week list.")
        
        weeks = []
        for year, data in VALID_OPTIONS_CACHE.items():
            for week in data.get("weeks", []):
                if self.player in data.get(week, {}).get("players", []):
                    if week not in weeks:
                        weeks.append(week)
        
        if weeks == []:
            raise ValueError(f"No weeks found for player {self.player}.")
        
        return list(weeks).sort()
    
    def get_positions(self):
        if not self.selected():
            raise ValueError("Player not selected; cannot get position list.")
        
        position = PLAYERS_DATA.get(self.player, {}).get("position", None)
        if position == None:
            raise ValueError(f"No position found for player {self.player}.")
        
        return list([position]])


class Position:
    def __init__(self, position):
        self.position = position
    
    def __str__(self):
        return self.position
    
    def __call__(self):
        return self.position
    
    def selected(self):
        return False if self.position == None else True
    
    def get_years(self):
        if not self.selected():
            raise ValueError("Position not selected; cannot get year list.")
        
        years = []
        for year, data in VALID_OPTIONS_CACHE.items():
            if self.position in data.get("positions", []):
                if year not in years:
                    years.append(int(year))
        
        if years == []:
            raise ValueError(f"No years found for position {self.position}.")
        
        return list(years).sort()
    
    def get_weeks(self):
        if not self.selected():
            raise ValueError("Position not selected; cannot get week list.")
        
        weeks = []
        for year, data in VALID_OPTIONS_CACHE.items():
            for week in data.get("weeks", []):
                if self.position in data.get(week, {}).get("positions", []):
                    if week not in weeks:
                        weeks.append(week)
        
        if weeks == []:
            raise ValueError(f"No weeks found for position {self.position}.")
        
        return list(weeks).sort()

    def get_managers(self):
        if not self.selected():
            raise ValueError("Position not selected; cannot get manager list.")
        
        managers = []
        for year, data in VALID_OPTIONS_CACHE.items():
            for week in data.get("weeks", []):
                for manager in data.get(week, {}).get("managers", []):
                    if self.position in data.get(week, {}).get("positions", []):
                        if manager not in managers:
                            managers.append(manager)
        
        if managers == []:
            raise ValueError(f"No managers found for position {self.position}.")
        
        return list(managers).sort()













# RECYCLED CODE FROM OLD BACKEND VERSION TO BE REWRITTEN LATER
# def fetch_valid_options(arg1, arg2, arg3, arg4=None):

#     year, week, manager, player, position = _parse_args(arg1, arg2, arg3, arg4)

#     positions = 
    
#     default_response = {
#         "years": list(LEAGUE_IDS.keys()),
#         "weeks": list(range(1, 18)),
#         "positions": list(["QB", "RB", "WR", "TE", "K", "DEF"]),
#         "managers": list(NAME_TO_MANAGER_USERNAME.keys())
#     }

#     # If all arguments are None, return all options
#     if None 
#         return default_response
    
#     if year == None and week != None:
#         raise ValueError("Week specified without a year.")
    
    

#     filtered_dict = _filter_year(year, default_response)
#     filtered_dict = _filter_week(week, year, filtered_dict) # week needs year
#     filtered_dict = _filter_manager(manager, year, week, filtered_dict)
#     filtered_dict = _filter_player(player, year, manager, week, filtered_dict)
#     filtered_dict = _filter_position(position, filtered_dict)

#     filtered_dict["managers"].sort()
    
#     return filtered_dict


# def _filter_year(year, filtered_dict):
#     if year == None:
#         return filtered_dict

#     return filtered_dict

# def _filter_week(week, filtered_dict):
#     if week == None:
#         return filtered_dict
    
#     return filtered_dict

# def _filter_manager(manager, filtered_dict):
#     if manager == None:
#         return filtered_dict

#     return filtered_dict

# def _filter_player(player, filtered_dict):
#     if player == None:
#         return filtered_dict
    
#     return filtered_dict

# def _filter_position(position, filtered_dict):
#     if position == None:
#         return filtered_dict

#     return filtered_dict
    

# def _trim_list(original_list, keep_list):
#     if keep_list == []:
#         return original_list
    
#     reference_list = original_list.copy()
#     for item in reference_list:
#         if item not in keep_list:
#             original_list.remove(item)
#     return original_list
