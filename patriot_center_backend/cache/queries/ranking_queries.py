"""Cache query helpers for ranking related manager metadata."""

from dataclasses import asdict, dataclass, fields
from typing import Any

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


def get_ranking_details_from_cache(
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
            if i > 0 and getattr(entry.values, field.name) != getattr(
                sorted_entries[i - 1].values, field.name
            ):
                rank = i + 1
            results[entry.manager]["ranks"][field.name] = rank

    return results
