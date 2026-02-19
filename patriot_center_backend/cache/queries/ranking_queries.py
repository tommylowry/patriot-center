"""Cache query helpers for ranking related manager metadata."""

import time
from copy import deepcopy
from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, TOMMY_USER_ID
from patriot_center_backend.models import Manager, Transaction
from patriot_center_backend.models.transaction import TransactionType


@dataclass
class ManagerValues:
    """Class for manager values."""
    win_percentage: float
    average_points_for: float
    average_points_against: float
    average_points_differential: float
    trades: int
    playoffs: int

@dataclass
class ManagerRankingEntry:
    """Class for manager ranking entry."""
    manager: Manager
    is_active_manager: bool
    worst: int
    values: ManagerValues


def new_get_ranking_details_from_cache(
    active_only: bool = True,
    year: str | None = None,
) -> dict[Manager, dict[str, Any]]:
    """Get ranking details for all managers.

    Args:
        active_only: If True, only return active managers.
        year: Season year (optional - defaults to all-time)

    Returns:
        Dictionary with managers and their rankings
    """
    managers = Manager.get_managers(year=year, active_only=active_only)

    all_trades = Transaction.get_transactions(
        year=year,
        transaction_type=TransactionType.TRADE,
    )

    trades_counts: dict[Manager, int] = {}
    for trade in all_trades:
        for manager in trade.managers_involved:
            trades_counts[manager] = trades_counts.get(manager, 0) + 1

    # Collect all values
    all_entries: list[ManagerRankingEntry] = []
    for manager in managers:
        matchup_data = manager.get_matchup_data_summary(year=year)

        manager_values = ManagerValues(
            win_percentage=matchup_data["win_percentage"],
            average_points_for=matchup_data["average_points_for"],
            average_points_against=matchup_data["average_points_against"],
            average_points_differential=matchup_data[
                "average_point_differential"
            ],
            trades=trades_counts.get(manager, 0),
            playoffs=len(manager.get_playoff_appearances_list()),
        )

        all_entries.append(
            ManagerRankingEntry(
                manager=manager,
                is_active_manager=manager.is_active(),
                worst=len(managers),
                values=manager_values,
            )
        )

    # Rank each category
    results: dict[Manager, dict[str, Any]] = {}
    for entry in all_entries:
        results[entry.manager] = {
            "values": asdict(entry.values),
            "ranks": {
                "is_active_manager": entry.is_active_manager,
                "worst": entry.worst,
            },
        }

    for field in fields(ManagerValues):
        sorted_entries = sorted(
            all_entries,
            key=lambda e: getattr(e.values, field.name),
            reverse=True,
        )
        rank = 1
        for i, entry in enumerate(sorted_entries):
            if (
                i > 0
                and getattr(entry.values, field.name)
                != getattr(
                    sorted_entries[i - 1].values, field.name
                )
            ):
                rank = i + 1
            results[entry.manager]["ranks"][field.name] = rank

    return results


