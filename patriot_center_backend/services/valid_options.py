"""Service to compute valid filtering options based on selected criteria."""

from contextlib import contextmanager
from copy import deepcopy
from typing import Dict, Generator, List

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME


class ValidOptionsService:
    """
    Service to compute valid filtering options based on selected criteria.
    """

    def __init__(
            self,
            arg1: str | None,
            arg2: str | None,
            arg3: str | None,
            arg4: str | None
        ) -> None:
        """
        Initializes the ValidOptionsService with the provided arguments.

        Args:
            arg1 (str | None): Position filter value (e.g., "QB")
            arg2 (str | None): Manager filter value (e.g., "Patriots")
            arg3 (str | None): Week filter value (e.g., "1")
            arg4 (str | None): Year filter value (e.g., "2020")

        Notes:
            All arguments are optional and can be set to None if not used.
            If any argument is set, it will be used as a filter to determine valid options.
            The service will compute all possible combinations of valid options based on the provided filters.
        """
        # Initialize master lists with all possible values
        self._years_list     = list(str(year) for year in LEAGUE_IDS.keys())
        self._weeks_list     = list(str(week) for week in range(1, 18))
        self._managers_list  = list(NAME_TO_MANAGER_USERNAME.keys())
        self._positions_list = list(["QB", "RB", "WR", "TE", "K", "DEF"])

        # Store original full lists for iteration (prevents bugs when lists are modified)
        self._original_years_list     = deepcopy(self._years_list)
        self._original_weeks_list     = deepcopy(self._weeks_list)
        self._original_managers_list  = deepcopy(self._managers_list)
        self._original_positions_list = deepcopy(self._positions_list)

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

    def _parse_arg(self, arg : str | None) -> None:
        """Parses the given argument and sets the appropriate instance variable.

        Determines whether the argument is a year, week, manager, player, or position
        and assigns it to the corresponding instance variable.

        Args:
            arg: The argument to parse. Can be a year, week number, manager name,
                player name, or position code.

        Raises:
            ValueError: If multiple arguments of the same type are provided, or
                if the argument is not recognized.
        """
        players_cache = CACHE_MANAGER.get_players_cache()
        
        if arg == None:
            return

        if isinstance(arg, int) or arg.isnumeric():
            arg = int(arg)
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if self._year is not None :
                    raise ValueError("Multiple year arguments provided.")
                self._year = str(arg)
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if self._week is not None:
                    raise ValueError("Multiple week arguments provided.")
                self._week = str(arg)
            
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if self._manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                self._manager = arg
            
            # Check if arg is a player
            elif arg in players_cache:
                
                if self._player is not None:
                    raise ValueError("Multiple player arguments provided.")
                self._player = arg
            
            elif arg in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if self._position is not None:
                    raise ValueError("Multiple position arguments provided.")
                self._position = arg

            else:
                raise ValueError(f"Unrecognized argument: {arg}")

    def _check_year_and_week(self) -> None:
        """Validates that week filter is only used when year is also selected.

        Raises:
            ValueError: If week is selected without year.
        """
        if (self._week is not None) and (self._year is None):
            raise ValueError("Week filter cannot be applied without a Year filter.")

    def _get_function_id(self) -> None:
        """Computes a unique identifier for the handler function to execute.

        The identifier is determined by which filters are active, computed by
        summing bit values for each present filter:
            - Position: 1 (2^0)
            - Manager: 2 (2^1)
            - Week: 4 (2^2)
            - Year: 8 (2^3)
            - Player: 16 (2^4)

        Examples:
            - Position + Manager selected: ID = 3 (1 + 2)
            - Position + Manager + Week selected: ID = 7 (1 + 2 + 4)
        """
        self._func_id = 0
        if self._position is not None:
            self._func_id += self._position_bit
        if self._manager is not None:
            self._func_id += self._manager_bit
        if self._week is not None:
            self._func_id += self._week_bit
        if self._year is not None ():
            self._func_id += self._year_bit
        if self._player is not None:
            self._func_id += self._player_bit

    def _add_to_valid_options(
            self,
            value : str,
            filter1 : str,
            filter2 : str | None = None,
            filter3 : str | None = None,
            filter4 : str | None = None
        ) -> None:
        """Adds a valid option value to the appropriate growing list.

        Tracks progress by checking if all possible values for the specified filters
        have been found. Sets self._done to True when complete to short-circuit searches.

        Args:
            value: The valid option value to add.
            filter1: Primary filter type (e.g., "year", "manager").
            filter2: Second filter to check for completeness.
            filter3: Third filter to check for completeness.
            filter4: Fourth filter to check for completeness.
        """
        # Add value to the first filter's growing list
        growing = getattr(self, f"_growing_{filter1}s_list")
        if value not in growing:
            growing.append(value)

        # Check if all specified filters are complete
        for filter_name in [filter1, filter2, filter3, filter4]:
            if filter_name is None:
                break
            
            growing_list = getattr(self, f"_growing_{filter_name}s_list")
            full_list = getattr(self, f"_{filter_name}s_list")
            
            if sorted(growing_list) != sorted(full_list):
                self._done = False
                return
        
        self._done = True  # All filters complete

    def _reset_growing_lists(self) -> None:
        """Resets all growing lists and sets self._done to False.

        Called when restarting the search for valid options, such as when a filter
        changes or when recomputing valid options after processing a week.
        """
        self._done = False
        self._growing_years_list     = list()
        self._growing_weeks_list     = list()
        self._growing_managers_list  = list()
        self._growing_positions_list = list()

    def _deepcopy_growing(self, *list_names) -> None:
        """Copies the growing lists to the main lists for the specified filter types.

        For each filter name provided, copies the contents of the growing list
        (e.g., _growing_years_list) to the main list (e.g., _years_list).

        Args:
            *list_names: Variable number of filter names (e.g., "years", "weeks").
        """
        for name in list_names:
            setattr(self, f"_{name}_list", deepcopy(getattr(self, f"_growing_{name}_list")))
    
    @contextmanager
    def _preserve_lists(self, *list_names) -> Generator[None, None, None]:
        """Context manager that preserves and restores list state.

        Saves the current state of the specified lists before yielding, then
        restores them to their original state when the context exits.

        Args:
            *list_names: Variable number of filter names to preserve
                (e.g., "years", "weeks").

        Yields:
            None: Control returns to the caller within the preserved context.
        """
        saved = {name: deepcopy(getattr(self, f"_{name}_list")) for name in list_names}
        try:
            yield
        finally:
            for name, value in saved.items():
                setattr(self, f"_{name}_list", value)

    def _preserve_lists_and_call_functions(self, bits_to_call, *list_names) -> None:
        """Calls handler functions for each bit while optionally preserving list state.

        Iterates over the provided function IDs and invokes the corresponding handler
        function for each. If list_names are provided, the lists are saved and restored
        around each function call.

        Args:
            bits_to_call: List of function IDs (bit combinations) to invoke.
            *list_names: Variable number of filter names to preserve during calls
                (e.g., "years", "weeks"). If empty, no preservation is done.
        """
        for bit in bits_to_call:
            if not list_names:
                self._call_new_function(bit)
            else:
                with self._preserve_lists(*list_names):
                    self._call_new_function(bit)

    def _call_new_function(self, bit: int) -> None:
        """Invokes a handler function for a different filter combination.

        Used to recursively compute valid options when one filter changes
        but others remain constant. Resets growing lists before and after
        the function call.

        Args:
            bit: Function ID computed from bit flags.

        Raises:
            ValueError: If the bit combination is not implemented.
        """
        self._reset_growing_lists()

        if bit not in self._function_mapping:
            raise ValueError(f"Function for bit {bit} not implemented.")

        self._function_mapping[bit]()

        self._reset_growing_lists()


    # -----------------------------------------
    # ---------- Public Functions--------------
    # -----------------------------------------
    def get_valid_options(self) -> Dict[str, List[str]]:
        """Returns a dictionary containing all valid options for the given filters.

        Each filter type is sorted appropriately for display:
            - years: reverse chronological order
            - weeks: numerical order
            - managers: alphabetical order
            - positions: original order (QB, RB, WR, TE, K, DEF)

        Returns:
            Dictionary with keys "years", "weeks", "managers", and "positions",
            each containing a list of valid string options.
        """

        # Ensure weeks are sorted numerically
        self._weeks_list = [int(week) for week in self._weeks_list]
        self._weeks_list = sorted(self._weeks_list)
        self._weeks_list = [str(week) for week in self._weeks_list]
        
        return {
            "years"    : sorted(self._years_list, reverse=True),
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
    def _none_selected(self) -> None:
        """Handles case when no filters are selected.

        Returns all possible options for all filter types without restriction.
            - All years available.
            - All weeks available.
            - All managers available.
            - All positions available.
        """
        return
    
    # 1
    def _pos_selected(self) -> None:
        """Handles case when only position is selected.

        Finds valid options for the selected position.
            - Years available for the selected position.
            - Weeks available for the selected position.
            - Managers available for the selected position.
            - All positions available.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Year, Week, and Manager options that have the selected Position
        for year in self._years_list:
            
            data = valid_options_cache.get(year, {})
            
            if self._position not in data.get("positions", []):
                continue
            self._add_to_valid_options(year, "year", "week", "manager")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_valid_options(week, "week", "year", "manager")
                if self._done:
                    break
                
                for manager in self._managers_list:
                    if self._position in data.get(week, {}).get(manager, {}).get("positions", []):
                        self._add_to_valid_options(manager, "manager", "year", "week")
                        if self._done:
                            break
            
                if self._done:
                    break
            if self._done:
                break
        
        self._deepcopy_growing("years", "weeks", "managers")
    
    # 2
    def _mgr_selected(self) -> None:
        """Handles case when only manager is selected.

        Finds valid options for the selected manager.
            - Years available for the selected manager.
            - Weeks available for the selected manager.
            - All managers available.
            - Positions available for the selected manager.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Year, Week, and Position options that have the selected Manager
        for year in self._years_list:
            
            data = valid_options_cache.get(year, {})
            
            if self._manager not in data.get("managers", []):
                continue
            self._add_to_valid_options(year, "year", "week", "position")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._manager not in data.get(week, {}).get("managers", []):
                    continue
                self._add_to_valid_options(week, "week", "year", "position")
                if self._done:
                    break
                
                for position in self._positions_list:
                    if position in data.get(week, {}).get(self._manager, {}).get("positions", []):
                        self._add_to_valid_options(position, "position", "year", "week")
                        if self._done:
                            break
            
                if self._done:
                    break
            if self._done:
                break
        
        self._deepcopy_growing("years", "weeks", "positions")
    
    # 3
    def _mgr_pos_selected(self) -> None:
        """Handles case when manager and position are selected.

        Finds valid options for the selected manager and position.
            - Years available for the selected manager AND position.
            - Weeks available for the selected manager AND position.
            - Managers available for the selected position.
            - Positions available for the selected manager.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Year and Week options that have the selected Manager and Position
        for year in self._years_list:
            
            data = valid_options_cache.get(year, {})
            
            if self._manager not in data.get("managers", []):
                continue
            if self._position not in data.get("positions", []):
                continue
            self._add_to_valid_options(year, "year", "week")
            if self._done:
                break
            
            for week in self._weeks_list:
                
                if self._manager not in data.get(week, {}).get("managers", []):
                    continue
                if self._position not in data.get(week, {}).get("positions", []):
                    continue
                self._add_to_valid_options(week, "week", "year")
                if self._done:
                    break
            
            if self._done:
                break
        
        # Preserve years and weeks list
        self._deepcopy_growing("years", "weeks")
        # Within the valid Years and Weeks:
        #     - Get the Manager options that have the selected Position
        #     - Get the Position options that have the selected Manager
        self._preserve_lists_and_call_functions(
            [
                self._position_bit,
                self._manager_bit
            ],
            "years", "weeks"
        )
    
    # 8
    def _yr_selected(self):
        """Handles case when only year is selected.

        Finds valid options for the selected year.
            - All years available.
            - Weeks available for the selected year.
            - Managers available for the selected year.
            - Positions available for the selected year.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        data = valid_options_cache.get(self._year, {})

        # Weeks, Managers, and Positions for the selected Year
        for week in self._weeks_list:
            if week in data.get("weeks", []):
                self._add_to_valid_options(week, "week")
        for manager in self._managers_list:
            if manager in data.get("managers", []):
                self._add_to_valid_options(manager, "manager")
        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_valid_options(position, "position")
        
        self._deepcopy_growing("weeks", "managers", "positions")
        self._preserve_lists_and_call_functions(
            [
                self._position_bit,
                self._manager_bit
            ],
            "years", "weeks"
        )
                
    # 9
    def _yr_pos_selected(self):
        """Handles case when year and position are selected.

        Finds valid options for the selected year and position.
            - Years available for the selected position.
            - Weeks available for the selected year AND position.
            - Managers available for the selected year AND position.
            - Positions available for the selected year.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Weeks and Managers options that have the selected Position for the selected Year
        data = valid_options_cache.get(self._year, {})

        for week in self._weeks_list:
            
            if self._position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_valid_options(week, "week", "manager")
            if self._done:
                break
            
            for manager in self._managers_list:
                if self._position in data.get(week, {}).get(manager, {}).get("positions", []):
                    self._add_to_valid_options(manager, "manager", "week")
                    if self._done:
                        break
            
            if self._done:
                break

        self._deepcopy_growing("weeks", "managers")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit,
                self._position_bit
            ],
            "weeks", "managers"
        )
    
    # 10
    def _yr_mgr_selected(self):
        """Handles case when year and manager are selected.

        Finds valid options for the selected year and manager.
            - Years available for the selected manager.
            - Weeks available for the selected year AND manager.
            - Managers available for the selected year.
            - Positions available for the selected year AND manager.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Weeks and Positions options that have the selected Manager for the selected Year
        data = valid_options_cache.get(self._year, {})

        for week in self._weeks_list:
            
            if self._manager not in data.get(week, {}).get("managers", []):
                continue
            self._add_to_valid_options(week, "week", "position")
            if self._done:
                break
            
            for position in self._positions_list:
                if position in data.get(week, {}).get(self._manager, {}).get("positions", []):
                    self._add_to_valid_options(position, "position", "week")
                    if self._done:
                        break
            
            if self._done:
                break
        
        self._deepcopy_growing("weeks", "positions")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit,
                self._manager_bit
            ],
            "weeks", "positions"
        )
    
    # 11
    def _yr_mgr_pos_selected(self):
        """Handles case when year, manager, and position are selected.

        Finds valid options for the selected manager and position.
            - Years available for the selected manager AND position.
            - Weeks available for the selected year AND manager AND position.
            - Managers available for the selected year AND position.
            - Positions available for the selected year AND manager.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Weeks options that have the selected Manager and Position for the selected Year
        data = valid_options_cache.get(self._year, {})

        for week in self._weeks_list:
            
            if self._manager not in data.get(week, {}).get("managers", []):
                continue
            if self._position not in data.get(week, {}).get("positions", []):
                continue
            self._add_to_valid_options(week, "week")
            if self._done:
                break
        
        self._deepcopy_growing("weeks")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit    + self._position_bit,
                self._year_bit    + self._manager_bit,
                self._manager_bit + self._position_bit
            ]
        )

    # 12
    def _yr_wk_selected(self):
        """Handles case when year and week are selected.

        Finds valid options for the selected year and week.
            - All years available.
            - Weeks available for the selected year.
            - Managers available for the selected year AND week.
            - Positions available for the selected year AND week.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Managers and Positions for the selected Year and Week
        data = valid_options_cache.get(self._year, {}).get(self._week, {})

        # Get the vaid Positions and Managers for the selected Year and Week
        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_valid_options(position, "position")
                if self._done:
                    break

        for manager in self._managers_list:
            if manager in data.get("managers", []):
                self._add_to_valid_options(manager, "manager")
                if self._done:
                    break

        self._deepcopy_growing("managers", "positions")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit
            ],
            "managers", "positions"
        )
    
    # 13
    def _yr_wk_pos_selected(self):
        """Handles case when year, week, and position are selected.

        Finds valid options for the selected year, week, and position.
            - Years available for the selected position.
            - Weeks available for the selected year AND position.
            - Managers available for the selected year AND week AND position.
            - Positions available for the selected year AND week.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Managers options that have the selected Position, Year, and Week
        data = valid_options_cache.get(self._year, {}).get(self._week, {})

        for manager in self._managers_list:
            if self._position in data.get(manager, {}).get("positions", []):
                self._add_to_valid_options(manager, "manager")
                if self._done:
                    break

        self._deepcopy_growing("managers")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit + self._week_bit,
                self._year_bit + self._position_bit
            ],
            "managers"
        )
    
    # 14
    def _yr_wk_mgr_selected(self):
        """Handles case when year, week, and manager are selected.

        Finds valid options for the selected year, week, and manager.
            - Years available for the selected manager.
            - Weeks available for the selected year AND manager.
            - Managers available for the selected year AND week.
            - Positions available for the selected year AND week AND manager.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Set positions list for the selected year, week, and manager
        data = valid_options_cache.get(self._year, {}).get(self._week, {}).get(self._manager, {})

        for position in self._positions_list:
            if position in data.get("positions", []):
                self._add_to_valid_options(position, "position")
                if self._done:
                    break

        self._deepcopy_growing("positions")
        self._preserve_lists_and_call_functions(
            [
                self._year_bit + self._week_bit,
                self._year_bit + self._manager_bit
            ],
            "positions"
        )
    
    # 15
    def _yr_wk_mgr_pos_selected(self):
        """Handles case when year, week, manager and position are selected.

        Finds valid options for the selected year, week, manager, and position.
            - Years available for the selected manager AND position.
            - Weeks available for the selected year AND manager AND position.
            - Managers available for the selected year AND week AND position.
            - Positions available for the selected year AND week AND manager.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
        """
        self._preserve_lists_and_call_functions([self._year_bit + self._manager_bit + self._position_bit,
                                                 self._year_bit + self._week_bit + self._position_bit,
                                                 self._year_bit + self._week_bit + self._manager_bit])
    
    # 16
    def _plyr_selected(self):
        """Handles case when player is selected.

        Finds valid options for the selected player.
            - Years available for the selected player.
            - Weeks available for the selected player.
            - Managers available for the selected player.
            - Only the position of the selected player.

        Notes
            - Position options with a player selected can only be the position of the player.
        """
        players_cache       = CACHE_MANAGER.get_players_cache()
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Position can only be the position of the player (set once)
        self._positions_list = list([players_cache[self._player]["position"]])

        # Always reset the lists to find valid options for the player
        # Use original lists for iteration to avoid bugs from modified lists
        for year in self._original_years_list:

            data = valid_options_cache.get(year, {})

            if self._player not in data.get("players", []):
                continue
            self._add_to_valid_options(year, "year", "week", "manager", "position")
            if self._done:
                break

            for week in self._original_weeks_list:

                if self._player not in data.get(week, {}).get("players", []):
                    continue
                self._add_to_valid_options(week, "week", "year", "manager", "position")
                if self._done:
                    break

                for manager in self._original_managers_list:

                    if self._player in data.get(week, {}).get(manager, {}).get("players", []):
                        self._add_to_valid_options(manager, "manager", "year", "week", "position")
                        if self._done:
                            break

                if self._done:
                    break
            if self._done:
                break
        
        self._deepcopy_growing("years", "weeks", "managers")
    
    # 17
    def _plyr_pos_selected(self):
        """Handles case when player and position are selected.

        Finds valid options for the selected player and position.
            - Years available for the selected player.
            - Weeks available for the selected player.
            - Managers available for the selected player.
            - Only the position of the selected player.

        Notes
            - Because position can only be the position of the player, having a position selected is the same as having a just player selected.
            - Position options with a player selected can only be the position of the player.
        """
        # Position can only be the position of the player
        self._call_new_function(self._player_bit)
    
    # 18
    def _plyr_mgr_selected(self):
        """Handles case when player and manager are selected.

        Finds valid options for the selected player and manager.
            - Years available for the selected player AND manager.
            - Weeks available for the selected player AND manager.
            - Managers available for the selected player.
            - Only the position of the selected player.

        Notes
            - Position options with a player selected can only be the position of the player.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # Filter out everything that does not have the player
        self._call_new_function(self._player_bit)

        # Get the years and weeks for the selected player (position is already set)
        for year in self._years_list:
            
            data = valid_options_cache.get(year, {})

            for week in self._weeks_list:

                if self._player in data.get(week, {}).get(self._manager, {}).get("players", []):
                    self._add_to_valid_options(year, "year", "week", "position")
                    self._add_to_valid_options(week, "week", "year", "position")
                    if self._done:
                        break
                
            if self._done:
                break
        
        self._deepcopy_growing("years", "weeks")
    
    # 19
    def _plyr_mgr_pos_selected(self):
        """Handles case when player is selected.

        Finds valid options for the selected player.
            - Years available for the selected player AND manager.
            - Weeks available for the selected player AND manager.
            - Managers available for the selected player.
            - Only the position of the selected player.

        Notes
            - Because position can only be the position of the player, having a position selected is the same as having a just player selected.
            - Position options with a player selected can only be the position of the player.
        """
        # Position can only be the position of the player
        self._call_new_function(self._player_bit + self._manager_bit)

    # 24
    def _plyr_yr_selected(self):
        """
        Handles case when player and year are selected.

        Finds valid options for the selected player and year.
            - Years available for the selected player.
            - Weeks available for the selected player AND year.
            - Managers available for the selected player AND year.
            - Only the position of the selected player.

        Notes
            - Position options with a player selected can only be the position of the player.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._call_new_function(self._player_bit)

        # Get the weeks and managers for the selected year and player (position is already set)
        data = valid_options_cache.get(self._year, {})

        for week in self._weeks_list:

            if self._player not in data.get(week, {}).get("players", []):
                continue

            for manager in self._managers_list:

                if self._player in data.get(week, {}).get(manager, {}).get("players", []):
                    self._add_to_valid_options(week, "week", "manager")
                    self._add_to_valid_options(manager, "manager", "week")
                    if self._done:
                        break
            
            if self._done:
                break
        
        self._deepcopy_growing("managers", "weeks")

    # 25
    def _plyr_yr_pos_selected(self):
        """
        Handles case when player, year, and position are selected.

        Finds valid options for the selected player, year, and position.
            - Years available for the selected player.
            - Weeks available for the selected player AND year.
            - Managers available for the selected player AND year.
            - Only the position of the selected player.

        Notes
            - Because position can only be the position of the player, having a position selected is the same as having a just player selected.
            - Position options with a player selected can only be the position of the player.
        """
        # Get the weeks and managers for the selected year and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit)
    
    # 26
    def _plyr_yr_mgr_selected(self):
        """
        Handles case when player, year, and manager are selected.

        Finds valid options for the selected player, year, and manager.
            - Years available for the selected player AND manager.
            - Weeks available for the selected player AND year AND manager.
            - Managers available for the selected player AND year.
            - Only the position of the selected player.

        Notes
            - Position options with a player selected can only be the position of the player.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        self._preserve_lists_and_call_functions([self._player_bit,
                                                self._player_bit + self._manager_bit])
        
        self._preserve_lists_and_call_functions([self._player_bit + self._year_bit],
                                                "years")

        # Get the Weeks options that have the selected Year, Manager and Player
        data = valid_options_cache.get(self._year, {})

        for week in self._weeks_list:
            if self._player in data.get(week, {}).get(self._manager, {}).get("players", []):
                self._add_to_valid_options(week, "week")
                if self._done:
                    break
        
        self._deepcopy_growing("weeks")
        
    # 27
    def _plyr_yr_mgr_pos_selected(self):
        """
        Handles case when player, year, manager, and position are selected.

        Finds valid options for the selected player, year, manager, and position.
            - Years available for the selected player AND manager.
            - Weeks available for the selected player AND year AND manager.
            - Managers available for the selected player AND year.
            - Only the position of the selected player.

        Notes
            - Because position can only be the position of the player, having a position selected is the same as having a just player selected.
            - Position options with a player selected can only be the position of the player.
        """
        
        # get the weeks for the selected year, manager, and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit + self._manager_bit)
        
    # 28
    def _plyr_yr_wk_selected(self):
        """
        Handles case when player, year, and week are selected.

        Finds valid options for the selected player, year, and week.
            - Years available for the selected player.
            - Weeks available for the selected player AND year.
            - Managers available for the selected player AND year AND week.
            - Only the position of the selected player.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
            - Position options with a player selected can only be the position of the player.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        # filter out everything that does not have the player and shorten the lists to loop through
        self._call_new_function(self._player_bit)

        # get the managers for the selected year, week, and player (position is already set)
        data = valid_options_cache.get(self._year, {}).get(self._week, {})

        for manager in self._managers_list:
            if self._player in data.get(manager, {}).get("players", []):
                self._add_to_valid_options(manager, "manager")
                if self._done:
                    break
        
        self._deepcopy_growing("managers")
        self._preserve_lists_and_call_functions(
            [
                self._player_bit + self._year_bit
            ],
            "managers"
        )

        # Get Year options: years where the player played in the selected week
        # Week requires year, so we need to find all years where player played in this specific week
        for year in self._years_list:
            data = valid_options_cache.get(year, {})
            if self._player in data.get(self._week, {}).get("players", []):
                self._add_to_valid_options(year, "year")
                if self._done:
                    break
        
        self._deepcopy_growing("years")
    
    # 29
    def _plyr_yr_wk_pos_selected(self):
        """
        Handles case when player, year, week, and position are selected.

        Finds valid options for the selected player, year, week, and position.
            - Years available for the selected player.
            - Weeks available for the selected player AND year.
            - Managers available for the selected player AND year AND week.
            - Only the position of the selected player.

        Notes
            - Because position can only be the position of the player, having a position selected is the same as having a just player selected.
            - Year options available are not limited to weeks available as week depends on year to be selected.
            - Position options with a player selected can only be the position of the player.
        """

        # get the managers for the selected year, week, and player (position is already set)
        self._call_new_function(self._player_bit + self._year_bit + self._week_bit)
    
    # 30
    def _plyr_yr_wk_mgr_selected(self):
        """
        Handles case when player, year, week, and manager are selected.

        Finds valid options for the selected player, year, week, and manager.
            - Years available for the selected player AND manager.
            - Weeks available for the selected player AND year AND manager.
            - Managers available for the selected player AND year AND week.
            - Only the position of the selected player.

        Notes
            - Year options available are not limited to weeks available as week depends on year to be selected.
            - Position options with a player selected can only be the position of the player.
        """
        self._preserve_lists_and_call_functions(
            [
                self._player_bit + self._manager_bit,
                self._player_bit + self._manager_bit + self._year_bit
            ]
        )

        # In a given year and week, the manager can only be the selected manager
        self._managers_list = list([self._manager])