"""Cache query helpers for reading award related manager metadata."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._validators import (
    validate_matchup_data,
)
from patriot_center_backend.utils.formatters import get_matchup_card
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_manager_awards_from_cache(manager: str) -> dict[str, Any]:
    """Get manager career achievements and awards.

    Extracts:
    - First/second/third place finishes (championship counts)
    - Playoff appearances
    - Most trades in a single year
    - Biggest FAAB bid

    Args:
        manager: Manager name

    Returns:
        Dictionary with all awards and achievements
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    awards = {}

    cached_overall_data = deepcopy(
        manager_cache[manager]["summary"]["overall_data"]
    )

    # First/Second/Third Place Finishes
    placement_counts = {"first_place": 0, "second_place": 0, "third_place": 0}
    for year in cached_overall_data.get("placement", {}):
        placement = cached_overall_data["placement"][year]
        if placement == 1:
            placement_counts["first_place"] += 1
        elif placement == 2:
            placement_counts["second_place"] += 1
        elif placement == 3:
            placement_counts["third_place"] += 1
    awards.update(deepcopy(placement_counts))

    # Playoff Appearances
    awards["playoff_appearances"] = len(
        cached_overall_data.get("playoff_appearances", [])
    )

    # Most Trades in a Year
    most_trades_in_year = {"count": 0, "year": ""}

    for year in manager_cache[manager].get("years", {}):
        mgr_yr_sum = manager_cache[manager]["years"][year]["summary"]

        num_trades = mgr_yr_sum["transactions"]["trades"]["total"]
        if num_trades > most_trades_in_year["count"]:
            most_trades_in_year["count"] = num_trades
            most_trades_in_year["year"] = year
    awards["most_trades_in_year"] = deepcopy(most_trades_in_year)

    # Biggest FAAB Bid
    biggest_faab_bid = {"player": "", "amount": 0, "year": ""}
    # Check if FAAB data exists in summary before accessing
    mgr_summary = manager_cache[manager].get("summary", {})
    if (
        "faab" in mgr_summary.get("transactions", {})
        and mgr_summary["transactions"]["faab"]
    ):
        for year in manager_cache[manager].get("years", {}):
            weeks = deepcopy(manager_cache[manager]["years"][year]["weeks"])
            for week in weeks:
                weekly_trans = weeks.get(week, {}).get("transactions", {})
                weekly_faab_bids = deepcopy(
                    weekly_trans.get("faab", {}).get("players", {})
                )
                for player in weekly_faab_bids:
                    bid_amount = weekly_faab_bids[player]["total_faab_spent"]
                    if bid_amount > biggest_faab_bid["amount"]:
                        biggest_faab_bid["player"] = get_image_url(
                            player, dictionary=True
                        )
                        biggest_faab_bid["amount"] = bid_amount
                        biggest_faab_bid["year"] = year

    awards["biggest_faab_bid"] = deepcopy(biggest_faab_bid)

    return deepcopy(awards)


def get_manager_score_awards_from_cache(
    manager: str
) -> dict[str, dict[str, Any]]:
    """Get manager scoring records and extremes.

    Iterates through all matchups to find:
    - Highest weekly score
    - Lowest weekly score
    - Biggest blowout win
    - Biggest blowout loss

    Each record includes full matchup card with top/lowest scorers.

    Args:
        manager: Manager name

    Returns:
        Dictionary with all scoring records
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    score_awards = {}

    highest_weekly_score = {}
    lowest_weekly_score = {}
    biggest_blowout_win = {}
    biggest_blowout_loss = {}

    for year in manager_cache[manager].get("years", {}):
        weeks = deepcopy(manager_cache[manager]["years"][year]["weeks"])
        for week in weeks:
            matchup_data = deepcopy(weeks.get(week, {}).get("matchup_data", {}))

            validation = validate_matchup_data(matchup_data)
            if "Warning" in validation:
                print(f"{validation} {manager}, year {year}, week {week}")
                continue
            if validation == "Empty":
                continue

            points_for = matchup_data.get("points_for", 0.0)
            points_against = matchup_data.get("points_against", 0.0)
            point_differential = float(
                Decimal(points_for - points_against).quantize(Decimal("0.01"))
            )

            # Highest Weekly Score
            if points_for > highest_weekly_score.get("manager_1_score", 0.0):
                highest_weekly_score = get_matchup_card(
                    manager,
                    matchup_data.get("opponent_manager", ""),
                    year,
                    week,
                )

            # Lowest Weekly Score
            if points_for < lowest_weekly_score.get(
                "manager_1_score", float("inf")
            ):
                lowest_weekly_score = get_matchup_card(
                    manager,
                    matchup_data.get("opponent_manager", ""),
                    year,
                    week,
                )

            # Biggest Blowout Win
            if point_differential > biggest_blowout_win.get(
                "differential", 0.0
            ):
                biggest_blowout_win = get_matchup_card(
                    manager,
                    matchup_data.get("opponent_manager", ""),
                    year,
                    week,
                )
                biggest_blowout_win["differential"] = point_differential

            # Biggest Blowout Loss
            if point_differential < biggest_blowout_loss.get(
                "differential", 0.0
            ):
                biggest_blowout_loss = get_matchup_card(
                    manager,
                    matchup_data.get("opponent_manager", ""),
                    year,
                    week,
                )
                biggest_blowout_loss["differential"] = point_differential

    score_awards["highest_weekly_score"] = deepcopy(highest_weekly_score)
    score_awards["lowest_weekly_score"] = deepcopy(lowest_weekly_score)
    score_awards["biggest_blowout_win"] = deepcopy(biggest_blowout_win)
    score_awards["biggest_blowout_loss"] = deepcopy(biggest_blowout_loss)

    return deepcopy(score_awards)