def get_ranking_details_from_cache(
    manager: str,
    manager_summary_usage: bool = False,
    active_only: bool = True,
    year: str | None = None,
) -> dict[str, Any] | dict[str, dict[str, Any]]:
    """Calculate manager rankings across all statistical categories.

    Compares manager against all active (or all) managers in 6 categories:
    - Win percentage
    - Average points for
    - Average points against
    - Average point differential
    - Total trades
    - Playoff appearances

    Handles ties properly - managers with same stat value get same rank.

    Args:
        manager: Manager to rank
        manager_summary_usage: If True, returns both values and ranks
            otherwise returns only ranks
        active_only: If True, only rank against active managers
            otherwise rank against all
        year: Season year (optional - defaults to all-time stats if None)

    Returns:
        Dict of rankings by category
        or dict with 'values' and 'ranks' if manager_summary_usage=True
    """
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    returning_dictionary = {}

    manager_rankings = {
        "win_percentage": [],
        "average_points_for": [],
        "average_points_against": [],
        "average_points_differential": [],
        "trades": [],
        "playoffs": [],
    }

    eval_manager_values = {
        "win_percentage": 0.0,
        "average_points_for": 0.0,
        "average_points_against": 0.0,
        "average_points_differential": 0.0,
        "trades": 0,
        "playoffs": 0,
    }

    current_year = year if year else str(max(LEAGUE_IDS.keys()))

    managers = deepcopy(valid_options_cache[current_year]["managers"])

    returning_dictionary["is_active_manager"] = True
    if manager not in managers:
        returning_dictionary["is_active_manager"] = False
        managers = list(manager_cache.keys())

    if not active_only:
        managers = list(manager_cache.keys())

    returning_dictionary["worst"] = len(managers)

    for m in managers:
        manager_data = deepcopy(manager_cache.get(m, {}))

        summary_section = manager_data.get("summary", {})
        if year:
            summary_section = (
                manager_data.get("years", {}).get(year, {}).get("summary", {})
            )

        ovr_matchup_data = summary_section["matchup_data"]["overall"]

        # Extract record components
        num_wins = ovr_matchup_data["wins"]["total"]
        num_losses = ovr_matchup_data["losses"]["total"]
        num_ties = ovr_matchup_data["ties"]["total"]

        # Calculate win percentage
        num_matchups = num_wins + num_losses + num_ties

        win_pct = 0.0
        if num_matchups != 0:
            win_pct = (num_wins / num_matchups) * 100
            win_pct = float(Decimal(win_pct).quantize(Decimal("0.1")))

        # Points for/against and averages
        tot_pf = ovr_matchup_data["points_for"]["total"]
        tot_pa = ovr_matchup_data["points_against"]["total"]

        avg_pf = 0.0
        avg_pa = 0.0
        avg_pd = 0.0
        if num_matchups != 0:
            avg_pf = tot_pf / num_matchups
            avg_pf = float(Decimal(avg_pf).quantize(Decimal("0.01")))

            avg_pa = tot_pa / num_matchups
            avg_pa = float(Decimal(avg_pa).quantize(Decimal("0.01")))

            avg_pd = (tot_pf - tot_pa) / num_matchups
            avg_pd = float(Decimal(avg_pd).quantize(Decimal("0.01")))

        num_trades = summary_section["transactions"]["trades"]["total"]
        num_playoffs = len(
            manager_data.get("summary", {})
            .get("overall_data", {})
            .get("playoff_appearances", [])
        )

        manager_rankings["win_percentage"].append({m: win_pct})
        manager_rankings["average_points_for"].append({m: avg_pf})
        manager_rankings["average_points_against"].append({m: avg_pa})
        manager_rankings["average_points_differential"].append({m: avg_pd})
        manager_rankings["trades"].append({m: num_trades})
        manager_rankings["playoffs"].append({m: num_playoffs})

        if m == manager:
            eval_manager_values["win_percentage"] = win_pct
            eval_manager_values["average_points_for"] = avg_pf
            eval_manager_values["average_points_against"] = avg_pa
            eval_manager_values["average_points_differential"] = avg_pd
            eval_manager_values["trades"] = num_trades
            eval_manager_values["playoffs"] = num_playoffs

    for k in manager_rankings:
        manager_rankings[k].sort(
            key=lambda item: next(iter(item.values())), reverse=True
        )

        rank = 1
        manager_value = eval_manager_values[k]
        for item in manager_rankings[k]:
            value = item[next(iter(item.keys()))]
            if value != manager_value:
                # If the value is different from the
                # previous one, update the rank
                rank += 1
            else:
                returning_dictionary[k] = rank
                break

    if manager_summary_usage:
        return {
            "values": deepcopy(eval_manager_values),
            "ranks": deepcopy(returning_dictionary),
        }

    return deepcopy(returning_dictionary)
