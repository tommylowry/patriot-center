import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache

VALID_OPTIONS_CACHE = fetch_valid_options_cache()
PLAYERS_DATA = fetch_players()

"""
Note: week cannot be used as a filter without a year selected
----------------------------------------------------------------------
|| plyr | yr  | wk  | mgr | pos || num |             func           ||
----------------------------------------------------------------------
||  No  | No  | No  | No  | No  ||  0  | none_selected()            ||
||  No  | No  | No  | No  | Yes ||  1  | pos_selected()             ||
||  No  | No  | No  | Yes | No  ||  2  | mgr_selected()             ||
||  No  | No  | No  | Yes | Yes ||  3  | mgr_pos_selected()         ||
**************************************************************************************
||  No  | No  | Yes | No  | No  ||  4  | wk_selected()              || not implemented
||  No  | No  | Yes | No  | Yes ||  5  | wk_pos_selected()          || not implemented
||  No  | No  | Yes | Yes | No  ||  6  | wk_mgr_selected()          || not implemented
||  No  | No  | Yes | Yes | Yes ||  7  | wk_mgr_pos_selected()      || not implemented
**************************************************************************************
||  No  | Yes | No  | No  | No  ||  8  | yr_selected()              ||
||  No  | Yes | No  | No  | Yes ||  9  | yr_pos_selected()          ||
||  No  | Yes | No  | Yes | No  ||  10 | yr_mgr_selected()          ||
||  No  | Yes | No  | Yes | Yes ||  11 | yr_mgr_pos_selected()      ||
||  No  | Yes | Yes | No  | No  ||  12 | yr_wk_selected()           ||
||  No  | Yes | Yes | No  | Yes ||  13 | yr_wk_pos_selected()       ||
||  No  | Yes | Yes | Yes | No  ||  14 | yr_wk_mgr_selected()       ||
||  No  | Yes | Yes | Yes | Yes ||  15 | yr_wk_mgr_pos_selected()   ||
||  Yes | No  | No  | No  | No  ||  16 | plyr_selected()            ||
||  Yes | No  | No  | No  | Yes ||  17 | plyr_pos_selected()        ||
||  Yes | No  | No  | Yes | No  ||  18 | plyr_mgr_selected()        ||
||  Yes | No  | No  | Yes | Yes ||  19 | plyr_mgr_pos_selected()    ||
**************************************************************************************
||  Yes | No  | Yes | No  | No  ||  20 | plyr_wk_selected()         || not implemented
||  Yes | No  | Yes | No  | Yes ||  21 | plyr_wk_pos_selected()     || not implemented
||  Yes | No  | Yes | Yes | No  ||  22 | plyr_wk_mgr_selected()     || not implemented
||  Yes | No  | Yes | Yes | Yes ||  23 | plyr_wk_mgr_pos_selected() || not implemented
**************************************************************************************
||  Yes | Yes | No  | No  | No  ||  24 | plyr_yr_selected()         ||
||  Yes | Yes | No  | No  | Yes ||  25 | plyr_yr_pos_selected()     ||
||  Yes | Yes | No  | Yes | No  ||  26 | plyr_yr_mgr_selected()     ||
||  Yes | Yes | No  | Yes | Yes ||  27 | plyr_yr_mgr_pos_selected() ||
||  Yes | Yes | Yes | No  | No  ||  28 | plyr_yr_wk_selected()      ||
||  Yes | Yes | Yes | No  | Yes ||  29 | plyr_yr_wk_pos_selected()  ||
||  Yes | Yes | Yes | Yes | No  ||  30 | plyr_yr_wk_mgr_selected()  ||
||  Yes | Yes | Yes | Yes | Yes ||  31 | all_selected()             ||
----------------------------------------------------------------------
"""
class ValidOptionsService:
    def __init__(self, arg1: str, arg2: str, arg3: str, arg4: str):
        
        self.years_list     = list([str(year) for year in list(LEAGUE_IDS.keys())]).sort()
        self.weeks_list     = list([str(week) for week in list(range(1, 18))]).sort()
        self.managers_list  = list(NAME_TO_MANAGER_USERNAME.keys()).sort()
        self.positions_list = list(["QB", "RB", "WR", "TE", "K", "DEF"])

        self.growing_years_list     = list()
        self.growing_weeks_list     = list()
        self.growing_managers_list  = list()
        self.growing_positions_list = list()

        self.year      = None
        self.week      = None
        self.manager   = None
        self.player    = None
        self.position  = None

        self._parse_arg(arg1)
        self._parse_arg(arg2)
        self._parse_arg(arg3)
        self._parse_arg(arg4)

        self._get_function_id()

        self.done = False

        # Mapping of function IDs to their corresponding methods
        # Note: week cannot be used as a filter without a year selected
        self.function_mapping = {
            0:  self._none_selected,
            1:  self._pos_selected,
            2:  self._mgr_selected,
            3:  self._mgr_pos_selected,
          # 4:  self._wk_selected,              (not implemented)
          # 5:  self._wk_pos_selected,          (not implemented)
          # 6:  self._wk_mgr_selected,          (not implemented)
          # 7:  self._wk_mgr_pos_selected,      (not implemented)
            8:  self._yr_selected,
            9:  self._yr_pos_selected,
            10: self._yr_mgr_selected,
            11: self._yr_mgr_pos_selected,
            12: self._yr_wk_selected,
            13: self._yr_wk_pos_selected,
            14: self._yr_wk_mgr_selected,
            15: self._yr_wk_mgr_pos_selected,
            16: self._plyr_selected,
            17: self._plyr_pos_selected,
            18: self._plyr_mgr_selected,
            19: self._plyr_mgr_pos_selected,
          # 20: self._plyr_wk_selected,         (not implemented)
          # 21: self._plyr_wk_pos_selected,     (not implemented)
          # 22: self._plyr_wk_mgr_selected,     (not implemented)
          # 23: self._plyr_wk_mgr_pos_selected, (not implemented)
            24: self._plyr_yr_selected,
            25: self._plyr_yr_pos_selected,
            26: self._plyr_yr_mgr_selected,
            27: self._plyr_yr_mgr_pos_selected,
            28: self._plyr_yr_wk_selected,
            29: self._plyr_yr_wk_pos_selected,
            30: self._plyr_yr_wk_mgr_selected,
            31: self._all_selected
        }
    
    # ----------------------------------------
    # ---------- Internal Functions ----------
    # ----------------------------------------
    def _year_selected(self):
        return False if self.year == None else True
    
    def _week_selected(self):
        return False if self.week == None else True
    
    def _manager_selected(self):
        return False if self.manager == None else True
    
    def _player_selected(self):
        return False if self.player == None else True
    
    def _position_selected(self):
        return False if self.position == None else True
        
    def _parse_arg(self, arg : str):
        
        if arg == None:
            return

        if isinstance(arg, int) or arg.isnumeric():
            arg = int(arg)
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if self.year.selected():
                    raise ValueError("Multiple year arguments provided.")
                self.year = str(arg)
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if self.week.selected():
                    raise ValueError("Multiple week arguments provided.")
                self.week = str(arg)
                if self._week_selected and not self._year_selected():
                    raise ValueError("Year must be selected before selecting a week.")
            
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if self.manager.selected():
                    raise ValueError("Multiple manager arguments provided.")
                self.manager = arg
            
            # Check if arg is a player
            elif arg.replace("_", " ").replace("%27", "'") in PLAYERS_DATA:
                
                if self.player.selected():
                    raise ValueError("Multiple player arguments provided.")
                self.player = arg
            
            elif arg in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if self.position.selected():
                    raise ValueError("Multiple position arguments provided.")
                self.position = arg
            
            else:
                raise ValueError(f"Unrecognized argument: {arg}")
                
    def _get_function_id(self):
        func_id = 0
        if self._player_selected():
            func_id += 16
        if self._year_selected():
            func_id += 8
        if self._week_selected():
            func_id += 4
        if self._manager_selected():
            func_id += 2
        if self._position_selected():
            func_id += 1
        
        self.func_id = func_id
    
    def _add_to_vaild_options(self, value : str, filter1 : str, filter2 : str = None, filter3 : str = None, filter4 : str = None):
        
        growing_filter1_list = getattr(self, f"growing_{filter1}s_list")
        filter1_list         = getattr(self, f"{filter1}s_list")

        if value not in filter1_list:
            growing_filter1_list.append(value)

            setattr(self, f"growing_{filter1}s_list", growing_filter1_list)

            if growing_filter1_list.sort() != filter1_list.sort():
                return

            if filter2 != None:
                growing_filter2_list = getattr(self, f"growing_{filter2}s_list")
                filter2_list         = getattr(self, f"{filter2}s_list")
                
                if growing_filter2_list.sort() != filter2_list.sort():
                    return
                
                if filter3 != None:
                    growing_filter3_list = getattr(self, f"growing_{filter3}s_list")
                    filter3_list         = getattr(self, f"{filter3}s_list")
                
                    if growing_filter3_list.sort() != filter3_list.sort():
                        return
                    
                    if filter4 != None:
                        growing_filter4_list = getattr(self, f"growing_{filter4}s_list")
                        filter4_list         = getattr(self, f"{filter4}s_list")
                        
                        if growing_filter4_list.sort() != filter4_list.sort():
                            return
                        else:
                            self.done = True
                    else:
                        self.done = True
                else:
                    self.done = True
            else:
                self.done = True
    

    # -----------------------------------------
    # ---------- Public Functions--------------
    # -----------------------------------------
    def get_valid_options(self) -> dict:
        """
        Returns the valid options based on the current filters.
        """
        return {
            "years"    : self.years_list.sort(),
            "weeks"    : self.weeks_list.sort(),
            "managers" : self.managers_list.sort(),
            "positions": self.positions_list
        }


    """
    Note: week cannot be used as a filter without a year selected
    ----------------------------------------------------------------------
    || plyr | yr  | wk  | mgr | pos || num |             func           ||
    ----------------------------------------------------------------------
    ||  No  | No  | No  | No  | No  ||  0  | none_selected()            ||
    ||  No  | No  | No  | No  | Yes ||  1  | pos_selected()             ||
    ||  No  | No  | No  | Yes | No  ||  2  | mgr_selected()             ||
    ||  No  | No  | No  | Yes | Yes ||  3  | mgr_pos_selected()         ||
    **************************************************************************************
    ||  No  | No  | Yes | No  | No  ||  4  | wk_selected()              || not implemented
    ||  No  | No  | Yes | No  | Yes ||  5  | wk_pos_selected()          || not implemented
    ||  No  | No  | Yes | Yes | No  ||  6  | wk_mgr_selected()          || not implemented
    ||  No  | No  | Yes | Yes | Yes ||  7  | wk_mgr_pos_selected()      || not implemented
    **************************************************************************************
    ||  No  | Yes | No  | No  | No  ||  8  | yr_selected()              ||
    ||  No  | Yes | No  | No  | Yes ||  9  | yr_pos_selected()          ||
    ||  No  | Yes | No  | Yes | No  ||  10 | yr_mgr_selected()          ||
    ||  No  | Yes | No  | Yes | Yes ||  11 | yr_mgr_pos_selected()      ||
    ||  No  | Yes | Yes | No  | No  ||  12 | yr_wk_selected()           ||
    ||  No  | Yes | Yes | No  | Yes ||  13 | yr_wk_pos_selected()       ||
    ||  No  | Yes | Yes | Yes | No  ||  14 | yr_wk_mgr_selected()       ||
    ||  No  | Yes | Yes | Yes | Yes ||  15 | yr_wk_mgr_pos_selected()   ||
    ||  Yes | No  | No  | No  | No  ||  16 | plyr_selected()            ||
    ||  Yes | No  | No  | No  | Yes ||  17 | plyr_pos_selected()        ||
    ||  Yes | No  | No  | Yes | No  ||  18 | plyr_mgr_selected()        ||
    ||  Yes | No  | No  | Yes | Yes ||  19 | plyr_mgr_pos_selected()    ||
    **************************************************************************************
    ||  Yes | No  | Yes | No  | No  ||  20 | plyr_wk_selected()         || not implemented
    ||  Yes | No  | Yes | No  | Yes ||  21 | plyr_wk_pos_selected()     || not implemented
    ||  Yes | No  | Yes | Yes | No  ||  22 | plyr_wk_mgr_selected()     || not implemented
    ||  Yes | No  | Yes | Yes | Yes ||  23 | plyr_wk_mgr_pos_selected() || not implemented
    **************************************************************************************
    ||  Yes | Yes | No  | No  | No  ||  24 | plyr_yr_selected()         ||
    ||  Yes | Yes | No  | No  | Yes ||  25 | plyr_yr_pos_selected()     ||
    ||  Yes | Yes | No  | Yes | No  ||  26 | plyr_yr_mgr_selected()     ||
    ||  Yes | Yes | No  | Yes | Yes ||  27 | plyr_yr_mgr_pos_selected() ||
    ||  Yes | Yes | Yes | No  | No  ||  28 | plyr_yr_wk_selected()      ||
    ||  Yes | Yes | Yes | No  | Yes ||  29 | plyr_yr_wk_pos_selected()  ||
    ||  Yes | Yes | Yes | Yes | No  ||  30 | plyr_yr_wk_mgr_selected()  ||
    ||  Yes | Yes | Yes | Yes | Yes ||  31 | all_selected()             ||
    ----------------------------------------------------------------------
    """
    # ------------------------------------
    # ---------- Function Stubs ----------
    # ------------------------------------
    # 0
    def _none_selected(self):
        return
    

    # 1
    def _pos_selected(self):
        
        for year in self.years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self.position not in data.get("positions", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "manager")
            if self.done:
                break
            
            for week in self.weeks_list:
                
                if self.position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_vaild_options(week, "week", "manager")
                if self.done:
                    break
                
                for manager in self.managers_list:
                    if self.position in data.get(week, {}).get("managers", {}).get(manager, []):
                        self._add_to_vaild_options(manager, "manager")
                        if self.done:
                            break
                if self.done:
                    break
            if self.done:
                break
        
        self.years_list    = copy.deepcopy(self.growing_years_list)
        self.weeks_list    = copy.deepcopy(self.growing_weeks_list)
        self.managers_list = copy.deepcopy(self.growing_managers_list)
    
    
    # 2
    def _mgr_selected(self):
        
        for year in self.years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self.manager not in data.get("managers", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "position")
            if self.done:
                break
            
            for week in data.get("weeks", []):
                
                if self.manager not in data.get(week, {}).get("managers", []):
                    continue
                self._add_to_vaild_options(week, "week", "position")
                if self.done:
                    break
                
                for position in self.positions_list:
                    if position in data.get(week, {}).get("managers", {}).get(self.manager, []):
                        self._add_to_vaild_options(position, "position")
                        if self.done:
                            break
                if self.done:
                    break
            if self.done:
                break
            
        self.years_list     = copy.deepcopy(self.growing_years_list)
        self.weeks_list     = copy.deepcopy(self.growing_weeks_list)
        self.positions_list = copy.deepcopy(self.growing_positions_list)
    

    # 3
    def _mgr_pos_selected(self):
        for year in self.years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self.manager not in data.get("managers", []):
                continue
            if self.position not in data.get("positions", []):
                continue
            self._add_to_vaild_options(year, "year", "week")
            if self.done:
                break
            
            for week in self.weeks_list:
                
                if self.manager not in data.get(week, {}).get("managers", []):
                    continue
                if self.position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_vaild_options(week, "week")
                if self.done:
                    break
            if self.done:
                break
        
        self.years_list = copy.deepcopy(self.growing_years_list)
        self.weeks_list = copy.deepcopy(self.growing_weeks_list)
    

    # 8
    def _yr_selected(self):
        
        data = VALID_OPTIONS_CACHE.get(self.year, {})
        self.growing_managers_list  = copy.deepcopy(list(data.get("managers", [])))
        self.growing_positions_list = copy.deepcopy(list(data.get("positions", [])))
        self.growing_weeks_list     = copy.deepcopy(list(data.get("weeks", [])))
                
    # 9
    def _yr_pos_selected(self):
        
        data = VALID_OPTIONS_CACHE.get(self.year, {})

        eval_weeks_list    = data.get("weeks", [])
        eval_managers_list = data.get("managers", [])
        
        for week in eval_weeks_list:
            
            if self.position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_vaild_options(week, "week", "manager")
            if self.done:
                break
            
            for manager in eval_managers_list:
                if self.position in data.get(week, {}).get(manager, {}).get("positions", []):
                    self._add_to_vaild_options(manager, "manager")
                    if self.done:
                        break
            if self.done:
                break
        
        self.weeks_list    = copy.deepcopy(self.growing_weeks_list)
        self.managers_list = copy.deepcopy(self.growing_managers_list)
    
    # 10
    def _yr_mgr_selected(self):
        
        data = VALID_OPTIONS_CACHE.get(self.year, {})

        eval_weeks_list    = data.get("weeks", [])
        eval_positions_list = data.get("positions", [])
        
        for week in eval_weeks_list:
            
            if self.manager not in data.get(week, {}).get("managers", []):
                continue
            self._add_to_vaild_options(week, "week", "position")
            if self.done:
                break
            
            for position in eval_positions_list:
                if position in data.get(week, {}).get(self.manager, {}).get("positions", []):
                    self._add_to_vaild_options(position, "position")
                    if self.done:
                        break
            if self.done:
                break
        
        self.weeks_list     = copy.deepcopy(self.growing_weeks_list)
        self.positions_list = copy.deepcopy(self.growing_positions_list)