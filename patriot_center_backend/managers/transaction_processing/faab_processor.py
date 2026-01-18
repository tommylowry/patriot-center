"""Process FAAB spending and trading details."""

import logging
from typing import Literal

from patriot_center_backend.cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


def add_faab_details_to_cache(
    year: str,
    week: str,
    transaction_type: Literal["waiver", "free_agent", "commissioner", "trade"],
    manager: str,
    player_name: str,
    faab_amount: int,
    transaction_id: str,
    trade_partner: str | None = None,
) -> None:
    """Update cache with FAAB spending and trading details.

    Handles two types of FAAB transactions:
    1. Waiver/free agent: FAAB spent on player acquisitions
    2. Trade: FAAB traded between managers (can be positive or negative)

    Updates cache at 3 levels (weekly, yearly, all-time) with:
    - Total FAAB lost/gained
    - Player-specific FAAB spent (for waivers)
    - Trade partner FAAB exchanges (for trades)

    Args:
        year: Year to apply the faab details
        week: Week to apply the faab details
        transaction_type: "waiver", "free_agent", "commissioner", or "trade"
        manager: Manager name
        player_name: Player name (for waivers) or "FAAB" (for trades)
        faab_amount: Amount of FAAB (positive for spent/sent, negative for
            received in trade)
        transaction_id: Unique transaction ID
        trade_partner: Other manager in FAAB trade (required for trades)
    """
    if transaction_type == "trade" and not trade_partner:
        logger.warning(
            f"Trade transaction missing trade partner for :"
            f"FAAB processing: transaction_id: {transaction_id}"
        )
        return

    manager_cache = CACHE_MANAGER.get_manager_cache()

    mgr = manager_cache[manager]
    yr_lvl = mgr["years"][year]

    if (
        transaction_id
        in yr_lvl["weeks"][week]["transactions"]["faab"]["transaction_ids"]
    ):
        return  # Waiver already processed for this week

    top_level_summary = mgr["summary"]["transactions"]["faab"]
    yearly_summary = yr_lvl["summary"]["transactions"]["faab"]
    weekly_summary = yr_lvl["weeks"][week]["transactions"]["faab"]
    summaries = [top_level_summary, yearly_summary, weekly_summary]

    if transaction_type in ["free_agent", "waiver", "commissioner"]:
        # Add waiver details in all summaries
        for summary in summaries:
            # Process total lost or gained
            summary["total_lost_or_gained"] -= faab_amount

            # Process player-specific FAAB amounts
            if player_name not in summary["players"]:
                summary["players"][player_name] = {
                    "num_bids_won": 0,
                    "total_faab_spent": 0,
                }
            summary["players"][player_name]["num_bids_won"] += 1
            summary["players"][player_name]["total_faab_spent"] += faab_amount

    elif transaction_type == "trade":
        # Add trade FAAB details in all summaries
        for summary in summaries:
            if faab_amount > 0:
                # Acquired FAAB
                summary["total_lost_or_gained"] += faab_amount

                acq_from = summary["acquired_from"]
                acq_from["total"] += faab_amount

                if trade_partner not in acq_from["trade_partners"]:
                    acq_from["trade_partners"][trade_partner] = 0
                acq_from["trade_partners"][trade_partner] += faab_amount

            # Traded FAAB away
            if faab_amount < 0:
                summary["total_lost_or_gained"] += faab_amount

                traded_away = summary["traded_away"]

                traded_away["total"] -= faab_amount
                if trade_partner not in traded_away["trade_partners"]:
                    traded_away["trade_partners"][trade_partner] = 0
                traded_away["trade_partners"][trade_partner] -= faab_amount

    else:
        logger.warning(
            f"Unexpected transaction type "
            f"for FAAB processing: {transaction_type}"
        )
        return

    # Finally, add transaction ID to weekly summary to avoid double counting
    weekly_summary["transaction_ids"].append(transaction_id)
