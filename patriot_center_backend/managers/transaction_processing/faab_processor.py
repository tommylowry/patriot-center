from patriot_center_backend.cache import get_cache_manager

CACHE_MANAGER = get_cache_manager()

MANAGER_CACHE = CACHE_MANAGER.get_manager_cache()


def add_faab_details_to_cache(year: str, week: str,
                              transaction_type: str, manager: str,
                              player_name: str, faab_amount: int,
                              transaction_id: str,
                              trade_partner: str = None) -> None:
    """
    Update cache with FAAB spending and trading details.

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
        faab_amount: Amount of FAAB (positive for spent/sent, negative for received in trade)
        transaction_id: Unique transaction ID
        trade_partner: Other manager in FAAB trade (required for trades)
    """
    if transaction_type == "trade" and trade_partner is None:
        print("Trade transaction missing trade partner for FAAB processing:", transaction_type, manager, player_name, faab_amount, transaction_id)
        return

    if transaction_id in MANAGER_CACHE[manager]["years"][year]["weeks"][week]["transactions"]["faab"]["transaction_ids"]:
        # Waiver already processed for this week
        return
    
    
    top_level_summary = MANAGER_CACHE[manager]["summary"]["transactions"]["faab"]
    yearly_summary = MANAGER_CACHE[manager]["years"][year]["summary"]["transactions"]["faab"]
    weekly_summary = MANAGER_CACHE[manager]["years"][year]["weeks"][week]["transactions"]["faab"]
    summaries = [top_level_summary, yearly_summary, weekly_summary]

    if transaction_type in ["free_agent", "waiver", "commissioner"]:
        # Add waiver details in all summaries
        for summary in summaries:
            # Process total lost or gained
            summary["total_lost_or_gained"] -= faab_amount

            # Process player-specific FAAB amounts
            if player_name not in summary["players"]:
                summary["players"][player_name] = {
                    'num_bids_won': 0,
                    'total_faab_spent': 0
                }
            summary["players"][player_name]['num_bids_won']     += 1
            summary["players"][player_name]['total_faab_spent'] += faab_amount
    
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