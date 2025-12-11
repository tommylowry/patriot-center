import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache

VALID_OPTIONS_CACHE = fetch_valid_options_cache()
PLAYERS_DATA = fetch_players()

class ValidOptionsService:
    def __init__(
        self,
        arg1: str | None,
        arg2: str | None,
        arg3: str | None,
        arg4: str | None
    ):
        
        
        self._years_list     = list(str(year) for year in LEAGUE_IDS.keys())
        self._weeks_list     = list(str(week) for week in range(1, 18))
        self._managers_list  = list(NAME_TO_MANAGER_USERNAME.keys())
        self._positions_list = list(["QB", "RB", "WR", "TE", "K", "DEF"])

        self._growing_years_list     = list()
        self._growing_weeks_list     = list()
        self._growing_managers_list  = list()
        self._growing_positions_list = list()

        self._year      = None
        self._week      = None
        self._manager   = None
        self._player    = None
        self._position  = None

        self._parse_arg(arg1)
        self._parse_arg(arg2)
        self._parse_arg(arg3)
        self._parse_arg(arg4)
        self._check_year_and_week()

        self._done = False
        self._player_filtered = False

        # Mapping of function IDs to their corresponding methods
        # [4-7], [20-23] Note: week cannot be used as a filter without a year selected
        # [31] Note; only 4 filters can be applied at once

        self._function_mapping = {
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
            30: self._plyr_yr_wk_mgr_selected
          # 31: self._all_selected              (not implemented)
        }

        self._position_bit = 1
        self._manager_bit  = 2
        self._week_bit     = 4
        self._year_bit     = 8
        self._player_bit   = 16

        self._get_function_id()

        self._function_mapping[self._func_id]()
    
    # ----------------------------------------
    # ---------- Internal Functions ----------
    # ----------------------------------------
    def _year_selected(self) -> bool:
        return False if self._year == None else True
    
    def _week_selected(self) -> bool:
        return False if self._week == None else True
    
    def _manager_selected(self) -> bool:
        return False if self._manager == None else True
    
    def _player_selected(self) -> bool:
        return False if self._player == None else True
    
    def _position_selected(self) -> bool:
        return False if self._position == None else True
        
    def _parse_arg(self, arg : str | None):
        
        if arg == None:
            return

        if isinstance(arg, int) or arg.isnumeric():
            arg = int(arg)
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if self._year_selected():
                    raise ValueError("Multiple year arguments provided.")
                self._year = str(arg)
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if self._week_selected():
                    raise ValueError("Multiple week arguments provided.")
                self._week = str(arg)
            
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if self._manager_selected():
                    raise ValueError("Multiple manager arguments provided.")
                self._manager = arg
            
            # Check if arg is a player
            elif arg.replace("_", " ").replace("%27", "'") in PLAYERS_DATA:
                
                if self._player_selected():
                    raise ValueError("Multiple player arguments provided.")
                self._player = arg.replace("_", " ").replace("%27", "'")
            
            elif arg in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if self._position_selected():
                    raise ValueError("Multiple position arguments provided.")
                self._position = arg

            else:
                raise ValueError(f"Unrecognized argument: {arg}")
            
    def _check_year_and_week(self):
        if self._week_selected() and not self._year_selected():
            raise ValueError("Week filter cannot be applied without a Year filter.")

    def _get_function_id(self):

        self._func_id = 0
        if self._position_selected():
            self._func_id += self._position_bit
        if self._manager_selected():
            self._func_id += self._manager_bit
        if self._week_selected():
            self._func_id += self._week_bit
        if self._year_selected():
            self._func_id += self._year_bit
        if self._player_selected():
            self._func_id += self._player_bit
    
    def _add_to_vaild_options(
            self,
            value : str,
            filter1 : str,
            filter2 : str | None = None, 
            filter3 : str | None = None,
            filter4 : str | None = None
        ):
        
        growing_filter1_list = getattr(self, f"_growing_{filter1}s_list")
        filter1_list         = getattr(self, f"_{filter1}s_list")

        if value not in growing_filter1_list:
            growing_filter1_list.append(value)

            setattr(self, f"_growing_{filter1}s_list", growing_filter1_list)

            if sorted(growing_filter1_list) != sorted(filter1_list):
                self._done = False
                return

            if filter2 != None:
                growing_filter2_list = getattr(self, f"_growing_{filter2}s_list")
                filter2_list         = getattr(self, f"_{filter2}s_list")
                
                if sorted(growing_filter2_list) != sorted(filter2_list):
                    self._done = False
                    return
                
                if filter3 != None:
                    growing_filter3_list = getattr(self, f"_growing_{filter3}s_list")
                    filter3_list         = getattr(self, f"_{filter3}s_list")
                
                    if sorted(growing_filter3_list) != sorted(filter3_list):
                        self._done = False
                        return
                    
                    if filter4 != None:
                        growing_filter4_list = getattr(self, f"_growing_{filter4}s_list")
                        filter4_list         = getattr(self, f"_{filter4}s_list")
                        
                        if sorted(growing_filter4_list) != sorted(filter4_list):
                            self._done = False
                            return
                        else:
                            self._done = True
                    else:
                        self._done = True
                else:
                    self._done = True
            else:
                self._done = True
    
    def _reset_growing_lists(self):
        self._done = False
        self._growing_years_list     = list()
        self._growing_weeks_list     = list()
        self._growing_managers_list  = list()
        self._growing_positions_list = list()
    
    def _call_new_function(self, bit: int):
        
        self._reset_growing_lists()
        
        if bit not in self._function_mapping:
            raise ValueError(f"Function for bit {bit} not implemented.")
        
        self._function_mapping[bit]()
        
        self._reset_growing_lists()


    # -----------------------------------------
    # ---------- Public Functions--------------
    # -----------------------------------------
    def get_valid_options(self) -> dict:
        """
        Returns the valid options based on the current filters.
        """

        # Ensure weeks are sorted numerically
        self._weeks_list = [int(week) for week in self._weeks_list]
        self._weeks_list = sorted(self._weeks_list)
        self._weeks_list = [str(week) for week in self._weeks_list]
        
        return {
            "years"    : sorted(self._years_list),
            "weeks"    : self._weeks_list,
            "managers" : sorted(self._managers_list),
            "positions": self._positions_list
        }


    # ------------------------------------
    # ---------- Function Stubs ----------
    # ------------------------------------


    """
    Note: week cannot be used as a filter without a year selected
    Note: only 4 filters can be applied at once, so all 5 selected is not implemented
    -----------------------------------------------------------------------
    || plyr | yr  | wk  | mgr | pos || num |             func            ||
    -----------------------------------------------------------------------
    ||  No  | No  | No  | No  | No  ||  0  | _none_selected()            ||
    ||  No  | No  | No  | No  | Yes ||  1  | _pos_selected()             ||
    ||  No  | No  | No  | Yes | No  ||  2  | _mgr_selected()             ||
    ||  No  | No  | No  | Yes | Yes ||  3  | _mgr_pos_selected()         ||
    ***************************************************************************************
    ||  No  | No  | Yes | No  | No  ||  4  | _wk_selected()              || not implemented
    ||  No  | No  | Yes | No  | Yes ||  5  | _wk_pos_selected()          || not implemented
    ||  No  | No  | Yes | Yes | No  ||  6  | _wk_mgr_selected()          || not implemented
    ||  No  | No  | Yes | Yes | Yes ||  7  | _wk_mgr_pos_selected()      || not implemented
    ***************************************************************************************
    ||  No  | Yes | No  | No  | No  ||  8  | _yr_selected()              ||
    ||  No  | Yes | No  | No  | Yes ||  9  | _yr_pos_selected()          ||
    ||  No  | Yes | No  | Yes | No  ||  10 | _yr_mgr_selected()          ||
    ||  No  | Yes | No  | Yes | Yes ||  11 | _yr_mgr_pos_selected()      ||
    ||  No  | Yes | Yes | No  | No  ||  12 | _yr_wk_selected()           ||
    ||  No  | Yes | Yes | No  | Yes ||  13 | _yr_wk_pos_selected()       ||
    ||  No  | Yes | Yes | Yes | No  ||  14 | _yr_wk_mgr_selected()       ||
    ||  No  | Yes | Yes | Yes | Yes ||  15 | _yr_wk_mgr_pos_selected()   ||
    ||  Yes | No  | No  | No  | No  ||  16 | _plyr_selected()            ||
    ||  Yes | No  | No  | No  | Yes ||  17 | _plyr_pos_selected()        ||
    ||  Yes | No  | No  | Yes | No  ||  18 | _plyr_mgr_selected()        ||
    ||  Yes | No  | No  | Yes | Yes ||  19 | _plyr_mgr_pos_selected()    ||
    ***************************************************************************************
    ||  Yes | No  | Yes | No  | No  ||  20 | _plyr_wk_selected()         || not implemented
    ||  Yes | No  | Yes | No  | Yes ||  21 | _plyr_wk_pos_selected()     || not implemented
    ||  Yes | No  | Yes | Yes | No  ||  22 | _plyr_wk_mgr_selected()     || not implemented
    ||  Yes | No  | Yes | Yes | Yes ||  23 | _plyr_wk_mgr_pos_selected() || not implemented
    ***************************************************************************************
    ||  Yes | Yes | No  | No  | No  ||  24 | _plyr_yr_selected()         ||
    ||  Yes | Yes | No  | No  | Yes ||  25 | _plyr_yr_pos_selected()     ||
    ||  Yes | Yes | No  | Yes | No  ||  26 | _plyr_yr_mgr_selected()     ||
    ||  Yes | Yes | No  | Yes | Yes ||  27 | _plyr_yr_mgr_pos_selected() ||
    ||  Yes | Yes | Yes | No  | No  ||  28 | _plyr_yr_wk_selected()      ||
    ||  Yes | Yes | Yes | No  | Yes ||  29 | _plyr_yr_wk_pos_selected()  ||
    ||  Yes | Yes | Yes | Yes | No  ||  30 | _plyr_yr_wk_mgr_selected()  ||
    ***************************************************************************************
    ||  Yes | Yes | Yes | Yes | Yes ||  31 | _all_selected()             || not implemented
    ***************************************************************************************
    -----------------------------------------------------------------------
    """


    # 0
    def _none_selected(self):
        return
    
    # 1
    def _pos_selected(self):

        # Year, Week, and Manager options that have the selected Position
        for year in self._years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self._position not in data.get("positions", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "manager")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "manager")
                if self._done:
                    break
                
                for manager in self._managers_list:
                    if self._position in data.get(week, {}).get(manager, {}).get("positions", []):
                        self._add_to_vaild_options(manager, "manager", "year", "week")
                        if self._done:
                            break
            
                if self._done:
                    break
            if self._done:
                break
        
        self._years_list    = copy.deepcopy(self._growing_years_list)
        self._weeks_list    = copy.deepcopy(self._growing_weeks_list)
        self._managers_list = copy.deepcopy(self._growing_managers_list)
    
    # 2
    def _mgr_selected(self):

        # Year, Week, and Position options that have the selected Manager
        for year in self._years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self._manager not in data.get("managers", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "position")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._manager not in data.get(week, {}).get("managers", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "position")
                if self._done:
                    break
                
                for position in self._positions_list:
                    if position in data.get(week, {}).get(self._manager, {}).get("positions", []):
                        self._add_to_vaild_options(position, "position", "year", "week")
                        if self._done:
                            break
            
                if self._done:
                    break
            if self._done:
                break
            
        self._years_list     = copy.deepcopy(self._growing_years_list)
        self._weeks_list     = copy.deepcopy(self._growing_weeks_list)
        self._positions_list = copy.deepcopy(self._growing_positions_list)
    
    # 3
    def _mgr_pos_selected(self):

        # Year and Week options that have the selected Manager and Position
        for year in self._years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self._manager not in data.get("managers", []):
                continue
            if self._position not in data.get("positions", []):
                continue
            self._add_to_vaild_options(year, "year", "week")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._manager not in data.get(week, {}).get("managers", []):
                    continue
                if self._position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_vaild_options(week, "week", "year")
                if self._done:
                    break
            
            if self._done:
                break
        
        self._years_list = copy.deepcopy(self._growing_years_list)
        self._weeks_list = copy.deepcopy(self._growing_weeks_list)

        # Within the valid Years and Weeks: Get the Manager options that have the selected Position
        self._call_new_function(self._position_bit)

        # Within the valid Years and Weeks: Get the Position options that have the selected Manager
        self._call_new_function(self._manager_bit)
    
    # 8
    def _yr_selected(self):

        data = VALID_OPTIONS_CACHE.get(self._year, {})

        # Weeks, Managers, and Positions for the selected Year
        for week in self._weeks_list:
            if week in data.get("weeks", []):
                self._add_to_vaild_options(week, "week")
        for manager in self._managers_list:
            if manager in data.get("managers", []):
                self._add_to_vaild_options(manager, "manager")
        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_vaild_options(position, "position")

        self._weeks_list     = copy.deepcopy(self._growing_weeks_list)
        self._managers_list  = copy.deepcopy(self._growing_managers_list)
        self._positions_list = copy.deepcopy(self._growing_positions_list)
                
    # 9
    def _yr_pos_selected(self):

        # Weeks and Managers options that have the selected Position for the selected Year
        data = VALID_OPTIONS_CACHE.get(self._year, {})

        for week in self._weeks_list:
            
            if self._position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_vaild_options(week, "week", "manager")
            if self._done:
                break
            
            for manager in self._managers_list:
                if self._position in data.get(week, {}).get(manager, {}).get("positions", []):
                    self._add_to_vaild_options(manager, "manager", "week")
                    if self._done:
                        break
            
            if self._done:
                break
        
        self._weeks_list    = copy.deepcopy(self._growing_weeks_list)
        self._managers_list = copy.deepcopy(self._growing_managers_list)

        # Within the valid Weeks and Managers: Get the Position options that have the selected Year
        self._call_new_function(self._year_bit)

        # Within the valid Weeks and Managers: Get the Year options that have the selected Position
        self._call_new_function(self._position_bit)
    
    # 10
    def _yr_mgr_selected(self):

        # Weeks and Positions options that have the selected Manager for the selected Year
        data = VALID_OPTIONS_CACHE.get(self._year, {})

        for week in self._weeks_list:
            
            if self._manager not in data.get(week, {}).get("managers", []):
                continue
            self._add_to_vaild_options(week, "week", "position")
            if self._done:
                break
            
            for position in self._positions_list:
                if position in data.get(week, {}).get(self._manager, {}).get("positions", []):
                    self._add_to_vaild_options(position, "position", "week")
                    if self._done:
                        break
            
            if self._done:
                break
        
        self._weeks_list     = copy.deepcopy(self._growing_weeks_list)
        self._positions_list = copy.deepcopy(self._growing_positions_list)

        # Within the valid Weeks and Positions: Get the Manager options that have the selected Year
        self._call_new_function(self._year_bit)

        # Within the valid Weeks and Positions: Get the Year options that have the selected Manager
        self._call_new_function(self._manager_bit)
    
    # 11
    def _yr_mgr_pos_selected(self):

        # Weeks options that have the selected Manager and Position for the selected Year
        data = VALID_OPTIONS_CACHE.get(self._year, {})

        for week in self._weeks_list:
            
            if self._manager not in data.get(week, {}).get("managers", []):
                continue
            if self._position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_vaild_options(week, "week")
            if self._done:
                break
        
        self._weeks_list = copy.deepcopy(self._growing_weeks_list)

        # Within the valid Weeks: Get the Manager options that have the selected Year and Position
        self._call_new_function(self._year_bit + self._position_bit)

        # Within the valid Weeks: Get the Position options that have the selected Year and Manager
        self._call_new_function(self._year_bit + self._manager_bit)

        # Within the valid Weeks: Get the Year options that have the selected Manager and Position
        self._call_new_function(self._manager_bit + self._position_bit)

    # 12
    def _yr_wk_selected(self):

        # Managers and Positions for the selected Year and Week
        data = VALID_OPTIONS_CACHE.get(self._year, {}).get(self._week, {})

        # Get the vaid Positions and Managers for the selected Year and Week
        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_vaild_options(position, "position")
                if self._done:
                    break

        for manager in self._managers_list:
            if manager in data.get("managers", []):
                self._add_to_vaild_options(manager, "manager")
                if self._done:
                    break

        self._managers_list  = copy.deepcopy(self._growing_managers_list)
        self._positions_list = copy.deepcopy(self._growing_positions_list)

        # Within the valid Managers and Positions: Get the Week options that have the selected Year
        self._call_new_function(self._year_bit)

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 13
    def _yr_wk_pos_selected(self):

        # Managers options that have the selected Position, Year, and Week
        data = VALID_OPTIONS_CACHE.get(self._year, {}).get(self._week, {})

        for manager in self._managers_list:
            if self._position in data.get(manager, {}).get("positions", []):
                self._add_to_vaild_options(manager, "manager")
                if self._done:
                    break

        self._managers_list = copy.deepcopy(self._growing_managers_list)

        # Get the Positions list for the selected year and week
        self._call_new_function(self._year_bit + self._week_bit)

        # Get the Weeks list for the selected year and position
        self._call_new_function(self._year_bit + self._position_bit)

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 14
    def _yr_wk_mgr_selected(self):

        # Set positions list for the selected year, week, and manager
        data = VALID_OPTIONS_CACHE.get(self._year, {}).get(self._week, {}).get(self._manager, {})

        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_vaild_options(position, "position")
                if self._done:
                    break

        self._positions_list = copy.deepcopy(self._growing_positions_list)

        # Within the valid Positions: Get the Manager options that have the selected Year and Week
        self._call_new_function(self._year_bit + self._week_bit)

        # Within the valid Positions: Get the Week options that have the selected Year and Manager
        self._call_new_function(self._year_bit + self._manager_bit)

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 15
    def _yr_wk_mgr_pos_selected(self):

        # Set Weeks list for the selected year, manager, and position
        self._call_new_function(self._year_bit + self._manager_bit + self._position_bit)

        # Set Managers list for the selected year, week, and position
        self._call_new_function(self._year_bit + self._week_bit + self._position_bit)

        # Set Positions list for the selected year, week, and manager
        self._call_new_function(self._year_bit + self._week_bit + self._manager_bit)

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 16
    def _plyr_selected(self):

        if self._player_filtered:
            return
        self._player_filtered = True

        # Position can only be the position of the player
        self._positions_list = list([PLAYERS_DATA[self._player]["position"]])

        for year in self._years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self._player not in data.get("players", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "manager", "position")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._player not in data.get(week, {}).get("players", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "manager", "position")
                if self._done:
                    break
                
                for manager in self._managers_list:
                    
                    if self._player in data.get(week, {}).get(manager, {}).get("players", []):
                        self._add_to_vaild_options(manager, "manager", "year", "week", "position")
                        if self._done:
                            break
                
                if self._done:
                    break
            if self._done:
                break
        
        self._years_list     = copy.deepcopy(self._growing_years_list)
        self._weeks_list     = copy.deepcopy(self._growing_weeks_list)
        self._managers_list  = copy.deepcopy(self._growing_managers_list)
    
    # 17
    def _plyr_pos_selected(self):

        # Position can only be the position of the player
        self._call_new_function(self._player_bit)
    
    # 18
    def _plyr_mgr_selected(self):

        # Filter out everything that does not have the player
        self._call_new_function(self._player_bit)

        # Get the years and weeks for the selected player (position is already set)
        for year in self._years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})

            for week in self._weeks_list:

                if self._player in data.get(week, {}).get(self._manager, {}).get("players", []):
                    self._add_to_vaild_options(year, "year", "week", "position")
                    self._add_to_vaild_options(week, "week", "year", "position")
                    if self._done:
                        break
                
            if self._done:
                break
        
        self._years_list = copy.deepcopy(self._growing_years_list)
        self._weeks_list = copy.deepcopy(self._growing_weeks_list)
    
    # 19
    def _plyr_mgr_pos_selected(self):
        
        # Position can only be the position of the player
        self._call_new_function(self._player_bit + self._manager_bit)

    # 24
    def _plyr_yr_selected(self):

        # filter out everything that does not have the player and shorten the lists to loop through
        self._call_new_function(self._player_bit)

        # Get the weeks and managers for the selected year and player (position is already set)
        data = VALID_OPTIONS_CACHE.get(self._year, {})

        for week in self._weeks_list:

            if self._player not in data.get(week, {}).get("players", []):
                continue

            for manager in self._managers_list:

                if self._player in data.get(week, {}).get(manager, {}).get("players", []):
                    self._add_to_vaild_options(week, "week", "manager")
                    self._add_to_vaild_options(manager, "manager", "week")
                    if self._done:
                        break
            
            if self._done:
                break
        
        self._managers_list = copy.deepcopy(self._growing_managers_list)
        self._weeks_list    = copy.deepcopy(self._growing_weeks_list)

    # 25
    def _plyr_yr_pos_selected(self):

        # Get the weeks and managers for the selected year and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit)
    
    # 26
    def _plyr_yr_mgr_selected(self):

        # Get all the options for the selected year and player (position is already set)
        self._call_new_function(self._player_bit)

        # Get the Managers options that have the selected Year and Player
        self._call_new_function(self._player_bit + self._year_bit)

        # Get the Year options that have the selected Manager and Player
        self._call_new_function(self._player_bit + self._manager_bit)


        # Get the Weeks options that have the selected Year, Manager and Player
        data = VALID_OPTIONS_CACHE.get(self._year, {})

        for week in self._weeks_list:
            if self._player in data.get(week, {}).get(self._manager, {}).get("players", []):
                self._add_to_vaild_options(week, "week")
                if self._done:
                    break
        
        self._weeks_list = copy.deepcopy(self._growing_weeks_list)
        
    # 27
    def _plyr_yr_mgr_pos_selected(self):
        
        # get the weeks for the selected year, manager, and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit + self._manager_bit)
        
    # 28
    def _plyr_yr_wk_selected(self):

        # filter out everything that does not have the player and shorten the lists to loop through
        self._call_new_function(self._player_bit)
        
        # get the managers for the selected year, week, and player (position is already set)
        data = VALID_OPTIONS_CACHE.get(self._year, {}).get(self._week, {})

        for manager in self._managers_list:
            if self._player in data.get(manager, {}).get("players", []):
                self._add_to_vaild_options(manager, "manager")
                if self._done:
                    break
        
        self._managers_list = copy.deepcopy(self._growing_managers_list)


        # Within the valid Managers: Get the Weeks options that have the selected Year and Player
        self._plyr_yr_selected()

        # (No need to get Year options for Week as Week cannot be selected without Year)
    
    # 29
    def _plyr_yr_wk_pos_selected(self):

        # get the managers for the selected year, week, and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit + self._week_bit)
    
    # 30
    def _plyr_yr_wk_mgr_selected(self):

        # Get the Years for the selected manager and player
        self._call_new_function(self._player_bit + self._manager_bit)

        # Get the Weeks for the selected year, manager, and player
        self._call_new_function(self._player_bit + self._manager_bit + self._year_bit)

        # In a given year and week, the manager can only be the selected manager
        self._managers_list = list([self._manager])