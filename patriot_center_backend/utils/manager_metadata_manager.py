import copy

from patriot_center_backend.constants import MANAGER_METADATA_CACHE_FILE, LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.cache_utils import load_cache, save_cache
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.utils.player_ids_loader import load_player_ids



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
        self._player_ids = load_player_ids()
        
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
        """Returns list of all managers with basic info."""
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
        """Returns complete summary data for a manager."""
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
        """Returns detailed yearly data for a manager."""
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
                "partner": weekly_transactions["trades"]["transaction_ids"],
            }
            transaction_data["trades"]["by_week"].append(copy.deepcopy(trade_item))

            # Adds
            add_item = {
                "week": week,
                "total": weekly_transactions["adds"]["total"]
            }
            transaction_data["adds"]["by_week"].append(copy.deepcopy(add_item))

            # Drops
            drop_item = {
                "week": week,
                "total": weekly_transactions["drops"]["total"]
            }
            transaction_data["drops"]["by_week"].append(copy.deepcopy(drop_item))


        







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
        trades["most_aquired_players"] = most_acquired_players

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

    def _get_head_to_head_details_from_cache(self, manager_name: str, year: str = None) -> dict:
        """Helper to extract head-to-head details from cache for a manager."""
        head_to_head_data = {}
        
        cached_head_to_head_data = copy.deepcopy(self._cache[manager_name]["summary"]["matchup_data"]["overall"])
        if year:
            cached_head_to_head_data = copy.deepcopy(self._cache[manager_name]["years"][year]["summary"]["matchup_data"]["overall"])
        
        for opponent in cached_head_to_head_data.get("points_for", {}).get("opponents", {}):

            head_to_head_data[opponent] = {
                "wins":           cached_head_to_head_data["wins"]["opponents"].get(opponent, 0),
                "losses":         cached_head_to_head_data["losses"]["opponents"].get(opponent, 0),
                "ties":           cached_head_to_head_data["ties"]["opponents"].get(opponent, 0),
                "points_for":     cached_head_to_head_data["points_for"]["opponents"].get(opponent, 0.0),
                "points_against": cached_head_to_head_data["points_against"]["opponents"].get(opponent, 0.0)
            }
        
        return copy.deepcopy(head_to_head_data)







    # ---------- Internal Save/Load Methods ----------
    def _load(self):
        """Load the entire manager metadata cache."""
        self._cache = load_cache(MANAGER_METADATA_CACHE_FILE, initialize_with_last_updated_info=False)


    def save(self):
        """Save the entire manager metadata cache."""
        save_cache(MANAGER_METADATA_CACHE_FILE, self._cache)





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

        if transaction_type in ["free_agent", "waiver", "commissioner"]:
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

            
    def _draft_pick_decipher(self, draft_pick_dict: dict) -> str:
        """Convert draft pick dictionary to a human-readable string."""
        season = draft_pick_dict.get("season", "unknown_year")
        round_num = draft_pick_dict.get("round", "unknown_round")

        origin_team = draft_pick_dict.get("roster_id", "unknown_team")
        origin_manager = self._weekly_roster_ids.get(origin_team, "unknown_manager")

        return f"{origin_manager}'s {season} Round {round_num} Draft Pick"
    

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
                self._add_add_or_drop_details_to_cache("add", manager, player_name, transaction_id)
                
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
    

    def _add_add_or_drop_details_to_cache(self, free_agent_type: str, manager: str, player_name: str, transaction_id: str):
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

test_manager_metadata_manager = ManagerMetadataManager().get_manager_yearly_data("Tommy", "2025")
print(test_manager_metadata_manager)