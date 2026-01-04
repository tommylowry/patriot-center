"""
Data export layer for manager metadata.

Provides public API for retrieving manager data in various formats.
All methods delegate to cache_queries for data extraction.
"""
from typing import Dict, Any
from copy import deepcopy

from patriot_center_backend.constants import LEAGUE_IDS

from patriot_center_backend.managers.utilities import get_current_manager_image_url
from patriot_center_backend.managers.cache_queries import (
    get_matchup_details_from_cache,
    get_transaction_details_from_cache,
    get_overall_data_details_from_cache,
    get_ranking_details_from_cache,
    get_head_to_head_details_from_cache,
    get_head_to_head_overall_from_cache,
    get_trade_history_between_two_managers,
    get_manager_awards_from_cache,
    get_manager_score_awards_from_cache
)
from patriot_center_backend.managers.formatters import get_image_url, get_trade_card


class DataExporter:
    """
    Exports manager metadata in various formats for API consumption.

    Provides public read-only API for accessing manager data including:
    - Manager lists with rankings
    - Comprehensive manager summaries
    - Head-to-head matchup histories
    - Transaction histories
    - Manager awards and achievements

    All methods delegate to cache_queries for data extraction.
    """

    def __init__(self, cache: dict, transaction_ids_cache: dict, players_cache: dict,
                 valid_options_cache: dict, starters_cache: dict, player_ids: dict):
        """
        Initialize data exporter with required caches.

        Args:
            cache: Main manager metadata cache (read-only)
            transaction_ids_cache: Transaction ID cache (read-only)
            players_cache: Player cache (read-only)
            valid_options_cache: Valid options cache by year (read-only)
            starters_cache: Starting lineup cache (read-only)
            player_ids: Player ID to metadata mapping (read-only)
        """
        self._cache = cache
        self._transaction_ids_cache = transaction_ids_cache
        self._players_cache = players_cache
        self._player_ids = player_ids
        self._valid_options_cache = valid_options_cache
        self._starters_cache = starters_cache
        self._image_urls_cache: Dict[str, str] = {}  # Mutable cache for image URLs
    
    def get_managers_list(self, active_only: bool) -> Dict[str, Any]:
        """
        Get list of all managers with key stats and rankings.

        Returns formatted manager list including:
        - Basic info (name, image, years active)
        - Record (wins/losses/ties, win percentage)
        - Transaction totals (trades, adds, drops)
        - Placements (championships, playoff appearances, best finish)
        - Rankings across categories
        - Weight for sorting (prioritizes championships, then playoffs, then points)

        Args:
            active_only: If True, only return currently active managers

        Returns:
            Dictionary with "managers" list, sorted by weight (best managers first)
        """
        current_year = str(max(LEAGUE_IDS.keys()))
        
        managers = self._valid_options_cache[current_year]["managers"]
        if not active_only:
            managers = list(self._cache.keys())
        
        managers_list = []
        
        for manager in managers:
            wins   = self._cache[manager]["summary"]["matchup_data"]["overall"]["wins"]["total"]
            losses = self._cache[manager]["summary"]["matchup_data"]["overall"]["losses"]["total"]
            ties   = self._cache[manager]["summary"]["matchup_data"]["overall"]["ties"]["total"]
            
            ranking_details = get_ranking_details_from_cache(self._cache, manager, self._valid_options_cache,
                                                             manager_summary_usage=True, active_only=active_only)

            manager_item = {
                "name":           manager,
                "image_url":      get_current_manager_image_url(manager, self._cache, self._image_urls_cache),
                "years_active":   list(self._cache[manager].get("years", {}).keys()),
                "total_trades":   self._cache[manager]["summary"]["transactions"]["trades"]["total"],
                "wins":           wins,
                "losses":         losses,
                "ties":           ties,
                "win_percentage": ranking_details['values']['win_percentage']
            }

            placements = {
                "first_place":  0,
                "second_place": 0,
                "third_place":  0
            }
            playoff_appearances = ranking_details['values']['playoffs']
            best_finish         = 4
            for y in self._cache[manager]['summary']['overall_data']['placement']:
                if self._cache[manager]['summary']['overall_data']['placement'][y] == 1:
                    placements['first_place'] += 1
                if self._cache[manager]['summary']['overall_data']['placement'][y] == 2:
                    placements['second_place'] += 1
                if self._cache[manager]['summary']['overall_data']['placement'][y] == 3:
                    placements['third_place'] += 1
                if self._cache[manager]['summary']['overall_data']['placement'][y] < best_finish:
                    best_finish = self._cache[manager]['summary']['overall_data']['placement'][y]


            if best_finish == 4:
                if playoff_appearances > 0:
                    best_finish = "Playoffs"
                else:
                    best_finish = "Never Made Playoffs"
            
            # determine how high or low they should go in the list
            weight = 0
            weight += placements['first_place'] * 10000
            weight += placements['second_place'] * 1000
            weight += placements['third_place'] * 100
            weight += playoff_appearances * 10
            weight += ranking_details['values']['average_points_for']
            manager_item['weight'] = weight
            
            manager_item["placements"]          = deepcopy(placements)
            manager_item["playoff_appearances"] = ranking_details['values']['playoffs']
            manager_item["best_finish"]         = best_finish

            manager_item["average_points_for"] = ranking_details['values']['average_points_for']

            manager_item["total_adds"]  = self._cache[manager]['summary']['transactions']['adds']['total']
            manager_item["total_drops"] = self._cache[manager]['summary']['transactions']['drops']['total']

            manager_item["is_active"] = ranking_details['ranks']['is_active_manager']

            rankings = {
                "win_percentage":     ranking_details['ranks']['win_percentage'],
                "average_points_for": ranking_details['ranks']['average_points_for'],
                "trades":             ranking_details['ranks']['trades'],
                "playoffs":           ranking_details['ranks']['playoffs'],
                "worst":              ranking_details['ranks']['worst']
            }

            manager_item["rankings"] = deepcopy(rankings)

            managers_list.append(manager_item)
        
        return { "managers": managers_list }
    
    def get_manager_summary(self, manager: str, year: str = None) -> Dict:
        """
        Get comprehensive manager summary with all statistics and rankings.

        Includes:
        - Basic info (name, image, years active)
        - Matchup data (record, averages by season state)
        - Transaction summary (trades, adds, drops, FAAB)
        - Overall data (placements, playoff appearances)
        - Rankings across all categories
        - Head-to-head records against all opponents

        Args:
            manager: Manager name
            year: Season year (optional - defaults to all-time stats)

        Returns:
            Comprehensive manager summary dictionary

        Raises:
            ValueError: If manager or year not found in cache
        """
        if manager not in self._cache:
            raise ValueError(f"Manager {manager} not found in cache.")
        
        if year:
            if year not in self._cache[manager]["years"]:
                raise ValueError(f"Year {year} not found for manager {manager} in cache.")
        
        return_dict = {}
        return_dict["manager_name"] = manager
        return_dict["image_url"]    = get_current_manager_image_url(manager, self._cache, self._image_urls_cache)
        return_dict["years_active"] = list(self._cache[manager].get("years", {}).keys())

        return_dict["matchup_data"] = get_matchup_details_from_cache(self._cache, manager, year=year)
        return_dict["transactions"] = get_transaction_details_from_cache(self._cache, year, manager,
                                                                         self._image_urls_cache, self._players_cache,
                                                                         self._player_ids)
        return_dict["overall_data"] = get_overall_data_details_from_cache(self._cache, year, manager)
        return_dict["rankings"]     = get_ranking_details_from_cache(self._cache, manager, self._valid_options_cache, year=year)
        return_dict["head_to_head"] = get_head_to_head_details_from_cache(self._cache, manager, self._image_urls_cache, 
                                                                          self._players_cache, self._player_ids, year=year)

        return deepcopy(return_dict)
    
    
    def get_head_to_head(self, manager1: str, manager2: str, year: str = None) -> Dict:
        """
        Get complete head-to-head analysis between two managers.

        Includes:
        - Overall statistics (record, margins, last wins, biggest blowouts)
        - Complete matchup history (all games with scores and performers)
        - Trade history between the two managers

        Args:
            manager1: First manager name
            manager2: Second manager name
            year: Season year (optional - defaults to all-time)

        Returns:
            Dictionary with overall stats, matchup_history, and trades_between

        Raises:
            ValueError: If manager or year not found in cache
        """
        return_dict = {}
        
        for manager in [manager1, manager2]:
        
            if manager not in self._cache:
                raise ValueError(f"Manager {manager} not found in cache.")
            if year:
                if year not in self._cache[manager]["years"]:
                    raise ValueError(f"Year {year} not found for manager {manager} in cache.")

            manager = {
                "name":      manager,
                "image_url": get_current_manager_image_url(manager, self._cache, self._image_urls_cache)
            }

            if "manager_1" not in return_dict:
                return_dict["manager_1"] = deepcopy(manager)
            else:
                return_dict["manager_2"] = deepcopy(manager)


        return_dict["overall"] = get_head_to_head_overall_from_cache(self._cache, manager1, manager2,
                                                                     self._players_cache, self._player_ids,
                                                                     self._image_urls_cache, self._starters_cache,
                                                                     year=year)

        return_dict["matchup_history"]= get_head_to_head_overall_from_cache(self._cache, manager1, manager2,
                                                                     self._players_cache, self._player_ids,
                                                                     self._image_urls_cache, self._starters_cache,
                                                                     year=year, list_all_matchups=True)

        trades_between = get_trade_history_between_two_managers(self._cache, manager1, manager2,
                                                                self._transaction_ids_cache,
                                                                self._image_urls_cache, self._players_cache,
                                                                self._player_ids, year=year)

        return_dict["trades_between"] = {
            "total": len(trades_between),
            "trade_history": trades_between
        }

        return deepcopy(return_dict)
    
    def get_manager_transactions(self, manager_name: str, year: str = None) -> dict:
        """
        Get complete transaction history for a manager.

        Returns all transactions (trades, adds, drops, add_and_drops) with details.
        Transactions include:
        - Trades: All players/assets exchanged
        - Adds: Players added with FAAB spent
        - Drops: Players dropped
        - Add_and_drops: Combined add/drop transactions

        Args:
            manager_name: Manager name
            year: Season year (optional - defaults to all-time)

        Returns:
            Dictionary with name, total_count, and transactions list (newest first)

        Raises:
            ValueError: If manager or year not found in cache
        """
        if manager_name not in self._cache:
            raise ValueError(f"Manager {manager_name} not found in cache.")
        if year:
            if year not in self._cache[manager_name]["years"]:
                raise ValueError(f"Year {year} not found for manager {manager_name} in cache.")
        
        
        transaction_history = {
            "name": get_image_url(manager_name, self._players_cache, self._player_ids,
                                  self._image_urls_cache, self._cache, dictionary=True),
            "total_count":  0,
            "transactions": []
        }

        # Gather transactions based on filters
        filtered_transactions = []
        years_to_check = [year] if year else list(self._cache[manager_name]["years"].keys())
        
        for yr in years_to_check:
            yearly_data = self._cache[manager_name]["years"][yr]
            for week in yearly_data.get("weeks", {}):
                weekly_transactions = deepcopy(yearly_data["weeks"][week]["transactions"])
                
                # Trades
                transaction_ids = deepcopy(weekly_transactions.get("trades", {}).get("transaction_ids", []))
                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    trade_details = get_trade_card(transaction_id, self._transaction_ids_cache,
                                                    self._image_urls_cache, self._players_cache,
                                                    self._player_ids, self._cache)

                    trade_details["type"] = "trade"
                    filtered_transactions.append(deepcopy(trade_details))
                        
                
                # Adds
                transaction_ids = deepcopy(weekly_transactions.get("adds", {}).get("transaction_ids", []))
                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    add_details = self._transaction_ids_cache.get(transaction_id, {})
                    if add_details:
                        
                        # Only include adds portion of a transaction for "add" filter
                        if "add" in add_details.get("types", []):
                            
                            transaction_item = {
                                "year":           yr,
                                "week":           week,
                                "type":           "add",
                                "player":         get_image_url(add_details.get("add", ""), self._players_cache,
                                                                self._player_ids, self._image_urls_cache, self._cache,
                                                                dictionary=True),
                                "faab_spent":     add_details.get("faab_spent", None), # None if FAAB not implemented yet or a free agent add
                                "transaction_id": transaction_id
                            }
                            filtered_transactions.append(deepcopy(transaction_item))
                

                # Drops
                transaction_ids = deepcopy(weekly_transactions.get("drops", {}).get("transaction_ids", []))
                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    drop_details = self._transaction_ids_cache.get(transaction_id, {})
                    if drop_details:
                        
                        # Only include drops portion of a transaction for "drop" filter
                        if "drop" in drop_details.get("types", []):
                            
                            transaction_item = {
                                "year":           yr,
                                "week":           week,
                                "type":           "drop",
                                "player":         get_image_url(drop_details.get("drop", ""), self._players_cache,
                                                                self._player_ids, self._image_urls_cache, self._cache,
                                                                dictionary=True),
                                "transaction_id": transaction_id
                            }
                            filtered_transactions.append(deepcopy(transaction_item))
                
                # Adds and Drops
                transaction_ids = deepcopy(weekly_transactions.get("adds", {}).get("transaction_ids", []))
                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    add_drop_details = self._transaction_ids_cache.get(transaction_id, {})
                    if add_drop_details:
                        
                        # Only include add_and_drop transactions
                        if "add" in add_drop_details.get("types", []) and "drop" in add_drop_details.get("types", []):
                            transaction_item = {
                                "year":           yr,
                                "week":           week,
                                "type":           "add_and_drop",
                                "added_player":   get_image_url(add_drop_details.get("add", ""), self._players_cache,
                                                                self._player_ids, self._image_urls_cache, self._cache,
                                                                dictionary=True),
                                "dropped_player": get_image_url(add_drop_details.get("drop", ""), self._players_cache,
                                                                self._player_ids, self._image_urls_cache, self._cache,
                                                                dictionary=True),
                                "faab_spent":     add_drop_details.get("faab_spent", None), # None if FAAB not implemented yet or a free agent add/drop
                                "transaction_id": transaction_id
                            }
                            filtered_transactions.append(deepcopy(transaction_item))
                
        # Set total count
        transaction_history["total_count"] = len(filtered_transactions)

        filtered_transactions.reverse()
        
        # Set transactions in output
        transaction_history["transactions"] = deepcopy(filtered_transactions)
        
        return deepcopy(transaction_history)

    
    def get_manager_awards(self, manager: str) -> Dict:
        """
        Get all career awards and achievements for a manager.

        Includes:
        - Placements (1st/2nd/3rd place finishes)
        - Playoff appearances
        - Trade records (most trades in a year)
        - FAAB records (biggest bid)
        - Scoring records (highest/lowest weeks, biggest blowouts)

        Args:
            manager: Manager name

        Returns:
            Dictionary with manager info and all awards

        Raises:
            ValueError: If manager not found in cache
        """
        if manager not in self._cache:
            raise ValueError(f"Manager {manager} not found in cache.")
        
        awards_data = {
            "manager":   get_image_url(manager, self._players_cache,
                                       self._player_ids, self._image_urls_cache,
                                       self._cache, dictionary=True),
            "image_url": get_current_manager_image_url(manager, self._cache,
                                                       self._image_urls_cache),
            "awards":    get_manager_awards_from_cache(self._cache, manager,
                                                       self._players_cache, self._player_ids,
                                                       self._image_urls_cache)
        }
        
        score_awards = get_manager_score_awards_from_cache(self._cache, manager, self._players_cache,
                                                           self._player_ids, self._image_urls_cache,
                                                           self._starters_cache)

        awards_data["awards"].update(deepcopy(score_awards))

        return deepcopy(awards_data)