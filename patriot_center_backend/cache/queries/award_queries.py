"""Cache query helpers for reading award related manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.formatters import get_matchup_card


def get_manager_awards_from_cache(manager_obj: Manager) -> dict[str, Any]:
    """Get manager career achievements and awards.

    Extracts:
    - First/second/third place finishes (championship counts)
    - Playoff appearances
    - Most trades in a single year
    - Biggest FAAB bid

    Args:
        manager_obj: Manager object

    Returns:
        Dictionary with all awards and achievements
    """
    # TODO: remove this once managers are stored in cache
    manager = manager_obj.real_name
    # END TODO
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

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

    for year in list(manager_cache[manager].get("years", {})):
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
        for year in list(manager_cache[manager].get("years", {})):
            weeks = deepcopy(manager_cache[manager]["years"][year]["weeks"])
            for week in weeks:
                weekly_trans = weeks.get(week, {}).get("transactions", {})
                weekly_faab_bids = deepcopy(
                    weekly_trans.get("faab", {}).get("players", {})
                )
                for player_id in weekly_faab_bids:
                    player = Player(player_id)
                    bid_amount = weekly_faab_bids[str(player)][
                        "total_faab_spent"
                    ]
                    if bid_amount > biggest_faab_bid["amount"]:
                        biggest_faab_bid["player"] = player.get_metadata()
                        biggest_faab_bid["amount"] = bid_amount
                        biggest_faab_bid["year"] = year

    awards["biggest_faab_bid"] = deepcopy(biggest_faab_bid)

    return deepcopy(awards)


def get_manager_score_awards_from_cache(
    maanager: Manager,
) -> dict[str, dict[str, Any]]:
    """Get manager scoring records and extremes.

    Iterates through all matchups to find:
    - Highest weekly score
    - Lowest weekly score
    - Biggest blowout win
    - Biggest blowout loss

    Each record includes full matchup card with top/lowest scorers.

    Args:
        maanager: Manager object

    Returns:
        Dictionary with all scoring records
    """
    score_awards = {}

    matchups = maanager.get_score_awards()

    for key in matchups:
        score_awards[key] = get_matchup_card(
            maanager,
            matchups[key]["opponent"],
            matchups[key]["year"],
            matchups[key]["week"],
        )

    return deepcopy(score_awards)
