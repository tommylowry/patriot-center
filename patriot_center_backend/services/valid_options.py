"""
Valid filtering options service for the Patriot Center backend.

This service handles complex filtering logic to determine which combinations of
year, week, manager, player, and position are valid based on the available data.
It uses a bit-flag system to map filter combinations to specialized handler methods.

The service supports up to 4 simultaneous filters (player, year, week, manager, position)
and ensures that returned options are consistent with the underlying data cache.

Key constraints:
- Week filter requires year to be selected
- Player filter restricts position to the player's actual position
- Some combinations (5 filters) are not implemented as they exceed practical limits
"""
import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache

# Load caches at module import time for fast access
VALID_OPTIONS_CACHE = fetch_valid_options_cache()
PLAYERS_DATA = fetch_players()

class ValidOptionsService:
    """
    Service to compute valid filtering options based on selected criteria.

    Uses a bit-flag mapping system where each filter type has a bit value:
    - Position: 1
    - Manager: 2
    - Week: 4
    - Year: 8
    - Player: 16

    The sum of selected filter bits maps to a handler method that computes
    which other filter values remain valid given the current selection.
    """

    def __init__(
        self,
        arg1: str | None,
        arg2: str | None,
        arg3: str | None,
        arg4: str | None
    ):
        """
        Initialize the service and compute valid options.

        Args:
            arg1-arg4 (str | None): Up to 4 filter arguments that can be:
                - Year (int matching LEAGUE_IDS)
                - Week (int 1-17)
                - Manager name (str matching NAME_TO_MANAGER_USERNAME)
                - Player name (str matching PLAYERS_DATA)
                - Position (str: QB, RB, WR, TE, K, DEF)

        Raises:
            ValueError: If arguments are invalid, duplicated, or violate constraints
        """

        # Initialize master lists with all possible values
        self._years_list     = list(str(year) for year in LEAGUE_IDS.keys())
        self._weeks_list     = list(str(week) for week in range(1, 18))
        self._managers_list  = list(NAME_TO_MANAGER_USERNAME.keys())
        self._positions_list = list(["QB", "RB", "WR", "TE", "K", "DEF"])

        # Store original full lists for iteration (prevents bugs when lists are modified)
        self._original_years_list     = copy.deepcopy(self._years_list)
        self._original_weeks_list     = copy.deepcopy(self._weeks_list)
        self._original_managers_list  = copy.deepcopy(self._managers_list)
        self._original_positions_list = copy.deepcopy(self._positions_list)

        # Tracking lists that grow as we find valid combinations
        self._growing_years_list     = list()
        self._growing_weeks_list     = list()
        self._growing_managers_list  = list()
        self._growing_positions_list = list()

        # Currently selected filter values (parsed from args)
        self._year      = None
        self._week      = None
        self._manager   = None
        self._player    = None
        self._position  = None

        # Parse all provided arguments to determine what filters are active
        self._parse_arg(arg1)
        self._parse_arg(arg2)
        self._parse_arg(arg3)
        self._parse_arg(arg4)
        self._check_year_and_week()

        # Control flags for filtering logic
        self._done = False  # Tracks whether all valid options have been found

        # Mapping of function IDs to their corresponding methods
        # Function IDs are computed using bit flags (see class docstring)
        # Note: [4-7], [20-23] week cannot be used as a filter without a year selected
        # Note: [31] all 5 filters selected simultaneously is not implemented (exceeds 4-filter limit)

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

        # Bit flags for computing function IDs (powers of 2 for bitwise operations)
        self._position_bit = 1   # 2^0
        self._manager_bit  = 2   # 2^1
        self._week_bit     = 4   # 2^2
        self._year_bit     = 8   # 2^3
        self._player_bit   = 16  # 2^4

        # Compute which handler function to call based on active filters
        self._get_function_id()

        # Execute the appropriate handler function to populate valid options
        self._function_mapping[self._func_id]()

    # ----------------------------------------
    # ---------- Internal Functions ----------
    # ----------------------------------------
    def _year_selected(self) -> bool:
        """Check if year filter is active."""
        return False if self._year == None else True

    def _week_selected(self) -> bool:
        """Check if week filter is active."""
        return False if self._week == None else True

    def _manager_selected(self) -> bool:
        """Check if manager filter is active."""
        return False if self._manager == None else True

    def _player_selected(self) -> bool:
        """Check if player filter is active."""
        return False if self._player == None else True

    def _position_selected(self) -> bool:
        """Check if position filter is active."""
        return False if self._position == None else True

    def _parse_arg(self, arg : str | None):
        """
        Parse a single argument and classify it as year, week, manager, player, or position.

        Args:
            arg (str | None): Argument to parse

        Raises:
            ValueError: If argument is invalid, duplicated, or unrecognized
        """
        
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
        """
        Validate that week filter is only used when year is also selected.

        Raises:
            ValueError: If week is selected without year
        """
        if self._week_selected() and not self._year_selected():
            raise ValueError("Week filter cannot be applied without a Year filter.")

    def _get_function_id(self):
        """
        Compute function ID by summing bit flags for all active filters.

        The resulting ID maps to a handler function in _function_mapping that
        knows how to compute valid options for that specific filter combination.
        """
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
        """
        Add a valid option value to the appropriate growing list.

        Tracks progress by checking if all possible values for the primary filter
        have been found. Sets self._done = True when complete to short-circuit searches.

        Args:
            value (str): The valid option value to add
            filter1 (str): Primary filter type (e.g., "year", "manager")
            filter2-4 (str | None): Additional filters to check for completeness
        """
        
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
        """
        Reset all growing lists and done flag for a fresh filter computation.

        Used when recursively calling handler functions to compute options for
        different filter combinations.
        """
        self._done = False
        self._growing_years_list     = list()
        self._growing_weeks_list     = list()
        self._growing_managers_list  = list()
        self._growing_positions_list = list()

    def _call_new_function(self, bit: int):
        """
        Invoke a handler function for a different filter combination.

        Used to recursively compute valid options when one filter is changed
        but others remain constant.

        Args:
            bit (int): Function ID computed from bit flags

        Raises:
            ValueError: If the bit combination is not implemented
        """
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

        # Save years and weeks before getting managers (so they don't get overwritten)
        saved_years_list = copy.deepcopy(self._years_list)
        saved_weeks_list = copy.deepcopy(self._weeks_list)

        # Within the valid Years and Weeks: Get the Manager options that have the selected Position
        self._call_new_function(self._position_bit)

        # Restore the years and weeks lists (they were overwritten by the function call above)
        self._years_list = saved_years_list
        self._weeks_list = saved_weeks_list

        # Within the valid Years and Weeks: Get the Position options that have the selected Manager
        self._call_new_function(self._manager_bit)

        # Restore the years and weeks lists again (they were overwritten by the function call above)
        self._years_list = saved_years_list
        self._weeks_list = saved_weeks_list
    
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

        # Save weeks and managers before getting positions (so they don't get overwritten)
        saved_weeks_list = copy.deepcopy(self._weeks_list)
        saved_managers_list = copy.deepcopy(self._managers_list)

        # Within the valid Weeks and Managers: Get the Position options that have the selected Year
        self._call_new_function(self._year_bit)

        # Restore the weeks and managers lists (they were overwritten by the function call above)
        self._weeks_list = saved_weeks_list
        self._managers_list = saved_managers_list

        # Within the valid Weeks and Managers: Get the Year options that have the selected Position
        self._call_new_function(self._position_bit)

        # Restore the weeks and managers lists again (they were overwritten by the function call above)
        self._weeks_list = saved_weeks_list
        self._managers_list = saved_managers_list
    
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

        # Save weeks and positions before getting managers (so they don't get overwritten)
        saved_weeks_list = copy.deepcopy(self._weeks_list)
        saved_positions_list = copy.deepcopy(self._positions_list)

        # Within the valid Weeks and Positions: Get the Manager options that have the selected Year
        self._call_new_function(self._year_bit)

        # Restore the weeks and positions lists (they were overwritten by the function call above)
        self._weeks_list = saved_weeks_list
        self._positions_list = saved_positions_list

        # Within the valid Weeks and Positions: Get the Year options that have the selected Manager
        self._call_new_function(self._manager_bit)

        # Restore the weeks and positions lists again (they were overwritten by the function call above)
        self._weeks_list = saved_weeks_list
        self._positions_list = saved_positions_list
    
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

        # Save managers and positions before getting weeks (so they don't get overwritten)
        saved_managers_list = copy.deepcopy(self._managers_list)
        saved_positions_list = copy.deepcopy(self._positions_list)

        # Within the valid Managers and Positions: Get the Week options that have the selected Year
        self._call_new_function(self._year_bit)

        # Restore the managers and positions lists (they were overwritten by the function call above)
        self._managers_list = saved_managers_list
        self._positions_list = saved_positions_list

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

        # Save managers before getting positions and weeks (so it doesn't get overwritten)
        saved_managers_list = copy.deepcopy(self._managers_list)

        # Get the Positions list for the selected year and week
        self._call_new_function(self._year_bit + self._week_bit)

        # Restore the managers list (it was overwritten by the function call above)
        self._managers_list = saved_managers_list

        # Get the Weeks list for the selected year and position
        self._call_new_function(self._year_bit + self._position_bit)

        # Restore the managers list again (it was overwritten by the function call above)
        self._managers_list = saved_managers_list

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

        # Save positions before getting managers and weeks (so it doesn't get overwritten)
        saved_positions_list = copy.deepcopy(self._positions_list)

        # Within the valid Positions: Get the Manager options that have the selected Year and Week
        self._call_new_function(self._year_bit + self._week_bit)

        # Restore the positions list (it was overwritten by the function call above)
        self._positions_list = saved_positions_list

        # Within the valid Positions: Get the Week options that have the selected Year and Manager
        self._call_new_function(self._year_bit + self._manager_bit)

        # Restore the positions list again (it was overwritten by the function call above)
        self._positions_list = saved_positions_list

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

        # Position can only be the position of the player (set once)
        self._positions_list = list([PLAYERS_DATA[self._player]["position"]])

        # Always reset the lists to find valid options for the player
        # Use original lists for iteration to avoid bugs from modified lists
        for year in self._original_years_list:

            data = VALID_OPTIONS_CACHE.get(year, {})

            if self._player not in data.get("players", []):
                continue
            self._add_to_vaild_options(year, "year", "week", "manager", "position")
            if self._done:
                break

            for week in self._original_weeks_list:

                if self._player not in data.get(week, {}).get("players", []):
                    continue
                self._add_to_vaild_options(week, "week", "year", "manager", "position")
                if self._done:
                    break

                for manager in self._original_managers_list:

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

        # Get the Year options that have the selected Manager and Player
        self._call_new_function(self._player_bit + self._manager_bit)

        # Save years list before getting managers (so it doesn't get overwritten)
        saved_years_list = copy.deepcopy(self._years_list)

        # Get the Managers options that have the selected Year and Player
        self._call_new_function(self._player_bit + self._year_bit)

        # Restore the years list (it was overwritten by the function call above)
        self._years_list = saved_years_list

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

        # Save managers list before getting weeks (so it doesn't get overwritten)
        saved_managers_list = copy.deepcopy(self._managers_list)

        # Within the valid Managers: Get the Weeks options that have the selected Year and Player
        self._call_new_function(self._player_bit + self._year_bit)

        # Restore the managers list (it was overwritten by the function call above)
        self._managers_list = saved_managers_list

        # Get Year options: years where the player played in the selected week
        # Week requires year, so we need to find all years where player played in this specific week
        for year in self._years_list:
            data = VALID_OPTIONS_CACHE.get(year, {})
            if self._player in data.get(self._week, {}).get("players", []):
                self._add_to_vaild_options(year, "year")
                if self._done:
                    break

        self._years_list = copy.deepcopy(self._growing_years_list)
    
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