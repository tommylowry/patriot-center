import copy

from patriot_center_backend.constants import MANAGER_METADATA_CACHE_FILE, TRANSACTION_IDS_FILE, LEAGUE_IDS, NAME_TO_MANAGER_USERNAME, STARTERS_CACHE_FILE
from patriot_center_backend.utils.cache_utils import load_cache, save_cache
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.utils.player_ids_loader import load_player_ids

STARTERS_CACHE = load_cache(STARTERS_CACHE_FILE)


class ManagerMetadataManager:
    def __init__(self):
        
        # In-memory cache structure (see _initialize_summary_templates for details on sub-structures)
        self._cache = {}

        # FAAB usage flag
        self._use_faab           = None
        self._playoff_week_start = None

        # Predefined templates for initializing new data
        self._initialize_summary_templates()

        # Weekly roster ID to manager mapping for current caching session, cleared on week cache completion
        self._weekly_roster_ids = {
            # roster_id: manager
        }

        # Player ID mapping
        self._player_ids           = load_player_ids()
        self._transaction_id_cache = load_cache(TRANSACTION_IDS_FILE, initialize_with_last_updated_info = False)
        
        # Weekly metadata
        self._year = None
        self._week = None

        # Playoff roster IDs
        self._playoff_roster_ids = {}
        
        # Load existing cache from disk
        self._load()





    # ---------- Public Methods For Importing Data ----------
    def set_roster_id(self, manager: str, year: str, week: str, roster_id: int, playoff_roster_ids: dict = {}):
        """Set the roster ID for a given manager and year."""
        if roster_id == None:
            # Co-manager scenario; skip
            return

        self._year = year
        self._week = week
        self._playoff_roster_ids = playoff_roster_ids

        if week == "1" or self._use_faab == None or self._playoff_week_start == None:
            # Fetch league settings to determine FAAB usage at start of season
            league_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year), '')}")[0]
            self._use_faab = True if league_settings.get("settings", {}).get("waiver_type", 1)==2 else False
            self._playoff_week_start = league_settings.get("settings", {}).get("playoff_week_start", None)

        self._weekly_roster_ids[roster_id] = manager
        self._set_defaults_if_missing(roster_id)
        self._cache[manager]["years"][year]["roster_id"] = roster_id

        if "user_id" not in self._cache[manager]["summary"]:
            username = NAME_TO_MANAGER_USERNAME.get(manager, "")
            if username:
                user_payload, status_code = fetch_sleeper_data(f"user/{username}")
                if status_code == 200 and "user_id" in user_payload:
                    self._cache[manager]["summary"]["user_id"] = user_payload["user_id"]
                    self._cache[manager]["summary"]["overall_data"]["avatar_urls"]["full_size"] = f"https://sleepercdn.com/avatars/{user_payload.get('avatar','')}"
                    self._cache[manager]["summary"]["overall_data"]["avatar_urls"]["thumbnail"] = f"https://sleepercdn.com/avatars/thumbs/{user_payload.get('avatar','')}"

                else:
                    raise ValueError(f"Failed to fetch user data for manager {manager} with username {username}.")
            else:
                raise ValueError(f"No username mapping found for manager {manager}.")


    def cache_week_data(self, year: str, week: str):
        """Cache week-specific data for a given week and year."""

        # Ensure preconditions are met
        self._caching_preconditions_met()

        # Scrub transaction data for the week
        self._scrub_transaction_data(year, week)

        # Scrub matchup data for the week
        self._scrub_matchup_data(year, week)

        # Scrub playoff data for the week if applicable
        if self._get_season_state() == "playoffs":
            self._scrub_playoff_data(year, week)

        # Clear weekly metadata
        self._year = None
        self._week = None    








    # ---------- Public Methods for Exporting Data ----------
    def get_managers_list(self) -> dict:
        """Returns list of all managers with basic info.
        
        EXAMPLE:
        {
            "managers": [
                {
                    "name": "Tommy",
                    "avatar_urls": {
                        "full_size": "https://sleepercdn.com/avatars/avatar_url",
                        "thumbnail": "https://sleepercdn.com/avatars/thumbs/avatar_url"
                    },
                    "years_active": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
                    "total_trades": 27,
                    "overall_record": "11-6-0"
                },
                ...
            ]
        }
        
        """
        managers_list = []
        
        for manager in self._cache:
            wins   = self._cache[manager]["summary"]["matchup_data"]["overall"]["wins"]["total"]
            losses = self._cache[manager]["summary"]["matchup_data"]["overall"]["losses"]["total"]
            ties   = self._cache[manager]["summary"]["matchup_data"]["overall"]["ties"]["total"]
            manager_item = {
                "name":           manager,
                "avatar_urls":    self._cache[manager]["summary"]["overall_data"].get("avatar_urls", {}),
                "years_active":   list(self._cache[manager].get("years", {}).keys()),
                "total_trades":   self._cache[manager]["summary"]["transactions"]["trades"]["total"],
                "overall_record": f"{wins}-{losses}-{ties}"
            }
            managers_list.append(manager_item)
        
        return { "managers": managers_list }
    

    def get_manager_summary(self, manager_name: str, year: str = None) -> dict:
        """
        Returns complete summary data for a manager.
        Year is optional, all of the data is either all-time if year is None or
        year specific if Year is specified.

        top _ partners is meant to be top 3.
        If the count at 3rd place is tied with other counts, those counts are included.

        EXAMPLE:
        {
            "manager_name": "Tommy",
            "user_id": "399258572535365632",
            "avatar_urls": {
                "full_size": "https://sleepercdn.com/avatars/avatar_url",
                "thumbnail": "https://sleepercdn.com/avatars/thumbs/avatar_url"
            },
            "years_active": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
            "matchup_data": {
                "overall": {
                    "record": "11-6-0",
                    "win_percentage": 64.7,
                    "total_points_for": 1951.07,
                    "total_points_against": 1881.71,
                    "point_differential": 69.36,
                    "average_points_for": 114.77,
                    "average_points_against": 110.69,
                    "average_point_differential": 4.08
                },
                "regular_season": {
                    "record": "8-6-0",
                    ... (same structure as overall)
                    "average_point_differential": -2.9
                },
                "playoffs": {
                    "record": "3-0-0",
                    ... (same structure as overall)
                    "average_point_differential": 36.64
                }
            },
            "transactions": {
                "trades": {
                    "total": 27,
                    "top_trade_partners": [
                        {"name": "Owen", "count": 7},
                        {"name": "Dheeraj", "count": 7},
                        {"name": "Cody", "count": 4},
                    ],
                    "most_aquired_players": [
                        {"name": "Ezekiel Elliott", "count": 2, "from": {"Sach": 1, "Dheeraj": 1}},
                        {"name": "Tank Dell", "count": 2, "from": {"Davey": 1, "Cody": 1}},
                        {"name": "$2 FAAB", "count": 2, "from": {"Dheeraj": 2}},
                        {"name": "Chris Olave", "count": 2, "from": {"Sach": 1, "Dheeraj": 1}}
                    ],
                    "most_sent_players": [
                        ... (same structure as most_acquired_players)
                    ]
                },
                "adds": {
                    "total": 86,
                    "top_players_added": [
                        ... (same structure as top_trade_partners)
                    ]
                },
                "drops": {
                    "total": 82,
                    "top_players_dropped": [
                        ... (same structure as top_trade_partners)
                    ]
                },
                "faab": {
                    "total_spent": 120,
                    "biggest_acquisitions": [
                        {"name": "Ty Chandler", "amount": 23},
                        {"name": "Jahan Dotson", "amount": 23},
                        {"name": "Jaxon Smith-Njigba", "amount": 23}
                    ],
                    "faab_traded": {
                        "sent": 55,
                        "received": 33,
                        "net": -22
                    }
                }
            },
            "overall_data": {
                "playoff_appearances": 3,
                "placements": [
                    {"year": "2021","placement": 1},
                    {"year": "2022","placement": 3},
                    {"year": "2024","placement": 1},
                ],
                "best_finish": 1,
                "championships": 2
            },
            "head_to_head": {
                "Dheeraj": {
                    "wins": 1,
                    "losses": 0,
                    "ties": 0,
                    "points_for": 76.15,
                    "points_against": 72.29
                },
                ...
            }
        }

        """


        if manager_name not in self._cache:
            raise ValueError(f"Manager {manager_name} not found in cache.")
        
        if year:
            if year not in self._cache[manager_name]["years"]:
                raise ValueError(f"Year {year} not found for manager {manager_name} in cache.")
        
        return_dict = {}
        return_dict["manager_name"] = manager_name
        return_dict["user_id"]      = self._cache[manager_name]["summary"].get("user_id", "")
        return_dict["avatar_urls"]  = self._cache[manager_name]["summary"]["overall_data"].get("avatar_urls", {})
        return_dict["years_active"] = list(self._cache[manager_name].get("years", {}).keys())

        return_dict["matchup_data"] = self._get_matchup_details_from_cache(manager_name, year)
        return_dict["transactions"] = self._get_trasaction_details_from_cache(manager_name, year)
        return_dict["overall_data"] = self._get_overall_data_details_from_cache(manager_name)
        return_dict["head_to_head"] = self._get_head_to_head_details_from_cache(manager_name, year)

        return copy.deepcopy(return_dict)
    

    def get_manager_yearly_data(self, manager_name: str, year: str) -> dict:
        """Returns detailed yearly data for a manager.

        EXAMPLE:
        {
            "manager_name": "Tommy",
            "year": "2023",
            "avatar_urls": {
                "full_size" = "https://sleepercdn.com/avatars/avatar_link",
                "thumbnail" = "https://sleepercdn.com/avatars/thumbs/avatar_link"
            },
            
            "matchup_data": {
                "overall": {
                    "record": "11-6-0",
                    "win_percentage": 64.7,
                    "total_points_for": 1951.07,
                    "total_points_against": 1881.71,
                    "point_differential": 69.36,
                    "average_points_for": 114.77,
                    "average_points_against": 110.69,
                    "average_point_differential": 4.08,
                    "weekly_scores": [
                        ...
                        {
                            "week": "2",
                            "opponent": "Sam",
                            "points_for": 126.92,
                            "points_against": 91.89,
                            "result": "win"
                        },
                        ...
                    ]
                    },
                    "regular_season": {
                        "record": "8-6-0",
                        "win_percentage": 57.1,
                        "total_points_for": 1584.58,
                        "total_points_against": 1625.15,
                        "point_differential": -40.57,
                        "average_points_for": 113.18,
                        "average_points_against": 116.08,
                        "average_point_differential": -2.9
                    },
                    "playoffs": {
                        "record": "3-0-0",
                        "win_percentage": 100.0,
                        "total_points_for": 366.49,
                        "total_points_against": 256.56,
                        "point_differential": 109.93,
                        "average_points_for": 122.16,
                        "average_points_against": 85.52,
                        "average_point_differential": 36.64
                    }
                }
            },
            
            "transactions": {
                "trades": {
                    "total": 27,
                    "by_week": [
                        ...
                        {
                            "week": "2",
                            "trades": [
                                ...
                                {
                                    "partners": ["Sach", "Owen"],
                                    "acquired": ["Ezekiel Elliott", "Josh Jacobs", "$5 FAAB"],
                                    "sent": ["Raheem Mostert", "Jeff Wilson", "Antonio Gibson"]
                                },
                                ...
                            ]
                        },
                        ...
                },
                "adds": {
                    "total": 25,
                    "by_week": [
                        ...
                        {"week": "2", "players": ["Amon-Ra St. Brown", "Travis Kelce"]},
                        ...
                    ]
                },
                "drops": {
                    "total": 20,
                    "by_week": [
                        ...
                        {"week": "2", "players": ["Gus Edwards"]}
                        ...
                    ]
                }
            }
        }
        """


        if manager_name not in self._cache:
            raise ValueError(f"Manager {manager_name} not found in cache.")
        
        if year not in self._cache[manager_name]["years"]:
            raise ValueError(f"Year {year} not found for manager {manager_name} in cache.")
        
        cached_yearly_data = copy.deepcopy(self._cache[manager_name]["years"][year])

        yearly_data = {
            "manager_name": manager_name,
            "year":         year,
            "avatar_urls":  copy.deepcopy(self._cache[manager_name]["summary"]["overall_data"].get("avatar_urls", {})),
            "matchup_data": self._get_matchup_details_from_cache(manager_name, year)
        }

        # Matchup Data
        
        weekly_scores = []
        for week in cached_yearly_data.get("weeks", {}):
            week_data = copy.deepcopy(cached_yearly_data["weeks"][week]["matchup_data"])
            weekly_score_item = {
                "week":              week,
                "opponent":          week_data.get("opponent_manager", "N/A"),
                "points_for":        week_data.get("points_for", 0.0),
                "points_against":    week_data.get("points_against", 0.0),
                "result":            week_data.get("result", "N/A"),
            }
            weekly_scores.append(copy.deepcopy(weekly_score_item))
        
        yearly_data["matchup_data"]["overall"]["weekly_scores"] = weekly_scores

        
        # Transactions Data
        transaction_data = {
            "trades": {
                "total": cached_yearly_data["summary"]["transactions"]["trades"]["total"],
                "by_week": []
            },
            "adds": {
                "total": cached_yearly_data["summary"]["transactions"]["adds"]["total"],
                "by_week": []
            },
            "drops": {
                "total": cached_yearly_data["summary"]["transactions"]["drops"]["total"],
                "by_week": []
            }
        }
        
        for week in cached_yearly_data.get("weeks", {}):
            weekly_transactions = cached_yearly_data["weeks"][week]["transactions"]
            
            # Trades
            trade_item = {
                "week": week,
                "trades": self._get_weekly_trade_details_from_cache(manager_name, year, week)
            }
            transaction_data["trades"]["by_week"].append(trade_item)
            

            # Adds
            add_item = {
                "week": week,
                "players": list(weekly_transactions.get("adds", {}).get("players", {}).keys())
            }
            transaction_data["adds"]["by_week"].append(copy.deepcopy(add_item))

            # Drops
            drop_item = {
                "week": week,
                "players": list(weekly_transactions.get("drops", {}).get("players", {}).keys())
            }
            transaction_data["drops"]["by_week"].append(copy.deepcopy(drop_item))
        
        yearly_data["transactions"] = copy.deepcopy(transaction_data)
        
        return copy.deepcopy(yearly_data)


    def get_head_to_head(self, manager_1: str, manager_2: str, year: str = None) -> dict:
        """
        Returns head-to-head stats between two managers.

        EXAMPLE:
        {
            "manager_1": {
                "name": "Tommy",
                "avatar_urls": {
                    "full_size" = "https://sleepercdn.com/avatars/avatar_link1",
                    "thumbnail" = "https://sleepercdn.com/avatars/thumbs/avatar_link1"
                }
            },
                }
            "manager_2": {
                "name": "Soup",
                "avatar_urls": {
                    "full_size" = "https://sleepercdn.com/avatars/avatar_link2",
                    "thumbnail" = "https://sleepercdn.com/avatars/thumbs/avatar_link2"
                }
            },
            "overall": {
                "tommy_wins": 6,
                "soup_wins": 3,
                "ties": 0,
                
                "tommy_points_for": 1049.0,
                "tommy_average_margin_of_victory": 12.87
                "soup_points_for": 985.57,
                "soup_average_margin_of_victory": 7.83,
                
                "tommy_last_win": { # Returns {} if no last win under inputted paramaters
                    "year": "2024",
                    "week": "12",
                    "tommy_score": 131.16,
                    "soup_score": 104.82,
                    "tommy_top_3_scorers": [
                        {"name": "Indianapolis Colts", "score": 18.5, "position": "DEF", "image_url": "https://sleepercdn.com/images/team_logos/nfl/no.png"},
                        {"name": "James Conner", "score": 17.4, "position": "RB", "image_url": "https://sleepercdn.com/content/nfl/players/6904.jpg"},
                        {"name": "Kyler Murray", "score": 17.36, "position": "QB", "image_url": "https://sleepercdn.com/content/nfl/players/6904.jpg"}
                    ]
                    "soup_top_3_scorers:": [
                        ... (same structure as "tommy_top_3_scorers")
                    ]
                },
                "soup_last_win"{
                    ... (same structure as "tommy_last_win")
                },
                "tommy_biggest_blowout"{
                    ... (same structure as "tommy_last_win")
                },
                "soup_biggest_blowout"{
                    ... (same structure as "tommy_last_win")
                },


                "matchup_history": [
                    {
                        "year": "2024",
                        "week": "1",
                        "tommy_score": 131.16,
                        "soup_score": 104.82,
                        "winner": "Tommy"
                        "tommy_top_3_scorers": [
                            (same structure as "tommy_top_3_scorers above")
                        ]
                        "soup_top_3_scorers:": [
                            ... (same structure as "tommy_top_3_scorers")
                        ]
                    },
                    ...
                ]
            },
            
            "trades_between": {
                "total": 4,
                "trade_history": [
                    {
                        "year": "2019",
                        "week": "3",
                        "tommy_received": ["Tyler Lockett"],
                        "soup_received": ["Sammy Watkins", "Damien Williams"]
                    },
                    {
                        (note there are scenarios where there was a multiple team trade, they would be shown like below)
                        "year": "2019",
                        "week": "3",
                        "tommy_received": ["Tyler Lockett"],
                        "tommy_sent": ["Sammy Watkins],
                        "soup_received": ["Damien Williams"],
                        "soup_sent": ["$5 FAAB", "Tyler Lockett"],
                        "jay_received": ["$5 FAAB", "Sammy Watkins"],
                        "jay_sent": ["Damien Williams"]
                    }
                ]
            }
        }
        """
        
        return_dict = {}
        
        for manager in [manager_1, manager_2]:
        
            if manager not in self._cache:
                raise ValueError(f"Manager {manager} not found in cache.")
            if year:
                if year not in self._cache[manager]["years"]:
                    raise ValueError(f"Year {year} not found for manager {manager} in cache.")

            manager = {
                "name":         manager,
                "avatar_urls": self._cache[manager]["summary"]["overall_data"].get("avatar_urls", {})
            }

            if "manager_1" not in return_dict:
                return_dict["manager_1"] = copy.deepcopy(manager)
            else:
                return_dict["manager_2"] = copy.deepcopy(manager)



        return_dict["overall"] = self._get_head_to_head_overall_from_cache(manager_1, manager_2, year)

        return_dict["matchup_history"] = self._get_head_to_head_overall_from_cache(manager_1, manager_2, year, list_all_matchups=True)

        trades_between = self._get_trade_history_between_two_managers(manager_1, manager_2, year)
        return_dict["trades_between"] = {
            "total": len(trades_between),
            "trade_history": trades_between
        }

        return copy.deepcopy(trades_between)

        
    def get_manager_transactions(self, 
                                manager_name: str,
                                year: str = None, 
                                transaction_type: str = None,
                                limit: int = 50, 
                                offset: int = 0) -> dict:
        """
        Returns transaction history for a manager with filtering.
        
        Get transaction history for a manager with filtering options. Frontend sends:
            URL parameter: manager_name
            Query parameters (optional):
            year: Filter by year
            type: Filter by transaction type ("trade", "add", "drop", "add_and_or_drop")
                # NOTE: "add_and_or_drop" covers both adds and drops and transactions when a player is added and dropped in the same transaction
                # NOTE: "faab_spent" is null when FAAB was not implemented in league settings for that year or when a player was added as a free agent without FAAB spending
            limit: Number of results to return (default: 50)
            offset: Pagination offset (default: 0)
        
        EXAMPLE:
        {
            "manager_name": "Tommy",
            "avatar_urls": {
                "full_size" = "https://sleepercdn.com/avatars/avatar_link",
                "thumbnail" = "https://sleepercdn.com/avatars/thumbs/avatar_link"
            },
            "total_count": 264,
            "transactions": [
                {
                    "year": "2019",
                    "week": "1",
                    "type": "trade",
                    "partners": ["Jay"],
                    "acquired": ["Aaron Rodgers", "Billiam's 2019 Round 9 Draft Pick"],
                    "sent": ["Anthony's 2019 Round 10 Draft Pick", "$5 FAAB"],
                    "transaction_id" = "abc123xyz"
                },
                {
                    "year": "2019",
                    "week": "1",
                    "type": "trade",
                    "partners": ["Jay", "Owen"],
                    "acquired": ["Aaron Rodgers", "Billiam's 2019 Round 9 Draft Pick"],
                    "sent": ["Anthony's 2019 Round 10 Draft Pick", "$5 FAAB"],
                    "transaction_id" = "abc123xyz"
                },
                {
                    "year": "2024",
                    "week": "2",
                    "type": "add",
                    "player": "Isaiah Likely",
                    "faab_spent": 46,
                    "transaction_id" = "abc123xyz"
                },
                {
                    "year": "2024",
                    "week": "2",
                    "type": "drop",
                    "player": "Gus Edwards",
                    "transaction_id" = "abc123xyz"
                },
                {
                    "year": "2019",
                    "week": "3",
                    "type": "add_and_drop",
                    "added_player": "Travis Kelce",
                    "dropped_player": "Tyler Higbee",
                    "faab_spent": null,
                    "transaction_id" = "abc123xyz"
                }
            ]
        }
        
        """
        

        if manager_name not in self._cache:
            raise ValueError(f"Manager {manager_name} not found in cache.")
        if year:
            if year not in self._cache[manager_name]["years"]:
                raise ValueError(f"Year {year} not found for manager {manager_name} in cache.")
        
        
        transaction_history = {
            "manager_name": manager_name,
            "avatar_urls":  self._cache[manager_name]["summary"]["overall_data"].get("avatar_urls", {}),
            "total_count":  0,
            "transactions": []
        }

        # Gather transactions based on filters
        filtered_transactions = []
        years_to_check = [year] if year else list(self._cache[manager_name]["years"].keys())
        
        for yr in years_to_check:
            yearly_data = self._cache[manager_name]["years"][yr]
            for week in yearly_data.get("weeks", {}):
                weekly_transactions = yearly_data["weeks"][week]["transactions"]
                
                # Trades
                if transaction_type in [None, "trade"]:
                    for transaction_id in weekly_transactions.get("trades", []).get("transaction_ids", []):
                        trade_details = self._transaction_id_cache.get(transaction_id, {})
                        if trade_details:
                            
                            acquired = []
                            sent     = []

                            for player in trade_details.get("trade_details", {}):
                                if trade_details["trade_details"][player].get("new_manager", None) == manager_name:
                                    acquired.append(player)
                                elif trade_details["trade_details"][player].get("old_manager", None) == manager_name:
                                    sent.append(player)

                            transaction_item = {
                                "year":          yr,
                                "week":          week,
                                "type":          "trade",
                                "partners":      trade_details.get("managers_involved", []).remove(manager_name),
                                "acquired":      acquired,
                                "sent":          sent,
                                "transaction_id": transaction_id
                            }
                            filtered_transactions.append(copy.deepcopy(transaction_item))
                        
                
                # Adds
                if transaction_type in [None, "add", "add_and_or_drop"]:
                    for transaction_id in weekly_transactions.get("adds", []).get("transaction_ids", []):
                        add_details = self._transaction_id_cache.get(transaction_id, {})
                        if add_details:
                            
                            # Only include adds portion of a transaction for "add" filter
                            if "add" in add_details.get("types", []):
                                
                                transaction_item = {
                                    "year":          yr,
                                    "week":          week,
                                    "type":          "add",
                                    "player":        add_details.get("add", ""),
                                    "faab_spent":    add_details.get("faab_spent", None), # None if FAAB not implemented yet or a free agent add
                                    "transaction_id": transaction_id
                                }
                                filtered_transactions.append(copy.deepcopy(transaction_item))
                

                # Drops
                if transaction_type in [None, "drop", "add_and_or_drop"]:
                    for transaction_id in weekly_transactions.get("drops", []).get("transaction_ids", []):
                        drop_details = self._transaction_id_cache.get(transaction_id, {})
                        if drop_details:
                            
                            # Only include drops portion of a transaction for "drop" filter
                            if "drop" in drop_details.get("types", []):
                                
                                transaction_item = {
                                    "year":          yr,
                                    "week":          week,
                                    "type":          "drop",
                                    "player":        drop_details.get("drop", ""),
                                    "transaction_id": transaction_id
                                }
                                filtered_transactions.append(copy.deepcopy(transaction_item))
                
                # Adds and Drops
                if transaction_type in [None, "add_and_or_drop"]:
                    
                    # 
                    for transaction_id in weekly_transactions.get("adds", []).get("transaction_ids", []):
                        add_drop_details = self._transaction_id_cache.get(transaction_id, {})
                        if add_drop_details:
                            
                            # Only include add_and_drop transactions
                            if "add" in add_drop_details.get("types", []) and "drop" in add_drop_details.get("types", []):
                                transaction_item = {
                                    "year":          yr,
                                    "week":          week,
                                    "type":          "add_and_drop",
                                    "added_player":  add_drop_details.get("add", ""),
                                    "dropped_player":add_drop_details.get("drop", ""),
                                    "faab_spent":    add_drop_details.get("faab_spent", None), # None if FAAB not implemented yet or a free agent add/drop
                                    "transaction_id": transaction_id
                                }
                                filtered_transactions.append(copy.deepcopy(transaction_item))
                
        # Set total count before pagination
        transaction_history["total_count"] = len(filtered_transactions)

        # Apply pagination
        paginated_transactions = filtered_transactions[offset:offset+limit] 
        
        # Set transactions in output
        transaction_history["transactions"] = copy.deepcopy(paginated_transactions)
        
        return copy.deepcopy(transaction_history)


    def get_manager_awards(self, manager_name: str) -> dict:
        """
        Returns awards and achievements for a manager.
        
        Get awards/achievements for a manager (for fun stats display).

        EXAMPLE:
        {
            "manager_name": "Tommy",
            "avatar_urls": {
                "full_size" = "https://sleepercdn.com/avatars/avatar_link",
                "thumbnail" = "https://sleepercdn.com/avatars/thumbs/avatar_link"
            },
            "awards": {
                "first_place": 0,
                "second_place": 1,
                "third_place": 2,
                "playoff_appearances": 5,
                "most_trades_in_year": {
                    "count": 25,
                    "year": "2022"
                },
                    "biggest_faab_bid": {
                    "player": "Isaiah Likely",
                    "amount": 46,
                    "year": "2023"
                },
                "highest_weekly_score": {
                    "score": 163.56,
                    "week": "1",
                    "year": "2019",
                    "opponent": "Luke"
                    "tommy_top_3_scorers": [
                        {"name": "Indianapolis Colts", "score": 28.5, "position": "DEF", "image_url": "https://sleepercdn.com/images/team_logos/nfl/no.png"},
                        {"name": "James Conner", "score": 27.4, "position": "RB", "image_url": "https://sleepercdn.com/content/nfl/players/6904.jpg"},
                        {"name": "Kyler Murray", "score": 26.36, "position": "QB", "image_url": "https://sleepercdn.com/content/nfl/players/6904.jpg"}
                    ],
                    "luke_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ]
                },
                "lowest_weekly_score": {
                    "score": 43.23,
                    "week": "8",
                    "year": "2020",
                    "opponent": "Davey"
                    "tommy_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ],
                    "davey_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ]
                },
                "biggest_blowout_win": {
                    "differential": 45.5,
                    "week": "3",
                    "year": "2021",
                    "opponent": "Parker"
                    "tommy_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ],
                    "parker_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ]
                },
                "biggest_blowout_loss": {
                    "differential": -52.3,
                    "week": "8",
                    "year": "2020",
                    "opponent": "Christian"
                    "tommy_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ],
                    "christian_top_3_scorers": [
                        ... (same structure as "tommy_top_3_scorers" above)
                    ]
                }
            }
        }

        """

        if manager_name not in self._cache:
            raise ValueError(f"Manager {manager_name} not found in cache.")
        
        awards_data = {
            "manager_name": manager_name,
            "avatar_urls":  self._cache[manager_name]["summary"]["overall_data"].get("avatar_urls", {}),
            "awards":       self._get_manager_awards_from_cache(manager_name)
        }
        

        score_awards = self._get_manager_score_awards_from_cache(manager_name)

        awards_data["awards"].update(copy.deepcopy(score_awards))

        

    
    
    
    
    
    # ---------- Internal Public Helper Methods ----------
    def _get_matchup_details_from_cache(self, manager_name: str, year: str = None) -> dict:
        """Helper to extract matchup details from cache for a manager."""
        from decimal import Decimal

        matchup_data = {
            "overall":        {},
            "regular_season": {},
            "playoffs":       {}
        }
        
        cached_matchup_data = copy.deepcopy(self._cache[manager_name]["summary"]["matchup_data"])
        if year:
            cached_matchup_data = copy.deepcopy(self._cache[manager_name]["years"][year]["summary"]["matchup_data"])

        for season_state in ["overall", "regular_season", "playoffs"]:
            
            # Handle no playoff appearances
            if season_state == "playoffs":
                playoff = True
                playoff_appearances = self._cache[manager_name]["summary"]["overall_data"]["playoff_appearances"]
                if len(playoff_appearances) == 0:
                    playoff = False
                elif year is not None and year not in self._cache[manager_name]["years"]:
                    playoff = False

                if playoff == False:
                    matchup_data[season_state] = {
                        "record":                     "0-0-0",
                        "win_percentage":             0.0,
                        "total_points_for":           0,
                        "total_points_against":       0,
                        "point_differential":         0,
                        "average_points_for":         0.0,
                        "average_points_against":     0.0,
                        "average_point_differential": 0.0
                    }
                    continue
            
            
            
            # Extract record components
            num_wins = cached_matchup_data[season_state]["wins"]["total"]
            num_losses = cached_matchup_data[season_state]["losses"]["total"]
            num_ties = cached_matchup_data[season_state]["ties"]["total"]

            matchup_data[season_state]["record"] = f"{num_wins}-{num_losses}-{num_ties}"

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
            

            matchup_data[season_state]["total_points_for"]           = total_points_for
            matchup_data[season_state]["total_points_against"]       = total_points_against
            matchup_data[season_state]["point_differential"]         = total_point_differential
            matchup_data[season_state]["average_points_for"]         = average_points_for
            matchup_data[season_state]["average_points_against"]     = average_points_against
            matchup_data[season_state]["average_point_differential"] = average_point_differential

        return copy.deepcopy(matchup_data)

    def _get_trasaction_details_from_cache(self, manager_name: str, year: str = None) -> dict:
        """Helper to extract transaction summary from cache for a manager."""
        transaction_summary = {
            "trades":      {},
            "adds":        {},
            "drops":       {},
            "faab":        {}
        }

        cached_transaction_data = copy.deepcopy(self._cache[manager_name]["summary"]["transactions"])
        if year:
            cached_transaction_data = copy.deepcopy(self._cache[manager_name]["years"][year]["summary"]["transactions"])
        
        
        trades = {
            "total":              cached_transaction_data["trades"]["total"],
            "top_trade_partners": self._get_top_three_of_dict(copy.deepcopy(cached_transaction_data["trades"]["trade_partners"]))
        }

        # ---- Trades Summary ----
        
        # Most Aquired Players
        trade_players_acquired = cached_transaction_data["trades"]["trade_players_acquired"]
        most_acquired_players = self._get_top_three_of_dict(copy.deepcopy(trade_players_acquired))
        for player in most_acquired_players:
            player_details = copy.deepcopy(trade_players_acquired[player["name"]])
            player["from"] = player_details.get("trade_partners", {})
        trades["most_acquired_players"] = most_acquired_players

        # Most Sent Players
        trade_players_sent = cached_transaction_data["trades"]["trade_players_sent"]
        most_sent_players = self._get_top_three_of_dict(copy.deepcopy(trade_players_sent))
        for player in most_sent_players:
            player_details = copy.deepcopy(trade_players_sent[player["name"]])
            player["to"] = player_details.get("trade_partners", {})
        trades["most_sent_players"] = most_sent_players

        transaction_summary["trades"] = trades


        # ---- Adds Summary ----
        adds = {
            "total":             cached_transaction_data["adds"]["total"],
            "top_players_added": self._get_top_three_of_dict(copy.deepcopy(cached_transaction_data["adds"]["players"]))
        }
        transaction_summary["adds"] = adds 
       

        # ---- Drops Summary ----
        drops = {
                "total":               cached_transaction_data["drops"]["total"],
                "top_players_dropped": self._get_top_three_of_dict(copy.deepcopy(cached_transaction_data["drops"]["players"]))
        }
        transaction_summary["drops"] = drops


        # ---- FAAB Summary ----
        faab = {
            "total_spent": abs(cached_transaction_data["faab"]["total_lost_or_gained"]),
            "biggest_acquisitions": self._get_top_three_of_dict(copy.deepcopy(cached_transaction_data["faab"]["players"]), key_name = "amount")
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
        transaction_summary["faab"] = faab


        # Return final transaction summary
        return copy.deepcopy(transaction_summary)

    def _get_overall_data_details_from_cache(self, manager_name: str) -> dict:
        """Helper to extract overall data details from cache for a manager."""
        cached_overall_data = copy.deepcopy(self._cache[manager_name]["summary"]["overall_data"])

        
        overall_data = {
            "playoff_appearances": len(cached_overall_data.get("playoff_appearances", []))
        }

        # ----- Other Overall Data -----
        placements = []
        best_finish = None
        championships = 0
        for year in cached_overall_data.get("placement", {}):
            if cached_overall_data["placement"][year] == 1:
                championships += 1
            if best_finish is None or cached_overall_data["placement"][year] < best_finish:
                best_finish = cached_overall_data["placement"][year]
            placement_item = {
                "year": year,
                "placement": cached_overall_data["placement"][year]
            }
            placements.append(placement_item)

        overall_data["placements"]    = placements
        overall_data["best_finish"]   = best_finish if best_finish is not None else 0
        overall_data["championships"] = championships

        return copy.deepcopy(overall_data)

    def _get_head_to_head_details_from_cache(self, manager_name: str, year: str = None, opponent: str = None) -> dict:
        """Helper to extract head-to-head details from cache for a manager."""
        head_to_head_data = {}
        
        cached_head_to_head_data = copy.deepcopy(self._cache[manager_name]["summary"]["matchup_data"]["overall"])
        if year:
            cached_head_to_head_data = copy.deepcopy(self._cache[manager_name]["years"][year]["summary"]["matchup_data"]["overall"])
        
        if opponent:
            head_to_head_data = {
                "wins":           cached_head_to_head_data["wins"]["opponents"].get(opponent, 0),
                "losses":         cached_head_to_head_data["losses"]["opponents"].get(opponent, 0),
                "ties":           cached_head_to_head_data["ties"]["opponents"].get(opponent, 0),
                "points_for":     cached_head_to_head_data["points_for"]["opponents"].get(opponent, 0.0),
                "points_against": cached_head_to_head_data["points_against"]["opponents"].get(opponent, 0.0)
            }
            return copy.deepcopy(head_to_head_data)
        
        
        for opponent in cached_head_to_head_data.get("points_for", {}).get("opponents", {}):

            head_to_head_data[opponent] = {
                "wins":           cached_head_to_head_data["wins"]["opponents"].get(opponent, 0),
                "losses":         cached_head_to_head_data["losses"]["opponents"].get(opponent, 0),
                "ties":           cached_head_to_head_data["ties"]["opponents"].get(opponent, 0),
                "points_for":     cached_head_to_head_data["points_for"]["opponents"].get(opponent, 0.0),
                "points_against": cached_head_to_head_data["points_against"]["opponents"].get(opponent, 0.0)
            }
        
        return copy.deepcopy(head_to_head_data)

    def _get_weekly_trade_details_from_cache(self, manager_name: str, year: str, week: str) -> list:
        weekly_trade_transaction_ids = copy.deepcopy(self._cache.get(manager_name, {}).get("years", {}).get(year, {}).get("weeks", {}).get(week, {}).get("transactions", {}).get("trades", {}).get("transaction_ids", []))

        trades = []
        for transaction_id in weekly_trade_transaction_ids:
            trade_dict = {
                "partners": [],
                "acquired": [],
                "sent":     []
            }
            trade_details = copy.deepcopy(self._transaction_id_cache.get(transaction_id, {})).get("trade_details")
            if trade_details == {}:
                print(f"WARNING: trade details empty for transaction_id: {transaction_id}")
            
            trade_dict["partners"] = copy.deepcopy(self._transaction_id_cache.get(transaction_id, {}).get("managers_involved"))
            trade_dict["partners"].remove(manager_name)
            for player in trade_details:
                if manager_name == trade_details[player]["old_manager"]:
                    trade_dict["sent"].append(player)
                elif manager_name == trade_details[player]["new_manager"]:
                    trade_dict["acquired"].append(player)
            
            trades.append(trade_dict)
        
        return trades

    def _get_head_to_head_overall_from_cache(self, manager_1: str, manager_2: str, year: str = None, list_all_matchups: bool = False) -> dict | list:
        from decimal import Decimal
        if list_all_matchups:
            years = list(self._cache[manager_1].get("years", {}).keys())
            if year:
                years = [year]
            matchup_history = []
        else:
            head_to_head_overall = {}


            head_to_head_data = self._get_head_to_head_details_from_cache(manager_1, year, manager_2)

            head_to_head_overall[f"{manager_1.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("wins")
            head_to_head_overall[f"{manager_2.lower().replace(' ', '_')}_wins"] = head_to_head_data.get("losses")
            head_to_head_overall[f"ties"] = head_to_head_data.get("ties")


            # Get average margin of victory, last win, biggest blowout
            years = list(self._cache[manager_1].get("years", {}).keys())
            manager_1_points_for = self._cache[manager_1].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager_2, 0.0)
            manager_2_points_for = self._cache[manager_2].get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager_1, 0.0)
            if year:
                years = [year]
                manager_1_points_for = self._cache[manager_1].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager_2, 0.0)
                manager_2_points_for = self._cache[manager_2].get("years", {}).get(year, {}).get("summary", {}).get("matchup_data", {}).get("overall", {}).get("points_for", {}).get("opponents", {}).get(manager_1, 0.0)

            manager_1_victory_margins = []
            manager_1_last_win        = {}
            manager_1_biggest_blowout = {}

            manager_2_victory_margins = []
            manager_2_last_win        = {}
            manager_2_biggest_blowout = {}
        

        for y in years:
            
            weeks = copy.deepcopy(self._cache[manager_1]["years"][y]["weeks"])
            
            for w in weeks:
                matchup_data = copy.deepcopy(weeks.get(w, {}).get("matchup_data", {}))

                # Manager didn't play that week but had transactions
                if matchup_data == {}:
                    continue

                validation = self._validate_matchup_data(matchup_data)
                if "Warning" in validation:
                    print(f"{validation} {manager_1}, year {y}, week {w}")
                    continue

                # we got our matchup
                if manager_2 == matchup_data.get("opponent_manager", ""):

                    manager_1_score = matchup_data.get("points_for")
                    manager_2_score = matchup_data.get("points_against")
                    
                    # manager 1 won
                    if matchup_data.get("result", "") == "win":

                        if list_all_matchups:
                            matchup_for_list = {
                                "year": y,
                                "week": w,
                                f"{manager_1.lower().replace(' ', '_')}_score": manager_1_score,
                                f"{manager_2.lower().replace(' ', '_')}_score": manager_2_score,
                                "winner": manager_1
                            }
                            self._get_top_3_scorers_from_matchup_data(matchup_for_list, manager_1, manager_2)
                            matchup_history.append(matchup_for_list)
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
                            manager_1_last_win["year"] = y
                            manager_1_last_win["week"] = w
                            manager_1_last_win[f"{manager_1.lower().replace(' ', '_')}_score"] = manager_1_score
                            manager_1_last_win[f"{manager_2.lower().replace(' ', '_')}_score"] = manager_2_score

                        
                        
                        # see if this matchup is the biggest blowout for manager_1
                        apply = False
                        if manager_1_biggest_blowout.get("year", "") == "": # initial
                            apply = True
                        elif manager_1_victory_margin == sorted(manager_1_victory_margins, reverse = True)[0]: # current victory margin is largest
                            apply = True
                        
                        if apply:
                            manager_1_biggest_blowout["year"] = y
                            manager_1_biggest_blowout["week"] = w
                            manager_1_biggest_blowout[f"{manager_1.lower().replace(' ', '_')}_score"] = manager_1_score
                            manager_1_biggest_blowout[f"{manager_2.lower().replace(' ', '_')}_score"] = manager_2_score
                    
                    # manager_2 won
                    if matchup_data.get("result", "") == "loss":
                        
                        if list_all_matchups:
                            matchup_for_list = {
                                "year": y,
                                "week": w,
                                f"{manager_1.lower().replace(' ', '_')}_score": manager_1_score,
                                f"{manager_2.lower().replace(' ', '_')}_score": manager_2_score,
                                "winner": manager_2
                            }
                            self._get_top_3_scorers_from_matchup_data(matchup_for_list, manager_1, manager_2)
                            matchup_history.append(matchup_for_list)
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
                            manager_2_last_win["year"] = y
                            manager_2_last_win["week"] = w
                            manager_2_last_win[f"{manager_2.lower().replace(' ', '_')}_score"] = manager_2_score
                            manager_2_last_win[f"{manager_1.lower().replace(' ', '_')}_score"] = manager_1_score

                        
                        
                        # see if this matchup is the biggest blowout for manager_1
                        apply = False
                        if manager_2_biggest_blowout.get("year", "") == "": # initial
                            apply = True
                        elif manager_2_victory_margin == sorted(manager_2_victory_margins, reverse = True)[0]: # current victory margin is largest
                            apply = True
                        
                        if apply:
                            manager_2_biggest_blowout["year"] = y
                            manager_2_biggest_blowout["week"] = w
                            manager_2_biggest_blowout[f"{manager_2.lower().replace(' ', '_')}_score"] = manager_2_score
                            manager_2_biggest_blowout[f"{manager_1.lower().replace(' ', '_')}_score"] = manager_1_score
                    
                    else: # Tie
                        
                        if list_all_matchups:
                            matchup_for_list = {
                                "year": y,
                                "week": w,
                                f"{manager_1.lower().replace(' ', '_')}_score": manager_1_score,
                                f"{manager_2.lower().replace(' ', '_')}_score": manager_2_score,
                                "winner": "Tie"
                            }
                            self._get_top_3_scorers_from_matchup_data(matchup_for_list, manager_1, manager_2)
                            matchup_history.append(matchup_for_list)
                            continue
        
        if list_all_matchups:
            return copy.deepcopy(matchup_history)


                    
        # average margin of victory
        manager_1_average_margin_of_victory =  float(Decimal(sum(manager_1_victory_margins) / len(manager_1_victory_margins)).quantize(Decimal('0.01')))
        manager_2_average_margin_of_victory =  float(Decimal(sum(manager_2_victory_margins) / len(manager_2_victory_margins)).quantize(Decimal('0.01')))
        
        # import the top 3 scorers of each manager for these games
        self._get_top_3_scorers_from_matchup_data(manager_1_last_win,        manager_1, manager_2)
        self._get_top_3_scorers_from_matchup_data(manager_2_last_win,        manager_1, manager_2)
        self._get_top_3_scorers_from_matchup_data(manager_1_biggest_blowout, manager_1, manager_2)
        self._get_top_3_scorers_from_matchup_data(manager_2_biggest_blowout, manager_1, manager_2)

        
        # put all the data in
        head_to_head_overall[f"{manager_1.lower().replace(' ', '_')}_points_for"]                = manager_1_points_for
        head_to_head_overall[f"{manager_1.lower().replace(' ', '_')}_average_margin_of_victory"] = manager_1_average_margin_of_victory
        head_to_head_overall[f"{manager_2.lower().replace(' ', '_')}_points_for"]                = manager_2_points_for
        head_to_head_overall[f"{manager_2.lower().replace(' ', '_')}_average_margin_of_victory"] = manager_2_average_margin_of_victory

        head_to_head_overall[f"{manager_1.lower().replace(' ', '_')}_last_win"]        = copy.deepcopy(manager_1_last_win)
        head_to_head_overall[f"{manager_2.lower().replace(' ', '_')}_last_win"]        = copy.deepcopy(manager_2_last_win)
        head_to_head_overall[f"{manager_1.lower().replace(' ', '_')}_biggest_blowout"] = copy.deepcopy(manager_1_biggest_blowout)
        head_to_head_overall[f"{manager_2.lower().replace(' ', '_')}_biggest_blowout"] = copy.deepcopy(manager_2_biggest_blowout)
        

        return copy.deepcopy(head_to_head_overall)

    def _get_trade_history_between_two_managers(self, manager_1: str, manager_2: str, year: str = None) -> list:
        
        

        years = list(self._cache[manager_1].get("years", {}).keys())
        if year:
            years = [year]
        
        # Gather all transaction IDs for manager_1
        transaction_ids = []
        for y in years:
            weeks = copy.deepcopy(self._cache[manager_1]["years"][y]["weeks"])
            for w in weeks:
                weekly_trade_transaction_ids = copy.deepcopy(self._cache.get(manager_1, {}).get("years", {}).get(y, {}).get("weeks", {}).get(w, {}).get("transactions", {}).get("trades", {}).get("transaction_ids", []))
                transaction_ids.extend(weekly_trade_transaction_ids)


        # Filter to only those involving both managers
        for tid in copy.deepcopy(transaction_ids):
            if manager_2 not in self._transaction_id_cache.get(tid, {}).get("managers_involved", []):
                transaction_ids.remove(tid)


        trades_between = []
        

        for t in transaction_ids:
            trans =  self._transaction_id_cache[t]
            trade_item = {
                "year": trans["year"],
                "week": trans["week"],
                f"{manager_1.lower().replace(' ', '_')}_received": [],
                f"{manager_1.lower().replace(' ', '_')}_sent": [],
                f"{manager_2.lower().replace(' ', '_')}_received": [],
                f"{manager_2.lower().replace(' ', '_')}_sent": [],
            }

            for m in trans["managers_involved"]:
                if m not in [manager_1, manager_2]:
                    trade_item[f"{m.lower().replace(' ', '_')}_received"] = []
                    trade_item[f"{m.lower().replace(' ', '_')}_sent"] = []
            
            for player in trans['trade_details']:
                old_manager = trans['trade_details'][player]['old_manager'].lower().replace(' ', '_')
                new_manager = trans['trade_details'][player]['new_manager'].lower().replace(' ', '_')

                trade_item[f"{old_manager}_sent"].append(player)
                trade_item[f"{new_manager}_received"].append(player)

            trades_between.append(copy.deepcopy(trade_item))
        
        return trades_between

    def _get_manager_awards_from_cache(self, manager_name: str) -> dict:
        """Helper to extract awards/achievements from cache for a manager."""
        from decimal import Decimal

        awards = {}

        cached_overall_data = copy.deepcopy(self._cache[manager_name]["summary"]["overall_data"])
        
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
        awards.update(copy.deepcopy(placement_counts))


        # Most Trades in a Year
        most_trades_in_year = {
            "count": 0,
            "year":  ""
        }
        for year in self._cache[manager_name].get("years", {}):
            num_trades = self._cache[manager_name]["years"][year]["summary"]["transactions"]["trades"]["total"]
            if num_trades > most_trades_in_year["count"]:
                most_trades_in_year["count"] = num_trades
                most_trades_in_year["year"] = year
        awards["most_trades_in_year"] = copy.deepcopy(most_trades_in_year)


        # Biggest FAAB Bid
        biggest_faab_bid = {
            "player": "",
            "amount": 0,
            "year":   ""
        }
        for player in self._cache[manager_name].get("summary", {}).get("transactions", {}).get("faab", {}).get("players", {}):
            faab_spent = self._cache[manager_name]["summary"]["transactions"]["faab"]["players"][player]
            if faab_spent > biggest_faab_bid["amount"]:
                biggest_faab_bid["player"] = player
                biggest_faab_bid["amount"] = faab_spent
        # Find year of biggest bid
        for year in self._cache[manager_name].get("years", {}):
            if player in self._cache[manager_name]["years"][year]["summary"]["transactions"]["faab"]["players"]:
                if self._cache[manager_name]["years"][year]["summary"]["transactions"]["faab"]["players"][player] == faab_spent:
                    biggest_faab_bid["year"] = year
                    break
        awards["biggest_faab_bid"] = copy.deepcopy(biggest_faab_bid)

        
        return copy.deepcopy(awards)

    def _get_manager_score_awards_from_cache(self, manager_name: str) -> dict:
        """Helper to extract score-related awards from cache for a manager."""
        from decimal import Decimal

        score_awards = {}


        highest_weekly_score = {
            "score": 0.0,
            "week":  "",
            "year":  "",
            "opponent": "",
            "top_3_scorers": []
        }
        lowest_weekly_score = {
            "score": float('inf'),
            "week":  "",
            "year":  "",
            "opponent": "",
            "top_3_scorers": []
        }
        biggest_blowout_win = {
            "differential": 0.0,
            "week":  "",
            "year":  "",
            "opponent": "",
            "top_3_scorers": []
        }
        biggest_blowout_loss = {
            "differential": 0.0,
            "week":  "",
            "year":  "",
            "opponent": "",
            "top_3_scorers": []
        }


        for year in self._cache[manager_name].get("years", {}):
            weeks = copy.deepcopy(self._cache[manager_name]["years"][year]["weeks"])
            for week in weeks:
                matchup_data = copy.deepcopy(weeks.get(week, {}).get("matchup_data", {}))

                # Manager didn't play that week but had transactions
                if "matchup_data" == {}:
                    continue

                validation = self._validate_matchup_data(matchup_data)
                if "Warning" in validation:
                    print(f"{validation} {manager_name}, year {year}, week {week}")
                    continue

                points_for     = matchup_data.get("points_for", 0.0)
                points_against = matchup_data.get("points_against", 0.0)
                point_differential = float(Decimal((points_for - points_against)).quantize(Decimal('0.01')))

                # Highest Weekly Score
                if points_for > highest_weekly_score["score"]:
                    highest_weekly_score             = {} # reset
                    highest_weekly_score["score"]    = points_for
                    highest_weekly_score["week"]     = week
                    highest_weekly_score["year"]     = year
                    highest_weekly_score["opponent"] = matchup_data.get("opponent_manager", "")
                    self._get_top_3_scorers_from_matchup_data(highest_weekly_score, manager_name, matchup_data.get("opponent_manager", ""))

                # Lowest Weekly Score
                if points_for < lowest_weekly_score["score"]:
                    lowest_weekly_score             = {} # reset
                    lowest_weekly_score["score"]    = points_for
                    lowest_weekly_score["week"]     = week
                    lowest_weekly_score["year"]     = year
                    lowest_weekly_score["opponent"] = matchup_data.get("opponent_manager", "")
                    self._get_top_3_scorers_from_matchup_data(lowest_weekly_score, manager_name, matchup_data.get("opponent_manager", ""))

                # Biggest Blowout Win
                if matchup_data.get("result", "") == "win" and point_differential > biggest_blowout_win["differential"]:
                    biggest_blowout_win                 = {} # reset
                    biggest_blowout_win["differential"] = point_differential
                    biggest_blowout_win["week"]         = week
                    biggest_blowout_win["year"]         = year
                    biggest_blowout_win["opponent"]     = matchup_data.get("opponent_manager", "")
                    self._get_top_3_scorers_from_matchup_data(biggest_blowout_win, manager_name, matchup_data.get("opponent_manager", ""))

                # Biggest Blowout Loss
                if matchup_data.get("result", "") == "loss" and point_differential < biggest_blowout_loss["differential"]:
                    biggest_blowout_loss                 = {} # reset
                    biggest_blowout_loss["differential"] = point_differential
                    biggest_blowout_loss["week"]         = week
                    biggest_blowout_loss["year"]         = year
                    biggest_blowout_loss["opponent"]     = matchup_data.get("opponent_manager", "")
                    self._get_top_3_scorers_from_matchup_data(biggest_blowout_loss, manager_name, matchup_data.get("opponent_manager", ""))

        score_awards["highest_weekly_score"] = copy.deepcopy(highest_weekly_score)
        score_awards["lowest_weekly_score"]  = copy.deepcopy(lowest_weekly_score)
        score_awards["biggest_blowout_win"]  = copy.deepcopy(biggest_blowout_win)
        score_awards["biggest_blowout_loss"] = copy.deepcopy(biggest_blowout_loss)

        return copy.deepcopy(score_awards)




    # ---------- Internal Save/Load Methods ----------
    def _load(self):
        """Load the entire manager metadata cache."""
        self._cache = load_cache(MANAGER_METADATA_CACHE_FILE, initialize_with_last_updated_info=False)

    def save(self):
        """Save the entire manager metadata cache."""
        save_cache(MANAGER_METADATA_CACHE_FILE, self._cache)
        save_cache(TRANSACTION_IDS_FILE, self._transaction_id_cache)





    # ---------- Internal Helper Methods ----------
    def _clear_weekly_metadata(self):
        """Clear weekly metadata used during caching sessions."""
        if self._year == "2024" and self._week == "17":
            self._weekly_roster_ids = {}
        self._week = None
        self._year = None

    def _set_defaults_if_missing(self, roster_id: int):
        """Helper to initialize nested structures if missing."""

        manager = self._weekly_roster_ids.get(roster_id, None)

        if manager not in self._cache:
            self._cache[manager] = {"summary": copy.deepcopy(self._top_level_summary_template), "years": {}}
        #######
        if self._year not in self._cache[manager]["years"]:
            self._cache[manager]["years"][self._year] = {
                "summary": copy.deepcopy(self._yearly_summary_template),
                "roster_id": None,
                "weeks": {}
            }
        
        # Initialize week template if missing
        if self._week not in self._cache[manager]["years"][self._year]["weeks"]:

            # Differentiate between playoff and non-playoff weeks
            if self._get_season_state() == "playoffs" and roster_id not in self._playoff_roster_ids:
                self._cache[manager]["years"][self._year]["weeks"][self._week] = copy.deepcopy(self._weekly_summary_template_not_in_playoffs)
            else:
                self._cache[manager]["years"][self._year]["weeks"][self._week] = copy.deepcopy(self._weekly_summary_template)
        
        if self._use_faab:
            self._initialize_faab_template(manager)

    def _caching_preconditions_met(self):
        """Check if preconditions for caching week data are met."""
        if len(self._weekly_roster_ids) == 0:
            # No roster IDs cached yet; nothing to do
            raise ValueError("No roster IDs cached. Cannot cache week data.")
        
        if len(self._weekly_roster_ids) % 2 == 1:
            # Sanity check: expect even number of rosters for matchups
            raise ValueError("Odd number of roster IDs cached, cannot process matchups.")
        
        if not self._year:
            raise ValueError("Year not set. Cannot cache week data.")
        if not self._week:
            raise ValueError("Week not set. Cannot cache week data.")

    def _draft_pick_decipher(self, draft_pick_dict: dict) -> str:
        """Convert draft pick dictionary to a human-readable string."""
        season = draft_pick_dict.get("season", "unknown_year")
        round_num = draft_pick_dict.get("round", "unknown_round")

        origin_team = draft_pick_dict.get("roster_id", "unknown_team")
        origin_manager = self._weekly_roster_ids.get(origin_team, "unknown_manager")

        return f"{origin_manager}'s {season} Round {round_num} Draft Pick"

    def _get_season_state(self):
        """Determine if current week is regular season or playoffs."""

        if not self._week or not self._year:
            raise ValueError("Week or Year not set. Cannot determine season state.")
        
        if not self._playoff_week_start:
            league_info = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(self._year), '')}")[0]
            self._playoff_week_start = league_info.get("settings", {}).get("playoff_week_start", None)
        
        if int(self._week) >= self._playoff_week_start:
            return "playoffs"
        return "regular_season"

    def _get_top_three_of_dict(self, data_dict: dict, key_name = "count") -> dict:
        """Helper to get top three entries of a dictionary based on values."""
        
        for key in data_dict:
            if not isinstance(data_dict[key], dict):
                break
            data_dict[key] = data_dict[key]["total"]
        
        
        sorted_items = sorted(data_dict.items(), key=lambda item: item[1], reverse=True)
        
        # Handle ties for third place
        for i in range(2, len(sorted_items)):
            if sorted_items[i][1] != sorted_items[i+1][1]:
                break
        top_three = dict(sorted_items[:i+1])

        items = []
        for item in top_three:
            long_dict = {}
            long_dict["name"] = item
            long_dict[key_name] = top_three[item]
            items.append(copy.deepcopy(long_dict))


        return copy.deepcopy(items)

    def _validate_matchup_data(self, matchup_data: dict) -> str:

        if not matchup_data:
            return "Warning, no matchup_data"
        
        opponent_manager = matchup_data.get("opponent_manager", "")
        result           = matchup_data.get("result", "")
        points_for       = matchup_data.get("points_for", 0.0)
        points_against   = matchup_data.get("points_against", 0.0)
        
        if opponent_manager == "":
            return "Warning, no opponent_data in matchup_data"
        if opponent_manager not in list(self._cache.keys()):
            return f"Warning, {opponent_manager} is an invalid manager"
        
        if points_for <= 0.0:
            return f"Warning, invalid points_for {points_for} in matchup_data"
        if points_against <= 0.0:
            return f"Warning, invalid points_against {points_against} in matchup_data"

        if result == "":
            return "Warning, no result in matchup_data"
        if result not in ["win", "loss", "tie"]:
            return f"Warning, {result} is an invalid result in matchup_data"
        
        if result == "win" and points_for < points_against:
            return f"Warning, result is win but points_against {points_against} is more than points_for {points_for} in matchup_data"
        if result == "loss" and points_for > points_against:
            return f"Warning, result is loss but points_for {points_for} is more than points_against {points_against} in matchup_data"
        if result == "tie" and points_for != points_against:
            return f"Warning, result is tie but points_for {points_for} is not the same as points_against {points_against} in matchup_data"
        
        return ""

    def _get_top_3_scorers_from_matchup_data(self, matchup_data: dict, manager_1: str, manager_2: str):
        manager_1_starters = copy.deepcopy(STARTERS_CACHE[matchup_data["year"]][matchup_data["week"]][manager_1])
        manager_2_starters = copy.deepcopy(STARTERS_CACHE[matchup_data["year"]][matchup_data["week"]][manager_2])
        manager_1_starters.pop("Total_Points")
        manager_2_starters.pop("Total_Points")
        
        manager_1_top_scorers = []
        for player in manager_1_starters:

            player_dict = {
                "name": player,
                "score": manager_1_starters[player]["points"],
                "position": manager_1_starters[player]["position"]
            }
            if manager_1_starters[player]["player_id"].isnumeric():
                player_dict["player_url"] = f"https://sleepercdn.com/content/nfl/players/{manager_1_starters[player]['player_id']}.jpg"
            else:
                player_dict["player_url"] = f"https://sleepercdn.com/images/team_logos/nfl/{manager_1_starters[player]['player_id']}.png"


            if len(manager_1_top_scorers) == 0:
                manager_1_top_scorers.append(player_dict)
            else:
                inserted = False
                for i in range(0, len(manager_1_top_scorers)):
                    if manager_1_starters[player]["points"] > manager_1_top_scorers[i]["score"]:
                        manager_1_top_scorers.insert(i, player_dict)
                        if len(manager_1_top_scorers) > 3:
                            manager_1_top_scorers.pop()
                        inserted = True
                        break

                # If not inserted and we have fewer than 3, append to end
                if not inserted and len(manager_1_top_scorers) < 3:
                    manager_1_top_scorers.append(player_dict)
        

        manager_2_top_scorers = []
        for player in manager_2_starters:

            player_dict = {
                "name": player,
                "score": manager_2_starters[player]["points"],
                "position": manager_2_starters[player]["position"]
            }
            if manager_2_starters[player]["player_id"].isnumeric():
                player_dict["player_url"] = f"https://sleepercdn.com/content/nfl/players/{manager_2_starters[player]['player_id']}.jpg"
            else:
                player_dict["player_url"] = f"https://sleepercdn.com/images/team_logos/nfl/{manager_2_starters[player]['player_id']}.png"


            if len(manager_2_top_scorers) == 0:
                manager_2_top_scorers.append(player_dict)
            else:
                inserted = False
                for i in range(0, len(manager_2_top_scorers)):
                    if manager_2_starters[player]["points"] > manager_2_top_scorers[i]["score"]:
                        manager_2_top_scorers.insert(i, player_dict)
                        if len(manager_2_top_scorers) > 3:
                            manager_2_top_scorers.pop()
                        inserted = True
                        break

                # If not inserted and we have fewer than 3, append to end
                if not inserted and len(manager_2_top_scorers) < 3:
                    manager_2_top_scorers.append(player_dict)
            

        matchup_data[f"{manager_1.lower().replace(' ', '_')}_top_3_scorers"] = manager_1_top_scorers
        matchup_data[f"{manager_2.lower().replace(' ', '_')}_top_3_scorers"] = manager_2_top_scorers
        




    # ---------- Internal Data Scrubbing Methods ----------
    def _scrub_transaction_data(self, year: str, week: str):
        """Scrub transaction data for all cached roster IDs for a given week."""
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        transactions_list , _ = fetch_sleeper_data(f"league/{league_id}/transactions/{week}")
        for transaction in transactions_list:
           self._process_transaction(transaction)

    def _process_transaction(self, transaction: dict):
        # Determine transaction type
        transaction_type = transaction.get("type", "")

        if transaction_type in ["free_agent", "waiver"]:
            transaction_type = "add_or_drop"
        
        elif transaction_type == "commissioner":
            # No swap, so it must be add or drop
            if transaction.get("adds", None) is None:
                transaction_type = "add_or_drop"
            elif transaction.get("drops", None) is None:
                transaction_type = "add_or_drop"
            
            # if adds or drops is multiple players, its commish forced swap/trade
            elif len(transaction.get("adds", {})) > 1 or len(transaction.get("drops", {})) > 1:
                transaction_type = "trade"
            
            # only one add and only one drop, so add_or_drop
            else:
                transaction_type = "add_or_drop"
        

        # Dynamically collect the proper function to process this transaction type
        process_transaction_type = getattr(self, f"_process_{transaction_type}_transaction", None)

        if not self._validate_transaction(transaction, transaction_type, process_transaction_type):
            return

        # Run the transaction through the appropriate processor
        process_transaction_type(transaction)

    def _validate_transaction(self, transaction: dict, transaction_type: str, process_transaction_type) -> bool:
        
        # Skip failed transactions
        if transaction.get("status", "") == "failed":
            return False
        
        if transaction.get("status", "") != "complete":
            print("Unexpected transaction status:", transaction)
            return False
        
        

        # Validate transaction type
        if transaction_type not in {"trade", "add_or_drop"}:
            print("Unexpected transaction type:", transaction)
            return False
        
        if not process_transaction_type:
            print("No processor for transaction type:", transaction)
            return False
        
        if transaction_type == "trade":
            # Validate trade transaction specifics

            if "transaction_id" not in transaction:
                print("Invalid trade transaction (missing transaction_id):", transaction)
                return False

            if "roster_ids" not in transaction or len(transaction["roster_ids"]) < 2:
                print("Invalid trade transaction (missing roster_ids):", transaction)
                return False
            
            if "adds" not in transaction or "drops" not in transaction:
                print("Invalid trade transaction (missing adds/drops):", transaction)
                return False
            
            if not any(roster_id in self._weekly_roster_ids for roster_id in transaction["roster_ids"]):
                # No involved roster IDs are relevant to this caching session
                return False
        
        return True

    def _validate_matchup_data(self, matchup_data: dict) -> str:
        if not matchup_data:
            return "Warning, no matchup_data"
        
        opponent_manager = matchup_data.get("opponent_manager", "")
        result           = matchup_data.get("result", "")
        points_for       = matchup_data.get("points_for", 0.0)
        points_against   = matchup_data.get("points_against", 0.0)
        
        if opponent_manager == "":
            return "Warning, no opponent_data in matchup_data"
        if opponent_manager not in list(self._cache.keys()):
            return f"Warning, {opponent_manager} is an invalid manager"
        
        if points_for <= 0.0:
            return f"Warning, invalid points_for {points_for} in matchup_data"
        if points_against <= 0.0:
            return f"Warning, invalid points_against {points_against} in matchup_data"

        if result == "":
            return "Warning, no result in matchup_data"
        if result not in ["win", "loss", "tie"]:
            return f"Warning, {result} is an invalid result in matchup_data"
        
        if result == "win" and points_for < points_against:
            return f"Warning, result is win but points_against {points_against} is more than points_for {points_for} in matchup_data"
        if result == "loss" and points_for > points_against:
            return f"Warning, result is loss but points_for {points_for} is more than points_against {points_against} in matchup_data"
        if result == "tie" and points_for != points_against:
            return f"Warning, result is tie but points_for {points_for} is not the same as points_against {points_against} in matchup_data"
        
        return ""



    # ---------- Transaction Type Processors ----------
    def _process_trade_transaction(self, transaction: dict):
        for roster_id in transaction.get("roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_id, None)

            trade_partners = transaction.get("roster_ids", []).copy()
            trade_partners.remove(roster_id)
            for i in range(len(trade_partners)):
                trade_partners[i] = self._weekly_roster_ids.get(trade_partners[i], "unknown_manager")

            
            # Players/Draft Picks Acquired and Sent
            acquired = {}
            if "adds" in transaction and transaction["adds"] != None:
                for player_id in transaction.get("adds", {}):
                    if transaction["adds"][player_id] == roster_id:
                        player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
                        acquired[player_name] = self._weekly_roster_ids.get(transaction["drops"][player_id], "unknown_manager")
            

            sent = {}
            if "drops" in transaction and transaction["drops"] != None:
                for player_id in transaction.get("drops", {}):
                    if transaction["drops"][player_id] == roster_id:
                        player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
                        sent[player_name] = self._weekly_roster_ids.get(transaction["adds"][player_id], "unknown_manager")
            

            if "draft_picks" in transaction and transaction["draft_picks"] != None:
                for draft_pick in transaction.get("draft_picks", []):
                    
                    # Acquired draft pick
                    if draft_pick.get("owner_id", None) == roster_id:
                        draft_pick_name = self._draft_pick_decipher(draft_pick)
                        acquired[draft_pick_name] = self._weekly_roster_ids.get(draft_pick.get("previous_owner_id", "unknown_manager"), "unknown_manager")
                    
                    # Sent draft pick
                    if draft_pick.get("previous_owner_id", None) == roster_id:
                        draft_pick_name = self._draft_pick_decipher(draft_pick)
                        sent[draft_pick_name] = self._weekly_roster_ids.get(draft_pick.get("owner_id", "unknown_manager"), "unknown_manager")

            transaction_id = transaction.get("transaction_id", "")

            # get faab traded information
            if self._use_faab and len(transaction.get("waiver_budget", [])) != 0:
                for faab_details in transaction["waiver_budget"]:
                    faab_receiver = self._weekly_roster_ids[faab_details["receiver"]]
                    faab_sender   = self._weekly_roster_ids[faab_details["sender"]]
                    faab_amount   = faab_details["amount"]

                    faab_string = f"${faab_amount} FAAB"
                    
                    # same faab amount traded in this trade with another party
                    if faab_string in sent or faab_string in acquired:
                        print(f"WARNING: {faab_string} already in internal storage for the following trade: {transaction}")
                    
                    if faab_sender == manager:
                        sent[faab_string] = faab_receiver
                    elif faab_receiver == manager:
                        acquired[faab_string] = faab_sender
            
            # add trade details to the cache
            self._add_trade_details_to_cache(manager, trade_partners, acquired, sent, transaction_id)
        

        # Faab Trading
        if self._use_faab and transaction.get("waiver_budget", []) != []:
            for faab_transaction in transaction.get("waiver_budget", []):
                
                faab_amount = faab_transaction.get("amount", 0)
                sender = self._weekly_roster_ids.get(faab_transaction.get("sender", ""), None)
                receiver = self._weekly_roster_ids.get(faab_transaction.get("receiver", ""), None)
                transaction_id = transaction.get("transaction_id", "")

                # add faab trade details to the cache
                self._add_faab_details_to_cache("trade", sender, "FAAB", faab_amount, transaction_id, trade_partner=receiver)
                self._add_faab_details_to_cache("trade", receiver, "FAAB", -faab_amount, transaction_id, trade_partner=sender)

    def _add_trade_details_to_cache(self, manager: str, trade_partners: list, acquired: dict, sent: dict, transaction_id: str):
        """
        "trades": {
            "total": 0,
            "trade_partners": {
                    "trade_partner": num_trades
            },
            "trade_players_acquired": {
                    "player_name": {
                        "total": int
                        "trade_partners": {
                            "trade_partner": num_times_acquired_from
                        }
                }
            },
            "trade_players_sent": {
                    "player_name": 
                        "total": int
                        "trade_partners": {
                            "trade_partner": num_times_acquired_from
                        }
                }
            }
        },
        """
        player_initial_dict = {
            "total": 0,
            "trade_partners": {
                # "trade_partner": num_times_acquired_from
            }
        }

        if transaction_id in self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]["trades"]["transaction_ids"]:
            # Trade already processed for this week
            return
        
        self._add_to_transaction_id_cache(
            {
                "type": "trade",
                "manager": manager,
                "trade_partners": trade_partners,
                "acquired": acquired,
                "sent": sent,
                "transaction_id": transaction_id
            }
        )
        
        top_level_summary = self._cache[manager]["summary"]["transactions"]["trades"]
        yearly_summary = self._cache[manager]["years"][self._year]["summary"]["transactions"]["trades"]
        weekly_summary = self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]["trades"]
        summaries = [top_level_summary, yearly_summary, weekly_summary]
        
        # Add trade details in all summaries
        for summary in summaries:

            # Process total trades
            if trade_partners:
                summary["total"] += 1
            
            # Process trade partners
            for trade_partner in trade_partners:
                if trade_partner not in summary["trade_partners"]:
                    summary["trade_partners"][trade_partner] = 0
                summary["trade_partners"][trade_partner] += 1


            # Process players acquired
            acquired_summary = summary["trade_players_acquired"]
            for player in acquired:
                if player not in acquired_summary:
                    acquired_summary[player] = copy.deepcopy(player_initial_dict)
                if acquired[player] not in acquired_summary[player]["trade_partners"]:
                    acquired_summary[player]["trade_partners"][acquired[player]] = 0
                acquired_summary[player]["trade_partners"][acquired[player]] += 1
                acquired_summary[player]["total"] += 1


            # Process players sent
            sent_summary = summary["trade_players_sent"]
            for player in sent:
                if player not in sent_summary:
                    sent_summary[player] = copy.deepcopy(player_initial_dict)
                if sent[player] not in sent_summary[player]["trade_partners"]:
                    sent_summary[player]["trade_partners"][sent[player]] = 0
                sent_summary[player]["trade_partners"][sent[player]] += 1
                sent_summary[player]["total"] += 1


        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)





    # ---------- Add or Drop Transaction Processor ----------
    def _process_add_or_drop_transaction(self, transaction: dict):
        adds  = transaction.get("adds", {})
        drops = transaction.get("drops", {})

        if not adds and not drops:
            print("Waiver transaction with no adds or drops:", transaction)
            return
        
        if adds:
            for player_id in adds:
                roster_id = adds[player_id]
                
                manager = self._weekly_roster_ids.get(roster_id, None)
                player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
                
                transaction_id = transaction.get("transaction_id", "")

                # add add details to the cache
                waiver_bid = None
                if self._use_faab and transaction.get("settings", None) != None:
                    waiver_bid = transaction.get("settings", {}).get("waiver_bid", None)
                self._add_add_or_drop_details_to_cache("add", manager, player_name, transaction_id, waiver_bid)
                
                # add FAAB details to the cache
                if self._use_faab and transaction.get("settings", None) != None:
                    faab_amount = transaction.get("settings", {}).get("waiver_bid", 0)
                    transaction_type = transaction.get("type", "")
                    self._add_faab_details_to_cache(transaction_type, manager, player_name, faab_amount, transaction_id)
        
        if drops:
            for player_id in drops:
                roster_id = drops[player_id]
                
                manager = self._weekly_roster_ids.get(roster_id, None)
                player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
                
                transaction_id = transaction.get("transaction_id", "")

                # add drop details to the cache
                self._add_add_or_drop_details_to_cache("drop", manager, player_name, transaction_id)

    def _add_add_or_drop_details_to_cache(self, free_agent_type: str, manager: str, player_name: str, transaction_id: str, waiver_bid: int|None = None):
        """
        "adds": {
            "total": 0,
            "players": {
                "player_name": num_times_added
            }
        }
        """

        if free_agent_type not in ["add", "drop"]:
            return

        if transaction_id in self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"][f"{free_agent_type}s"]["transaction_ids"]:
            # Add already processed for this week
            return
        
        self._add_to_transaction_id_cache(
            {
                "type": "add_or_drop",
                "free_agent_type": free_agent_type,
                "manager": manager,
                "player_name": player_name,
                "transaction_id": transaction_id,
                "waiver_bid": waiver_bid
            }
        )
        
        top_level_summary = self._cache[manager]["summary"]["transactions"][f"{free_agent_type}s"]
        yearly_summary = self._cache[manager]["years"][self._year]["summary"]["transactions"][f"{free_agent_type}s"]
        weekly_summary = self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"][f"{free_agent_type}s"]
        summaries = [top_level_summary, yearly_summary, weekly_summary]
        
        # Add add details in all summaries
        for summary in summaries:
            if player_name not in summary["players"]:
                summary["players"][player_name] = 0
            summary["players"][player_name] += 1
            summary["total"] += 1
        
        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)

        return copy.deepcopy(weekly_summary)

    def _add_faab_details_to_cache(self, transaction_type: str, manager: str, player_name: str, faab_amount: int, transaction_id: str, trade_partner: str = None):
        """
        "faab" = {
            "total_lost_or_gained": 0,
            "players":{
                # "player_name": faab_amount
            },
            "traded_away": {
                "total": 0,
                # "trade_partner": amount_sent
            },
            "acquired_from": {
                "total": 0
                # "trade_partner": amount_received
            }
        }
        """

        if transaction_type == "trade" and trade_partner is None:
            print("Trade transaction missing trade partner for FAAB processing:", transaction_type, manager, player_name, faab_amount, transaction_id)
            return

        if transaction_id in self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]["faab"]["transaction_ids"]:
            # Waiver already processed for this week
            return
        
        
        top_level_summary = self._cache[manager]["summary"]["transactions"]["faab"]
        yearly_summary = self._cache[manager]["years"][self._year]["summary"]["transactions"]["faab"]
        weekly_summary = self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]["faab"]
        summaries = [top_level_summary, yearly_summary, weekly_summary]

        if transaction_type in ["free_agent", "waiver", "commissioner"]:
            # Add waiver details in all summaries
            for summary in summaries:
                # Process total lost or gained
                summary["total_lost_or_gained"] -= faab_amount

                # Process player-specific FAAB amounts
                if player_name not in summary["players"]:
                    summary["players"][player_name] = 0
                summary["players"][player_name] += faab_amount
        
        elif transaction_type == "trade":
            # Add trade FAAB details in all summaries
            for summary in summaries:
                if faab_amount > 0:
                    # Acquired FAAB
                    summary["total_lost_or_gained"] += faab_amount
                    summary["acquired_from"]["total"] += faab_amount
                    
                    if trade_partner not in summary["acquired_from"]["trade_partners"]:
                        summary["acquired_from"]["trade_partners"][trade_partner] = 0
                    summary["acquired_from"]["trade_partners"][trade_partner] += faab_amount
                
                # Traded FAAB away
                if faab_amount < 0:
                    summary["total_lost_or_gained"] += faab_amount
                    summary["traded_away"]["total"] -= faab_amount
                    
                    if trade_partner not in summary["traded_away"]["trade_partners"]:
                        summary["traded_away"]["trade_partners"][trade_partner] = 0
                    summary["traded_away"]["trade_partners"][trade_partner] -= faab_amount
        
        else:
            print("Unexpected transaction type for FAAB processing:", transaction_type)
            return
        
        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)





    # ---------- Set Transaction Data to Transacion ID Cache ----------
    def _add_to_transaction_id_cache(self, transaction_info: dict):

        transaction_type = transaction_info.get("type", "")
        if not transaction_type:
            raise ValueError(f"Transaction type not found in transaction_info: {transaction_info}")
        
        transaction_id = transaction_info.get("transaction_id", "")
        if not transaction_id:
            raise ValueError(f"Transaction transaction_id not found in transaction_info: {transaction_info}")
        
        manager = transaction_info.get("manager", "")
        if not manager:
            raise ValueError(f"Transaction manager not found in transaction_info: {transaction_info}")
        
        valid_add_or_drop_types = ["add", "drop", "commissioner"]
        if transaction_type == "add_or_drop":
            transaction_type = transaction_info.get("free_agent_type", "")
            if transaction_type not in valid_add_or_drop_types:
                raise ValueError(f"Transaction type {transaction_info.get('type') } not a valid 'add_or_drop' type, needs to be one of: {valid_add_or_drop_types}")

        
        # If transaction not in cache, make a new object
        if transaction_id not in self._transaction_id_cache:
            self._transaction_id_cache[transaction_id] = {
                "year":              self._year,
                "week":              self._week,
                "managers_involved": [],
                "types":             [],
                "players_involved":  []
            }
        transaction_info_to_cache = self._transaction_id_cache[transaction_id]

        

        if manager not in transaction_info_to_cache["managers_involved"]:
            transaction_info_to_cache["managers_involved"].append(manager)
            
        if transaction_type not in transaction_info_to_cache["types"]:
            transaction_info_to_cache["types"].append(transaction_type)
        

        # Add/Drop transactions
        if transaction_type in valid_add_or_drop_types:
            player_name = transaction_info.get("player_name", "")
            if not player_name:
                raise ValueError(f"player_name not found for {transaction_type} with info: {transaction_info}")
            transaction_info_to_cache["players_involved"].append(transaction_info.get("player_name", ""))
            
            if transaction_type in transaction_info_to_cache:
                raise ValueError(f"Can only add or drop one player per transaction.")
            
            transaction_info_to_cache[transaction_type] = player_name

            if transaction_type == "add" and self._use_faab and transaction_info.get("waiver_bid", None) != None:
                transaction_info_to_cache["faab_spent"] = transaction_info["waiver_bid"]
        
        # Trade transaction
        elif transaction_type == "trade":
            
            # Initialize trade details if not already in cache
            if "trade_details" not in transaction_info_to_cache:
                transaction_info_to_cache["trade_details"] = {}

            # Add all managers involved if not already in list
            for partner in transaction_info.get("trade_partners", []):
                if partner and partner not in transaction_info_to_cache["managers_involved"]:
                    transaction_info_to_cache["managers_involved"].append(partner)
            
            # Get players acquired and players sent
            players_acquired = transaction_info.get("acquired", {})
            if not players_acquired:
                print(f"WARNING: Player sent with no return, transaction_info: {transaction_info}")
            
            players_sent = transaction_info.get("sent", {})
            if not players_sent:
                print(f"WARNING: Player sent with no return, transaction_info: {transaction_info}")
            
            # Adding player from players_acquired into players_involved and into the trade
            # details if not already in cache
            for player in players_acquired:
                if not player:
                    continue
                
                if player not in transaction_info_to_cache["players_involved"]:
                    transaction_info_to_cache["players_involved"].append(player)
                
                if player not in transaction_info_to_cache["trade_details"]:
                    transaction_info_to_cache["trade_details"][player] = {
                        "old_manager": players_acquired[player],
                        "new_manager": manager
                    }
                
            
            # Adding player from players_sent into players_involved and into the trade
            # details if not already in cache
            for player in players_sent:
                if not player:
                    continue
                
                if player not in transaction_info_to_cache["players_involved"]:
                    transaction_info_to_cache["players_involved"].append(player)
                
                if player not in transaction_info_to_cache["trade_details"]:
                    transaction_info_to_cache["trade_details"][player] = {
                        "old_manager": manager,
                        "new_manager": players_sent[player]
                    }
        
        # FAAB data being handled in trades and add/drop for transactions
        elif transaction_type == "faab":
            return
        
        # Transaction type unknown
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")


        



    # ---------- Internal Matchup Data Scrubbing ----------
    def _scrub_matchup_data(self, year: str, week: str):
        """Scrub matchup data for all cached roster IDs for a given week."""
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        matchups_evaluated = []
        manager_matchup_data , _ = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
        for manager_1_data in manager_matchup_data:
            if self._get_season_state() == "playoffs" and manager_1_data.get("roster_id", None) not in self._playoff_roster_ids.get("round_roster_ids", []):
                # Manager not in playoffs; skip
                continue

            matchup_id = manager_1_data.get("matchup_id", None)
            if matchup_id in matchups_evaluated:
                continue
            matchups_evaluated.append(matchup_id)

            # Find opponent manager data
            for manager_2_data in manager_matchup_data:
                if manager_2_data.get("roster_id", None) == manager_1_data.get("roster_id", None):
                    continue
                if manager_2_data.get("matchup_id", None) == matchup_id:
                    break
            
            # Extract points data
            manager_1_points = manager_1_data.get("points", 0.0)
            manager_2_points = manager_2_data.get("points", 0.0)

            # Construct manager matchup dicts
            manager_1 = {
                "manager": self._weekly_roster_ids.get(manager_1_data.get("roster_id", None), None),
                "opponent_manager": self._weekly_roster_ids.get(manager_2_data.get("roster_id", None), None),
                "points_for": manager_1_points,
                "points_against": manager_2_points
            }
            manager_2 = {
                "manager": self._weekly_roster_ids.get(manager_2_data.get("roster_id", None), None),
                "opponent_manager": self._weekly_roster_ids.get(manager_1_data.get("roster_id", None), None),
                "points_for": manager_2_data.get("points", 0.0),
                "points_against": manager_1_points
            }

            # Determine results
            if manager_1["points_for"] > manager_2["points_for"]:
                manager_1["result"] = "win"
                manager_2["result"] = "loss"
            elif manager_1["points_for"] < manager_2["points_for"]:
                manager_1["result"] = "loss"
                manager_2["result"] = "win"
            else:
                manager_1["result"] = "tie"
                manager_2["result"] = "tie"
            

            self._add_matchup_details_to_cache(manager_1)
            self._add_matchup_details_to_cache(manager_2)

    def _add_matchup_details_to_cache(self, matchup_data: dict):
        from decimal import Decimal
        
        # Extract matchup data
        manager = matchup_data.get("manager", None)
        opponent_manager = matchup_data.get("opponent_manager", None)
        points_for = matchup_data.get("points_for", 0.0)
        points_against = matchup_data.get("points_against", 0.0)
        result = matchup_data.get("result", None)

        if not manager or not opponent_manager or result is None:
            raise ValueError("Invalid matchup data for caching:", matchup_data)
        
        # Update weekly summary
        weekly_summary = self._cache[manager]["years"][self._year]["weeks"][self._week]["matchup_data"]
        weekly_summary["opponent_manager"] = opponent_manager
        weekly_summary["points_for"] = points_for
        weekly_summary["points_against"] = points_against
        weekly_summary["result"] = result

        # Prepare yearly and top-level summaries
        yearly_overall_summary         = self._cache[manager]["years"][self._year]["summary"]["matchup_data"]["overall"]
        yearly_season_state_summary    = self._cache[manager]["years"][self._year]["summary"]["matchup_data"][self._get_season_state()]

        top_level_overall_summary      = self._cache[manager]["summary"]["matchup_data"]["overall"]
        top_level_season_state_summary = self._cache[manager]["summary"]["matchup_data"][self._get_season_state()]
        
        summaries = [yearly_overall_summary, yearly_season_state_summary,
                     top_level_overall_summary, top_level_season_state_summary]
        
        # Determine result key
        if result == "win":
            result_key = "wins"
        elif result == "loss":
            result_key = "losses"
        elif result == "tie":
            result_key = "ties"
        else:
            raise ValueError("Invalid matchup result for caching:", result)
        
        
        # Add matchup details in all summaries
        for summary in summaries:
            
            # Points for
            summary["points_for"]["total"] += points_for
            if opponent_manager not in summary["points_for"]["opponents"]:
                summary["points_for"]["opponents"][opponent_manager] = 0.0
            summary["points_for"]["opponents"][opponent_manager] += points_for

            # Points against
            summary["points_against"]["total"] += points_against
            if opponent_manager not in summary["points_against"]["opponents"]:
                summary["points_against"]["opponents"][opponent_manager] = 0.0
            summary["points_against"]["opponents"][opponent_manager] += points_against

            # Total matchups
            summary["total_matchups"]["total"] += 1
            if opponent_manager not in summary["total_matchups"]["opponents"]:
                summary["total_matchups"]["opponents"][opponent_manager] = 0
            summary["total_matchups"]["opponents"][opponent_manager] += 1

            # Wins/Losses/Ties
            summary[result_key]["total"] += 1
            if opponent_manager not in summary[result_key]["opponents"]:
                summary[result_key]["opponents"][opponent_manager] = 0
            summary[result_key]["opponents"][opponent_manager] += 1

            # Quantize points to 2 decimal places
            summary["points_for"]["total"] = float(Decimal(summary["points_for"]["total"]).quantize(Decimal('0.01')))
            summary["points_for"]["opponents"][opponent_manager] = float(Decimal(summary["points_for"]["opponents"][opponent_manager]).quantize(Decimal('0.01')))
            
            summary["points_against"]["total"] = float(Decimal(summary["points_against"]["total"]).quantize(Decimal('0.01')))
            summary["points_against"]["opponents"][opponent_manager] = float(Decimal(summary["points_against"]["opponents"][opponent_manager]).quantize(Decimal('0.01')))
            
    



    # ---------- Internal Playoff Data Scrubbing ----------
    def _scrub_playoff_data(self, year: str, week: str):
        """Scrub playoff data for all cached roster IDs for a given week."""

        for roster_ids in self._playoff_roster_ids.get("round_roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_ids, None)
            if not manager:
                continue

            manager_overall_data = self._cache[manager]["summary"]["overall_data"]

            # Mark week as playoff week in the weekly summary
            if self._year not in manager_overall_data["playoff_appearances"]:
                manager_overall_data["playoff_appearances"].append(self._year)
        
        first_place_roster_id = self._playoff_roster_ids.get("first_place_id", None)
        second_place_roster_id = self._playoff_roster_ids.get("second_place_id", None)
        third_place_roster_id = self._playoff_roster_ids.get("third_place_id", None)

        if first_place_roster_id is None or second_place_roster_id is None or third_place_roster_id is None:
            print("Incomplete playoff roster IDs for caching playoff data:", self._playoff_roster_ids)
            return

        first_place_manager = self._weekly_roster_ids.get(first_place_roster_id, None)
        second_place_manager = self._weekly_roster_ids.get(second_place_roster_id, None)
        third_place_manager = self._weekly_roster_ids.get(third_place_roster_id, None)

        if year not in self._cache[first_place_manager]["summary"]["overall_data"]["placement"]:
            self._cache[first_place_manager]["summary"]["overall_data"]["placement"][year] = 1
        if year not in self._cache[second_place_manager]["summary"]["overall_data"]["placement"]:
            self._cache[second_place_manager]["summary"]["overall_data"]["placement"][year] = 2
        if year not in self._cache[third_place_manager]["summary"]["overall_data"]["placement"]:
            self._cache[third_place_manager]["summary"]["overall_data"]["placement"][year] = 3

    
    


    # ---------- Internal Template Initialization Methods ----------
    def _initialize_faab_template(self, manager: str):
        if "faab" not in self._cache[manager]["summary"]["transactions"]:
            self._cache[manager]["summary"]["transactions"]["faab"] = copy.deepcopy(self._faab_template)
        
        if "faab" not in self._cache[manager]["years"][self._year]["summary"]["transactions"]:
            self._cache[manager]["years"][self._year]["summary"]["transactions"]["faab"] = copy.deepcopy(self._faab_template)
            
        if "faab" not in self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]:
            faab_template_with_transaction_ids = copy.deepcopy(self._faab_template)
            faab_template_with_transaction_ids["transaction_ids"] = []
            self._cache[manager]["years"][self._year]["weeks"][self._week]["transactions"]["faab"] = copy.deepcopy(faab_template_with_transaction_ids)

    def _initialize_summary_templates(self):
        
        # Common matchup data template
        matchup_data_int = {
            "total": 0,
            "opponents": {
                # "opponent_manager": value
            }
        }
        matchup_data_float = {
            "total": 0.0,
            "opponents": {
                # "opponent_manager": value
            }
        }
        full_matchup_data = {
            "points_for":     copy.deepcopy(matchup_data_float),
            "points_against": copy.deepcopy(matchup_data_float),
            "total_matchups": copy.deepcopy(matchup_data_int),
            "wins":           copy.deepcopy(matchup_data_int),
            "losses":         copy.deepcopy(matchup_data_int),
            "ties":           copy.deepcopy(matchup_data_int)
        }



        self._faab_template = {
            "total_lost_or_gained": 0,
            "players":{
                # "player_name": faab_amount
            },
            "traded_away": {
                "total": 0,
                "trade_partners": {
                    # "trade_partner": amount_received
                }
            },
            "acquired_from": {
                "total": 0,
                "trade_partners": {
                    # "trade_partner": amount_received
                }
            }
        }

        # Transaction data template
        transaction_data = {
            "trades": {
                "total": 0,
                "trade_partners": {
                    # "trade_partner": num_trades
                },
                "trade_players_acquired": {
                    # "player_name": {
                    #     "total": int
                    #     "trade_partners": {
                    #         "trade_partner": num_times_acquired_from
                    #     }
                    #}
                },
                "trade_players_sent": {
                    # "player_name": 
                    #     "total": int
                    #     "trade_partners": {
                    #         "trade_partner": num_times_acquired_from
                    #     }
                    #}
                }
            },
            "adds": {
                "total": 0,
                "players": {
                    # "player_name": num_times_added
                }
            },
            "drops": {
                "total": 0,
                "players": {
                    # "player_name": num_times_dropped
                }
            }
            # "faab" = {
            #     "total_lost_or_gained": 0,
            #     "players":{
            #         # "player_name": faab_amount
            #     },
            #     "traded_away": {
            #         "total": 0,
            #         "trade_partners": {
            #             "trade_partner": amount_received
            #         }
            #     },
            #     "acquired_from": {
            #         "total": 0
            #         "trade_partners": {
            #             "trade_partner": amount_received
            #         }
            #     }
            # }
        }

        if self._use_faab:
            transaction_data["faab"] = copy.deepcopy(self._faab_template)
        
        
        self._yearly_summary_template = {
            "matchup_data": {
                "overall":        copy.deepcopy(full_matchup_data),
                "regular_season": copy.deepcopy(full_matchup_data),
                "playoffs":       copy.deepcopy(full_matchup_data)
            },
            "transactions": copy.deepcopy(transaction_data)
        }

        # Blank summary template for initializing new weekly data
        self._weekly_summary_template = {
            "matchup_data": {
                "opponent_manager": None,
                "result": None,  # "win", "loss", "tie"
                "points_for": 0.0,
                "points_against": 0.0
            },
            "transactions": copy.deepcopy(transaction_data)
        }
        self._weekly_summary_template_not_in_playoffs = {
            "matchup_data": {}, # No matchup data when not in playoffs
            "transactions": copy.deepcopy(transaction_data)
        }


        self._weekly_summary_template["transactions"]["trades"]["transaction_ids"] = []
        self._weekly_summary_template["transactions"]["adds"]["transaction_ids"] = []
        self._weekly_summary_template["transactions"]["drops"]["transaction_ids"] = []
        self._weekly_summary_template_not_in_playoffs["transactions"]["trades"]["transaction_ids"] = []
        self._weekly_summary_template_not_in_playoffs["transactions"]["adds"]["transaction_ids"] = []
        self._weekly_summary_template_not_in_playoffs["transactions"]["drops"]["transaction_ids"] = []


        if self._use_faab:
            self._weekly_summary_template["transactions"]["faab"]["transaction_ids"] = []

        self._top_level_summary_template = copy.deepcopy(self._yearly_summary_template)
        self._top_level_summary_template["overall_data"] = {
            "placement": {
                # "year": placement
            },
            "playoff_appearances": [ 
                # list of years with playoff appearances    
            ],
            "avatar_urls": {
                "full_size": "",
                "thumbnail": ""
            }
        }




man = ManagerMetadataManager()
d = man._get_manager_score_awards_from_cache("Tommy")
import json
pretty_json_string = json.dumps(d, indent=4)
print(pretty_json_string)
print("")