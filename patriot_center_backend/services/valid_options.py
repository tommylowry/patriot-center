import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache

VALID_OPTIONS_CACHE = fetch_valid_options_cache()
PLAYERS_DATA = fetch_players()

class ValidOptionsService:
    def __init__(self,
                 last_added: str | None,
                 arg1:       str | None,
                 arg2:       str | None,
                 arg3:       str | None,
                 arg4:       str | None):
        
        
        self.years_list     = list(str(year) for year in LEAGUE_IDS.keys())
        self.weeks_list     = list(str(week) for week in range(1, 18))
        self.managers_list  = list(NAME_TO_MANAGER_USERNAME.keys())
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

        self._parse_last_updated(last_added)

        self.done = False

        # Mapping of function IDs to their corresponding methods
        # [4-7], [20-23] Note: week cannot be used as a filter without a year selected
        # [31] Note; only 4 filters can be applied at once

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
            30: self._plyr_yr_wk_mgr_selected
          # 31: self._all_selected              (not implemented)
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
                if self._year_selected():
                    raise ValueError("Multiple year arguments provided.")
                self.year = str(arg)
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if self._week_selected():
                    raise ValueError("Multiple week arguments provided.")
                self.week = str(arg)
                if self._week_selected and not self._year_selected():
                    raise ValueError("Year must be selected before selecting a week.")
            
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if self._manager_selected():
                    raise ValueError("Multiple manager arguments provided.")
                self.manager = arg
            
            # Check if arg is a player
            elif arg.replace("_", " ").replace("%27", "'") in PLAYERS_DATA:
                
                if self._player_selected():
                    raise ValueError("Multiple player arguments provided.")
                self.player = arg
            
            elif arg in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if self._position_selected():
                    raise ValueError("Multiple position arguments provided.")
                self.position = arg
            
            else:
                raise ValueError(f"Unrecognized argument: {arg}")

    def _parse_last_updated(self, last_added: str | None):
        if last_added == None:
            if self.func_id != 0:
                raise ValueError("Last added filter must be provided when filters are applied.")
        
        elif last_added.lower() == "year" or last_added.lower() == "season": # 'year' or 'season' are used interchangeably
            if not self._year_selected():
                raise ValueError("Last added filter is 'year' but no year was selected.")
            self.last_added = "year"
        
        elif last_added.lower() == "week":
            if not self._week_selected():
                raise ValueError("Last added filter is 'week' but no week was selected.")
            self.last_added = "week"
        
        elif last_added.lower() == "manager":
            if not self._manager_selected():
                raise ValueError("Last added filter is 'manager' but no manager was selected.")
            self.last_added = "manager"
        
        elif last_added.lower() == "player":
            if not self._player_selected():
                raise ValueError("Last added filter is 'player' but no player was selected.")
            self.last_added = "player"
        
        elif last_added.lower() == "position":
            if not self._position_selected():
                raise ValueError("Last added filter is 'position' but no position was selected.")
            self.last_added = "position"
        
        else:
            raise ValueError(f"Unrecognized last added filter: {last_added}")

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
    
    def _add_to_vaild_options(self,
                              value : str,
                              filter1 : str,
                              filter2 : str | None = None, 
                              filter3 : str | None = None,
                              filter4 : str | None = None):
        
        growing_filter1_list = getattr(self, f"growing_{filter1}s_list")
        filter1_list         = getattr(self, f"{filter1}s_list")

        if value not in growing_filter1_list:
            growing_filter1_list.append(value)

            setattr(self, f"growing_{filter1}s_list", growing_filter1_list)

            if sorted(growing_filter1_list) != sorted(filter1_list):
                return

            if filter2 != None:
                growing_filter2_list = getattr(self, f"growing_{filter2}s_list")
                filter2_list         = getattr(self, f"{filter2}s_list")
                
                if sorted(growing_filter2_list) != sorted(filter2_list):
                    return
                
                if filter3 != None:
                    growing_filter3_list = getattr(self, f"growing_{filter3}s_list")
                    filter3_list         = getattr(self, f"{filter3}s_list")
                
                    if sorted(growing_filter3_list) != sorted(filter3_list):
                        return
                    
                    if filter4 != None:
                        growing_filter4_list = getattr(self, f"growing_{filter4}s_list")
                        filter4_list         = getattr(self, f"{filter4}s_list")
                        
                        if sorted(growing_filter4_list) != sorted(filter4_list):
                            return
                        else:
                            self.done = True
                    else:
                        self.done = True
                else:
                    self.done = True
            else:
                self.done = True
    
    def _reset_growing_lists(self):
        self.done = False
        self.growing_years_list     = list()
        self.growing_weeks_list     = list()
        self.growing_managers_list  = list()
        self.growing_positions_list = list()

    # -----------------------------------------
    # ---------- Public Functions--------------
    # -----------------------------------------
    def get_valid_options(self) -> dict:
        """
        Returns the valid options based on the current filters.
        """

        self.function_mapping[self.func_id]()

        # Ensure weeks are sorted numerically
        self.weeks_list = [int(week) for week in self.weeks_list]
        self.weeks_list = sorted(self.weeks_list)
        self.weeks_list = [str(week) for week in self.weeks_list]
        
        return {
            "years"    : sorted(self.years_list),
            "weeks"    : self.weeks_list,
            "managers" : sorted(self.managers_list),
            "positions": self.positions_list
        }


    # ------------------------------------
    # ---------- Function Stubs ----------
    # ------------------------------------


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
    ||  Yes | Yes | Yes | Yes | Yes ||  31 | all_selected()             || not implemented
    ----------------------------------------------------------------------
    """


    # 0
    def _none_selected(self):
        return
    
    # 1
    def _pos_selected(self):

        self._reset_growing_lists()

        # Year, Week, and Manager options that have the selected Position
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
                self._add_to_vaild_options(week, "week", "year", "manager")
                if self.done:
                    break
                
                for manager in self.managers_list:
                    if self.position in data.get(week, {}).get(manager, {}).get("positions", []):
                        self._add_to_vaild_options(manager, "manager", "year", "week")
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

        self._reset_growing_lists()

        # Year, Week, and Position options that have the selected Manager
        for year in self.years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self.manager not in data.get("managers", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "position")
            if self.done:
                break
            
            for week in self.weeks_list:
                
                if self.manager not in data.get(week, {}).get("managers", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "position")
                if self.done:
                    break
                
                for position in self.positions_list:
                    if position in data.get(week, {}).get(self.manager, {}).get("positions", []):
                        self._add_to_vaild_options(position, "position", "year", "week")
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
        
        self._reset_growing_lists()

        # Year and Week options that have the selected Manager and Position
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
                self._add_to_vaild_options(week, "week", "year")
                if self.done:
                    break
            
            if self.done:
                break
        
        self.years_list = copy.deepcopy(self.growing_years_list)
        self.weeks_list = copy.deepcopy(self.growing_weeks_list)

        # Within the valid Years and Weeks: Get the Manager options that have the selected Position
        self._pos_selected()

        # Within the valid Years and Weeks: Get the Position options that have the selected Manager
        self._mgr_selected()
    
    # 8
    def _yr_selected(self):

        self._reset_growing_lists()

        data = VALID_OPTIONS_CACHE.get(self.year, {})

        # Weeks, Managers, and Positions for the selected Year
        for week in self.weeks_list:
            if week in data.get("weeks", []):
                self._add_to_vaild_options(week, "week")
        for manager in self.managers_list:
            if manager in data.get("managers", []):
                self._add_to_vaild_options(manager, "manager")
        for position in self.positions_list:
            if position in data.get("positions", []):
                self._add_to_vaild_options(position, "position")

        self.weeks_list     = copy.deepcopy(self.growing_weeks_list)
        self.managers_list  = copy.deepcopy(self.growing_managers_list)
        self.positions_list = copy.deepcopy(self.growing_positions_list)
                
    # 9
    def _yr_pos_selected(self):

        self._reset_growing_lists()

        # Weeks and Managers options that have the selected Position for the selected Year
        data = VALID_OPTIONS_CACHE.get(self.year, {})

        for week in self.weeks_list:
            
            if self.position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_vaild_options(week, "week", "manager")
            if self.done:
                break
            
            for manager in self.managers_list:
                if self.position in data.get(week, {}).get(manager, {}).get("positions", []):
                    self._add_to_vaild_options(manager, "manager", "week")
                    if self.done:
                        break
            
            if self.done:
                break
        
        self.weeks_list    = copy.deepcopy(self.growing_weeks_list)
        self.managers_list = copy.deepcopy(self.growing_managers_list)

        # Within the valid Weeks and Managers: Get the Position options that have the selected Year
        self._yr_selected()

        # Within the valid Weeks and Managers: Get the Year options that have the selected Position
        self._pos_selected()
    
    # 10
    def _yr_mgr_selected(self):

        self._reset_growing_lists()

        # Weeks and Positions options that have the selected Manager for the selected Year
        data = VALID_OPTIONS_CACHE.get(self.year, {})

        for week in self.weeks_list:
            
            if self.manager not in data.get(week, {}).get("managers", []):
                continue
            self._add_to_vaild_options(week, "week", "position")
            if self.done:
                break
            
            for position in self.positions_list:
                if position in data.get(week, {}).get(self.manager, {}).get("positions", []):
                    self._add_to_vaild_options(position, "position", "week")
                    if self.done:
                        break
            
            if self.done:
                break
        
        self.weeks_list     = copy.deepcopy(self.growing_weeks_list)
        self.positions_list = copy.deepcopy(self.growing_positions_list)

        # Within the valid Weeks and Positions: Get the Manager options that have the selected Year
        self._yr_selected()

        # Within the valid Weeks and Positions: Get the Year options that have the selected Manager
        self._mgr_selected()
    
    # 11
    def _yr_mgr_pos_selected(self):

        self._reset_growing_lists()

        # Weeks options that have the selected Manager and Position for the selected Year
        data = VALID_OPTIONS_CACHE.get(self.year, {})

        for week in self.weeks_list:
            
            if self.manager not in data.get(week, {}).get("managers", []):
                continue
            if self.position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_vaild_options(week, "week")
            if self.done:
                break
        
        self.weeks_list = copy.deepcopy(self.growing_weeks_list)

        # Within the valid Weeks: Get the Manager options that have the selected Year and Position
        self._yr_pos_selected()

        # Within the valid Weeks: Get the Position options that have the selected Year and Manager
        self._yr_mgr_selected()

        # Within the valid Weeks: Get the Year options that have the selected Manager and Position
        self._mgr_pos_selected()

    # 12
    def _yr_wk_selected(self):
        
        self._reset_growing_lists()

        # Managers and Positions for the selected Year and Week
        data = VALID_OPTIONS_CACHE.get(self.year, {}).get(self.week, {})

        for manager in self.managers_list:
            if manager in data.get("managers", []):
                for position in self.positions_list:
                    if position in data.get(manager, {}).get("positions", []):
                        self._add_to_vaild_options(manager, "manager", "position")
                        if self.done:
                            break
                        self._add_to_vaild_options(position, "position", "manager")
                        if self.done:
                            break
                if self.done:
                    break

        self.managers_list  = copy.deepcopy(self.growing_managers_list)
        self.positions_list = copy.deepcopy(self.growing_positions_list)

        # Within the valid Managers and Positions: Get the Week options that have the selected Year
        self._yr_selected()

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 13
    def _yr_wk_pos_selected(self):

        self._reset_growing_lists()

        # Managers options that have the selected Position, Year, and Week
        data = VALID_OPTIONS_CACHE.get(self.year, {}).get(self.week, {})

        for manager in self.managers_list:
            if self.position in data.get(manager, {}).get("positions", []):
                self._add_to_vaild_options(manager, "manager")
                if self.done:
                    break

        self.managers_list = copy.deepcopy(self.growing_managers_list)

        # Within the valid Managers: Get the Position options that have the selected Year and Week
        self._yr_wk_selected()

        # Within the valid Managers: Get the Year options that have the selected Week and Position
        self._yr_pos_selected()

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 14
    def _yr_wk_mgr_selected(self):

        self._reset_growing_lists()

        # Set positions list for the selected year, week, and manager
        data = VALID_OPTIONS_CACHE.get(self.year, {}).get(self.week, {}).get(self.manager, {})

        for position in self.positions_list:
            if position in data.get("positions", []):
                self._add_to_vaild_options(position, "position")
                if self.done:
                    break

        self.positions_list = copy.deepcopy(self.growing_positions_list)

        # Within the valid Positions: Get the Manager options that have the selected Year and Week
        self._yr_wk_selected()

        # Within the valid Positions: Get the Week options that have the selected Year and Manager
        self._yr_mgr_selected()

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 15
    def _yr_wk_mgr_pos_selected(self):

        self._reset_growing_lists()

        # Set Weeks list for the selected year, manager, and position
        self._yr_mgr_pos_selected()

        # Set Managers list for the selected year, week, and position
        self._yr_wk_pos_selected()

        # Set Positions list for the selected year, week, and manager
        self._yr_wk_mgr_selected()

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)
    
    # 16
    def _plyr_selected(self):

        self._reset_growing_lists()

        # Position can only be the position of the player
        self.positions_list = list([PLAYERS_DATA[self.player]["position"]])

        for year in self.years_list:
            
            data = VALID_OPTIONS_CACHE.get(year, {})
            
            if self.player not in data.get("players", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "manager", "position")
            if self.done:
                break
            
            eval_weeks_list = data.get("weeks", [])
            for week in eval_weeks_list:
                
                if self.player not in data.get(week, {}).get("players", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "manager", "position")
                if self.done:
                    break
                
                eval_managers_list = data.get(week, {}).get("managers", [])
                for manager in eval_managers_list:
                    
                    if self.player in data.get(week, {}).get(manager, {}).get("players", []):
                        self._add_to_vaild_options(manager, "manager", "year", "week", "position")
                        if self.done:
                            break
                
                if self.done:
                    break
            if self.done:
                break
        
        self.years_list     = copy.deepcopy(self.growing_years_list)
        self.weeks_list     = copy.deepcopy(self.growing_weeks_list)
        self.managers_list  = copy.deepcopy(self.growing_managers_list)
    
    # 17
    def _plyr_pos_selected(self):

        self._reset_growing_lists()

        # Position can only be the position of the player
        self._plyr_selected()
    
    # 18
    def _plyr_mgr_selected(self):

        self._reset_growing_lists()

        # Filter out everything that does not have the player
        self._plyr_selected()

        # Within the valid Years, Weeks, and Positions: Get the Manager options that have the selected Player
        self._mgr_selected()
    
    # 19
    def _plyr_mgr_pos_selected(self):
        
        self._reset_growing_lists()
        
        # Position can only be the position of the player
        self._plyr_mgr_selected()

    # 24
    def _plyr_yr_selected(self):

        # filter out everything that does not have the player and shorten the lists to loop through
        self._plyr_selected()
        
        # Of the valid years that have the player, filter out weeks, managers, and positions
        self._yr_selected

    # 25
    def _plyr_yr_pos_selected(self):

        self._reset_growing_lists()

        # Get the weeks and managers for the selected year and player (position is already set)
        self._plyr_yr_selected()
    
    # 26
    def _plyr_yr_mgr_selected(self):

        self._reset_growing_lists()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._plyr_selected()
        
        # get the weeks for the selected year and player (position is already set)
        self._yr_mgr_selected()
    
    # 27
    def _plyr_yr_mgr_pos_selected(self):
        
        self._reset_growing_lists()
        
        # get the weeks for the selected year, manager, and player (position is already set)
        self._plyr_yr_mgr_selected()
        
    # 28
    def _plyr_yr_wk_selected(self):

        self._reset_growing_lists()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._plyr_selected()
        
        # get the managers for the selected year, week, and player (position is already set)
        self._yr_wk_selected()
    
    # 29
    def _plyr_yr_wk_pos_selected(self):

        self._reset_growing_lists()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._plyr_selected()

        # get the managers for the selected year, week, and player (position is already set)
        self._yr_wk_pos_selected()
    
    # 30
    def _plyr_yr_wk_mgr_selected(self):

        self._reset_growing_lists()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._plyr_selected()
       
        # get the managers for the selected year, week, and player (position is already set)
        self._yr_wk_selected()
       
        # get the weeks for the selected year, manager, and player (position is already set)
        self._yr_mgr_selected()

        # (Getting valid Year options for Week is not necessary as Week cannot be selected without Year)

    # 31
    def _all_selected(self):

        self._reset_growing_lists()

        # Position can only be the position of the player
        self._plyr_yr_wk_mgr_selected()


if __name__ == "__main__":
    service = ValidOptionsService(
        last_added = "year",
        arg1       = "2019",
        arg2       = "Tommy",
        arg3       = "3",
        arg4       = None
    )
    valid_options = service.get_valid_options()
    print(valid_options)