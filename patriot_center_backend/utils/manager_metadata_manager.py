import copy
from time import sleep

from patriot_center_backend.constants import MANAGER_METADATA_CACHE_FILE, LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.cache_utils import load_cache, save_cache
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.utils.player_ids_loader import load_player_ids



class ManagerMetadataManager:
    def __init__(self):
        
        # In-memory cache structure (see _initialize_summary_templates for details on sub-structures)
        self._cache = {
            # "manager":{
            #     "summary": { ... },
            #     "years": {
            #         "year": {
            #             "summary": { ... },
            #             "roster_id": int,
            #             "weeks": {
            #                 "week": {
            #                     "matchup_data":
            #                     {
            #                         "opponent_manager": str,
            #                         "result": str,  # "win", "loss", "tie"
            #                         "points_for": float,
            #                         "points_against": float
            #                     },
            #                     "transactions": { ... }
            #                 }
            #             }
            #         }
            #     }
            # }
        }

        # Predefined templates for initializing new data
        self._initialize_summary_templates()

        # Weekly roster ID to manager mapping for current caching session, cleared on week cache completion
        self._weekly_roster_ids = {
            # roster_id: manager
        }
        self._year = None
        self._week = None
        
        self._load()





    def set_roster_id(self, manager: str, year: str, week: str, roster_id: int):
        """Set the roster ID for a given manager and year."""

        self._set_defaults_if_missing(manager, year, week)
        self._cache[manager]["years"][year]["roster_id"] = roster_id
        self._weekly_roster_ids[roster_id] = manager
        self._year = year
        self._week = week

        if "user_id" not in self._cache[manager]["summary"]:
            username = NAME_TO_MANAGER_USERNAME.get(manager, "")
            if username:
                user_payload, status_code = fetch_sleeper_data(f"user/{username}")
                if status_code == 200 and "user_id" in user_payload:
                    self._cache[manager]["summary"]["user_id"] = user_payload["user_id"]
            
                else:
                    raise ValueError(f"Failed to fetch user data for manager {manager} with username {username}.")
            else:
                raise ValueError(f"No username mapping found for manager {manager}.")
            
            
        self._save()


        self._save()



    
    def cache_week_data(self, year: str, week: str):
        """Cache week-specific data for a given week and year."""
        
        # Ensure preconditions are met
        self._caching_preconditions_met()

        self._player_ids = load_player_ids()

        #
        self._scrub_transaction_data(year, week)

        self._save()

        self._clear_weekly_metadata()

    








    def _load(self):
        """Load the entire manager metadata cache."""
        self._cache = load_cache(MANAGER_METADATA_CACHE_FILE, initialize_with_last_updated_info=False)

    def _save(self):
        """Save the entire manager metadata cache."""
        save_cache(MANAGER_METADATA_CACHE_FILE, self._cache)
    
    def _clear_weekly_metadata(self):
        """Clear the entire manager metadata."""
        self._weekly_roster_ids = {}
        self._year = None
        self._week = None
    
    def _set_defaults_if_missing(self, manager: str, year: str, week: str):
        """Helper to initialize nested structures if missing."""
        if manager not in self._cache:
            self._cache[manager] = {"summary": copy.deepcopy(self._top_level_summary_template), "years": {}}
        
        if year not in self._cache[manager]["years"]:
            self._cache[manager]["years"][year] = {
                "summary": copy.deepcopy(self._yearly_summary_template),
                "roster_id": None,
                "weeks": {}
            }
        
        if week not in self._cache[manager]["years"][year]["weeks"]:
            self._cache[manager]["years"][year]["weeks"][week] = copy.deepcopy(self._weekly_summary_template)

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

        # Dynamically collect the proper function to process this transaction type
        process_transaction_type = getattr(self, f"_process_{transaction_type}_transaction", None)

        if not self._validate_transaction(transaction, transaction_type, process_transaction_type):
            return

        # Run the transaction through the appropriate processor
        process_transaction_type(transaction)








    def _process_trade_transaction(self, transaction: dict):
        for roster_id in transaction.get("roster_ids", []):
            manager = self._weekly_roster_ids.get(roster_id, None)

            trade_partners = transaction.get("roster_ids", []).copy()
            trade_partners.remove(roster_id)
            for i in range(len(trade_partners)):
                trade_partners[i] = self._weekly_roster_ids.get(trade_partners[i], "unknown_manager")
            


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

            print(f"{manager} traded with {trade_partners}: acquired {acquired}, sent {sent}")

            # add trade details to the cache
            self._add_trade_details_to_cache(manager, trade_partners, acquired, sent, transaction_id)
    

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


            # Process trade partners
            for trade_partner in trade_partners:
                if trade_partner not in [summary["trade_partners"].keys()]:
                    summary["trade_partners"][trade_partner] = 0
                summary["trade_partners"][trade_partner] += 1
                summary["total"] += 1


            # Process players acquired
            acquired_summary = summary["trade_players_acquired"]
            for player in acquired:
                if player not in acquired_summary:
                    acquired_summary[player] = copy.deepcopy(player_initial_dict)
                    acquired_summary[player]["trade_partners"][acquired[player]] = 0
                if acquired[player] not in acquired_summary[player]["trade_partners"]:
                    acquired_summary[player]["trade_partners"][acquired[player]] = 0
                acquired_summary[player]["trade_partners"][acquired[player]] += 1
                acquired_summary[player]["total"] += 1


            # Process players sent
            sent_summary = summary["trade_players_sent"]
            for player in sent:
                if player not in sent_summary:
                    sent_summary[player] = copy.deepcopy(player_initial_dict)
                    sent_summary[player]["trade_partners"][sent[player]] = 0
                if sent[player] not in sent_summary[player]["trade_partners"]:
                    sent_summary[player]["trade_partners"][sent[player]] = 0
                sent_summary[player]["trade_partners"][sent[player]] += 1
                sent_summary[player]["total"] += 1
        
        # Finally, add transaction ID to weekly summary to avoid double counting
        weekly_summary["transaction_ids"].append(transaction_id)
    






    def _process_free_agent_transaction(self, transaction: dict):
        adds  = transaction.get("adds", {})
        drops = transaction.get("drops", {})

        if not adds:
            return
        for player_id in adds:
            roster_id = adds[player_id]
            
            manager = self._weekly_roster_ids.get(roster_id, None)
            player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
            
            transaction_id = transaction.get("transaction_id", "")

            # add add details to the cache
            self._add_free_agent_details_to_cache("add", manager, player_name, transaction_id)
        
        if not drops:
            return
        for player_id in drops:
            roster_id = drops[player_id]
            
            manager = self._weekly_roster_ids.get(roster_id, None)
            player_name = self._player_ids.get(player_id, {}).get("full_name", "unknown_player")
            
            transaction_id = transaction.get("transaction_id", "")

            # add drop details to the cache
            self._add_free_agent_details_to_cache("drop", manager, player_name, transaction_id)
    

    def _add_free_agent_details_to_cache(self, free_agent_type: str, manager: str, player_name: str, transaction_id: str):
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







    def _process_waiver_transaction(self, transaction: dict):
        
        # Waiver transactions are treated the same as free agent transactions
        self._process_free_agent_transaction(transaction)

        # Later, faab logic will be added here

    def _process_commissioner_transaction(self, transaction: dict):
        
        # Commissioner transactions are treated the same as free agent transactions
        self._process_free_agent_transaction(transaction)





    def _validate_transaction(self, transaction: dict, transaction_type: str, process_transaction_type) -> bool:
        
        # Skip failed transactions
        if transaction.get("status", "") == "failed":
            return False
        
        if transaction.get("status", "") != "complete":
            print("Unexpected transaction status:", transaction)
            return False
        
        

        # Validate transaction type
        if transaction_type not in {"trade", "free_agent", "waiver", "commissioner"}:
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
    
    def _initialize_summary_templates(self):
        
        # Common matchup data template
        matchup_data = {
            "total": 0.0,
            "opponents": {
                # "opponent_manager": value
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
        }
        
        
        self._yearly_summary_template = {
            "matchup_data": {
                "overall": {
                    "points_for":     copy.deepcopy(matchup_data),
                    "points_against": copy.deepcopy(matchup_data),
                    "wins":           copy.deepcopy(matchup_data),
                    "losses":         copy.deepcopy(matchup_data),
                    "ties":           copy.deepcopy(matchup_data)
                },
                "regular_season": {
                    "points_for":     copy.deepcopy(matchup_data),
                    "points_against": copy.deepcopy(matchup_data),
                    "wins":           copy.deepcopy(matchup_data),
                    "losses":         copy.deepcopy(matchup_data),
                    "ties":           copy.deepcopy(matchup_data)
                },
                "playoffs": {
                    "points_for":     copy.deepcopy(matchup_data),
                    "points_against": copy.deepcopy(matchup_data),
                    "wins":           copy.deepcopy(matchup_data),
                    "losses":         copy.deepcopy(matchup_data),
                    "ties":           copy.deepcopy(matchup_data)
                }
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
        self._weekly_summary_template["transactions"]["trades"]["transaction_ids"] = []
        self._weekly_summary_template["transactions"]["adds"]["transaction_ids"] = []
        self._weekly_summary_template["transactions"]["drops"]["transaction_ids"] = []

        self._top_level_summary_template = copy.deepcopy(self._yearly_summary_template)
        self._top_level_summary_template["overall_data"] = {
            "placement": {
                # "year": placement
            },
            "playoff_appearances": [ 
                # list of years with playoff appearances    
            ]
        }