"""Data exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.cache_queries.award_queries import (
    get_manager_awards_from_cache,
    get_manager_score_awards_from_cache,
)
from patriot_center_backend.managers.cache_queries.head_to_head_queries import (
    get_head_to_head_details_from_cache,
    get_head_to_head_overall_from_cache,
)
from patriot_center_backend.managers.cache_queries.matchup_queries import (
    get_matchup_details_from_cache,
    get_overall_data_details_from_cache,
)
from patriot_center_backend.managers.cache_queries.ranking_queries import (
    get_ranking_details_from_cache,
)
from patriot_center_backend.managers.cache_queries.transaction_queries import (
    get_trade_history_between_two_managers,
    get_transaction_details_from_cache,
)
from patriot_center_backend.managers.formatters import get_trade_card
from patriot_center_backend.utils.image_providers import (
    get_current_manager_image_url,
    get_image_url,
)


class DataExporter:
    """Data exporter for manager metadata."""

    def __init__(self) -> None:
        """Initialize a DataExporter object."""
        self._image_urls: dict[str, str] = {}

    def get_managers_list(self, active_only: bool) -> dict[str, Any]:
        """Get a list of all managers in the system.

        Args:
            active_only: If True, only return active managers.

        Returns:
            A dictionary containing a list of manager metadata.
            Each manager is represented as a dictionary with the following keys:
                name: The manager's name.
                image_url: The URL of the manager's image.
                years_active: A list of years the manager has been active.
                total_trades: The total number of trades the manager has made.
                wins: The total number of wins the manager has.
                losses: The total number of losses the manager has.
                ties: The total number of ties the manager has.
                win_percentage: The manager's win percentage.
                placements: A dictionary containing the number of
                    first, second, and third place finishes the manager has.
                playoff_appearances: The number of times the manager has
                    appeared in the playoffs.
                best_finish: The best finish the manager has achieved.
                average_points_for: The average number of points the manager
                    gets for each win.
                total_adds: The total number of adds the manager has made.
                total_drops: The total number of drops the manager has made.
                is_active: If the manager is currently active.
                rankings: A dictionary containing the manager's rankings in
                    different categories.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        current_year = str(max(LEAGUE_IDS.keys()))

        managers = valid_options_cache[current_year]["managers"]
        if not active_only:
            managers = list(manager_cache.keys())

        managers_list = []

        for manager in managers:
            wins = (
                manager_cache[manager]["summary"]["matchup_data"]["overall"]["wins"]["total"]
            )

            losses = (
                manager_cache[manager]["summary"]["matchup_data"]["overall"]["losses"]["total"]
            )

            ties = (
                manager_cache[manager]["summary"]["matchup_data"]["overall"]["ties"]["total"]
            )

            ranking_details = get_ranking_details_from_cache(
                manager, manager_summary_usage=True, active_only=active_only
            )

            manager_item = {
                "name": manager,
                "image_url": get_current_manager_image_url(
                    manager, self._image_urls
                ),

                "years_active": list(
                    manager_cache[manager].get("years", {}).keys()
                ),

                "total_trades": (
                    manager_cache[manager]["summary"]["transactions"]["trades"]["total"]
                ),

                "wins": wins,
                "losses": losses,
                "ties": ties,
                "win_percentage": ranking_details['values']['win_percentage']
            }

            placements = {
                "first_place": 0,
                "second_place": 0,
                "third_place": 0
            }

            playoff_appearances = ranking_details['values']['playoffs']
            best_finish = 4

            overall_data_placements = (
                manager_cache[manager]['summary']['overall_data']['placement']
            )

            for y in overall_data_placements:
                year_placement = (
                    manager_cache[manager]['summary']['overall_data']['placement'][y]
                )

                if year_placement == 1:
                    placements['first_place'] += 1
                if year_placement == 2:
                    placements['second_place'] += 1
                if year_placement == 3:
                    placements['third_place'] += 1
                if year_placement < best_finish:
                    best_finish = year_placement

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

            manager_item["placements"] = deepcopy(placements)
            manager_item["playoff_appearances"] = (
                ranking_details['values']['playoffs']
            )

            manager_item["best_finish"] = best_finish
            manager_item["average_points_for"] = (
                ranking_details['values']['average_points_for']
            )

            manager_item["total_adds"] = (
                manager_cache[manager]['summary']['transactions']['adds']['total']
            )

            manager_item["total_drops"] = (
                manager_cache[manager]['summary']['transactions']['drops']['total']
            )

            manager_item["is_active"] = (
                ranking_details['ranks']['is_active_manager']
            )

            rankings = {
                "win_percentage": ranking_details['ranks']['win_percentage'],
                "average_points_for": (
                    ranking_details['ranks']['average_points_for']
                ),

                "trades": ranking_details['ranks']['trades'],
                "playoffs": ranking_details['ranks']['playoffs'],
                "worst": ranking_details['ranks']['worst']
            }

            manager_item["rankings"] = deepcopy(rankings)

            managers_list.append(manager_item)

        return {"managers": managers_list}

    def get_manager_summary(
        self, manager: str, year: str | None = None
    ) -> dict[str, Any]:
        """Get comprehensive manager summary.

        Includes:
        - Manager name and image URL
        - List of years active
        - Matchup data (wins, losses, ties, win percentage,
            average points for/against)
        - Transaction data (adds, drops, trades)
        - Overall data (placement counts, playoff appearances,
            biggest blowout win/loss)
        - Rankings (win percentage, average points for, trades, playoffs,
            worst finish)
        - Head-to-head data (wins, losses, ties, points for/against,
            num trades between)

        Args:
            manager: Manager name
            year: Season year (optional - defaults to all-time)

        Returns:
            dictionary with all manager summary data

        Raises:
            ValueError: If manager or year is not found in cache
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        if manager not in manager_cache:
            raise ValueError(
                f"Manager {manager} not found in cache."
            )

        if year and year not in manager_cache[manager]["years"]:
            raise ValueError(
                f"Year {year} not found for manager {manager} in cache."
            )

        return_dict = {}
        return_dict["manager_name"] = manager
        return_dict["image_url"] = get_current_manager_image_url(
            manager, self._image_urls
        )

        return_dict["years_active"] = list(
            manager_cache[manager].get("years", {}).keys()
        )

        return_dict["matchup_data"] = get_matchup_details_from_cache(
            manager, year=year
        )

        return_dict["transactions"] = get_transaction_details_from_cache(
            year, manager, self._image_urls
        )

        return_dict["overall_data"] = get_overall_data_details_from_cache(
            year, manager, self._image_urls
        )

        return_dict["rankings"] = get_ranking_details_from_cache(
            manager, year=year
        )

        return_dict["head_to_head"] = get_head_to_head_details_from_cache(
            manager, self._image_urls, year=year
        )

        return deepcopy(return_dict)

    def get_head_to_head(
        self, manager1: str, manager2: str, year: str | None = None
    ) -> dict[str, Any]:
        """Get comprehensive head-to-head analysis between two managers.

        Iterates through all matchups to find:
        - Overall win/loss/tie record
        - Average margin of victory for each manager
        - Last win for each manager (most recent)
        - Biggest blowout for each manager

        Args:
            manager1: First manager name
            manager2: Second manager name
            year: Season year (optional - defaults to all-time)

        Returns:
            dictionary with all head-to-head data, including overall data,
                matchup history, and trades between the two managers

        Raises:
            ValueError: If manager or year is not found in cache
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        return_dict = {}

        for manager in [manager1, manager2]:

            if manager not in manager_cache:
                raise ValueError(
                    f"Manager {manager} not found in cache."
                )
            if year and year not in manager_cache[manager]["years"]:
                raise ValueError(
                    f"Year {year} not found for manager {manager} in cache."
                )

            manager = {
                "name": manager,
                "image_url": get_current_manager_image_url(
                    manager, self._image_urls
                )
            }

            if "manager_1" not in return_dict:
                return_dict["manager_1"] = deepcopy(manager)
            else:
                return_dict["manager_2"] = deepcopy(manager)

        return_dict["overall"] = get_head_to_head_overall_from_cache(
            manager1, manager2, self._image_urls, year=year
        )

        return_dict["matchup_history"] = get_head_to_head_overall_from_cache(
            manager1,
            manager2,
            self._image_urls,
            year=year,
            list_all_matchups=True
        )

        trades_between = get_trade_history_between_two_managers(
            manager1, manager2, self._image_urls, year=year
        )

        return_dict["trades_between"] = {
            "total": len(trades_between),
            "trade_history": trades_between
        }

        return deepcopy(return_dict)

    def get_manager_transactions(
        self, manager_name: str, year: str | None = None
    ) -> dict[str, Any]:
        """Get manager transaction history.

        Args:
            manager_name: The name of the manager.
            year: Optional year to filter transactions.

        Returns:
            dictionary with manager transaction history.

        Raises:
            ValueError: If manager or year is not found in cache.
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()
        transaction_ids_cache = CACHE_MANAGER.get_transaction_ids_cache()

        if manager_name not in manager_cache:
            raise ValueError(
                f"Manager {manager_name} not found in cache."
            )
        if year and year not in manager_cache[manager_name]["years"]:
            raise ValueError(
                f"Year {year} not found for manager "
                f"{manager_name} in cache."
            )

        transaction_history = {
            "name": get_image_url(
                manager_name, self._image_urls, dictionary=True
            ),

            "total_count": 0,
            "transactions": []
        }

        # Gather transactions based on filters
        filtered_transactions = []
        years_to_check = [year] if year else list(
            manager_cache[manager_name]["years"].keys()
        )

        for yr in years_to_check:
            yearly_data = manager_cache[manager_name]["years"][yr]
            for week in yearly_data.get("weeks", {}):
                weekly_transactions = deepcopy(
                    yearly_data["weeks"][week]["transactions"])

                # Trades
                trade_data = weekly_transactions.get("trades", {})
                transaction_ids = deepcopy(
                    trade_data.get("transaction_ids", [])
                )

                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    trade_details = get_trade_card(
                        transaction_id, self._image_urls
                    )

                    trade_details["type"] = "trade"
                    filtered_transactions.append(deepcopy(trade_details))

                # Adds
                adds_data = weekly_transactions.get("adds", {})
                transaction_ids = deepcopy(
                    adds_data.get("transaction_ids", [])
                )

                transaction_ids.reverse()
                for transaction_id in transaction_ids:

                    # Only include adds portion of a
                    #   transaction for "add" filter
                    add_details = transaction_ids_cache.get(transaction_id, {})
                    if add_details and "add" in add_details.get("types", []):

                        transaction_item = {
                            "year": yr,
                            "week": week,
                            "type": "add",
                            "player": get_image_url(
                                add_details.get("add", ""),
                                self._image_urls,
                                dictionary=True
                            ),

                            # None if FAAB not implemented yet
                            #   or a free agent add
                            "faab_spent": add_details.get(
                                "faab_spent", None
                            ),

                            "transaction_id": transaction_id
                        }
                        filtered_transactions.append(deepcopy(transaction_item))

                # Drops
                drops_data = weekly_transactions.get("drops", {})
                transaction_ids = deepcopy(
                    drops_data.get("transaction_ids", [])
                )

                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    drop_details = transaction_ids_cache.get(transaction_id, {})
                    if drop_details and "drop" in drop_details.get("types", []):

                        transaction_item = {
                            "year": yr,
                            "week": week,
                            "type": "drop",
                            "player": get_image_url(
                                drop_details.get("drop", ""),
                                self._image_urls,
                                dictionary=True
                            ),

                            "transaction_id": transaction_id
                        }
                        filtered_transactions.append(deepcopy(transaction_item))

                # Adds and Drops
                adds_data = weekly_transactions.get("adds", {})
                transaction_ids = deepcopy(
                    adds_data.get("transaction_ids", [])
                )

                transaction_ids.reverse()
                for transaction_id in transaction_ids:
                    add_drop_details = (
                        transaction_ids_cache.get(transaction_id, {})
                    )

                    # Only include add_and_drop transactions
                    types = add_drop_details.get("types", [])
                    if types and "add" in types and "drop" in types:

                            transaction_item = {
                                "year": yr,
                                "week": week,
                                "type": "add_and_drop",
                                "added_player": get_image_url(
                                    add_drop_details.get("add", ""),
                                    self._image_urls,
                                    dictionary=True
                                ),

                                "dropped_player": get_image_url(
                                    add_drop_details.get("drop", ""),
                                    self._image_urls,
                                    dictionary=True
                                ),

                                # None if FAAB not implemented yet
                                # or a free agent add/drop
                                "faab_spent": (
                                    add_drop_details.get("faab_spent", None)
                                ),

                                "transaction_id": transaction_id
                            }
                            filtered_transactions.append(deepcopy(transaction_item))

        # Set total count
        transaction_history["total_count"] = len(filtered_transactions)

        filtered_transactions.reverse()

        # Set transactions in output
        transaction_history["transactions"] = deepcopy(filtered_transactions)

        return deepcopy(transaction_history)

    def get_manager_awards(self, manager: str) -> dict[str, Any]:
        """Get awards and recognitions for a specific manager.

        Args:
            manager: Manager name

        Returns:
            dictionary with manager awards and recognitions

        Raises:
            ValueError: If manager is not found in cache
        """
        manager_cache = CACHE_MANAGER.get_manager_cache()

        if manager not in manager_cache:
            raise ValueError(
                f"Manager {manager} not found in cache."
            )

        awards_data = {
            "manager": get_image_url(
                manager, self._image_urls, dictionary=True
            ),

            "image_url": get_current_manager_image_url(
                manager, self._image_urls
            ),

            "awards": get_manager_awards_from_cache(
                manager, self._image_urls
            )
        }
        score_awards = get_manager_score_awards_from_cache(
            manager, self._image_urls
        )

        awards_data["awards"].update(deepcopy(score_awards))

        return deepcopy(awards_data)
