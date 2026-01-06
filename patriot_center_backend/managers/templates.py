"""
Template initialization for manager metadata structures.

This module provides template definitions for FAAB tracking and summary data.
All templates are pure functions with no side effects.
"""
from copy import deepcopy

from patriot_center_backend.cache import get_cache_manager

CACHE_MANAGER = get_cache_manager()
MANAGER_CACHE = CACHE_MANAGER.get_manager_cache()

# faab_template used by both methods
faab_template = {
    "total_lost_or_gained": 0,
    "players":{
        # "player_name": {
        #  'num_bids_won': 0,
        #  'total_faab_spent': 0
        #}
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

def initialize_faab_template(manager: str, year: str, week: str) -> dict:
    """
    Initialize FAAB template for a specific year/week.
    
    Args:
        manager: Manager needing the faab template
        year: Season year as string
        week: Week number as string
    """
    if "faab" not in MANAGER_CACHE[manager]["summary"]["transactions"]:
        MANAGER_CACHE[manager]["summary"]["transactions"]["faab"] = deepcopy(faab_template)
    
    if "faab" not in MANAGER_CACHE[manager]["years"][year]["summary"]["transactions"]:
        MANAGER_CACHE[manager]["years"][year]["summary"]["transactions"]["faab"] = deepcopy(faab_template)
        
    if "faab" not in MANAGER_CACHE[manager]["years"][year]["weeks"][week]["transactions"]:
        faab_template_with_transaction_ids = deepcopy(faab_template)
        faab_template_with_transaction_ids["transaction_ids"] = []
        MANAGER_CACHE[manager]["years"][year]["weeks"][week]["transactions"]["faab"] = deepcopy(faab_template_with_transaction_ids)

def initialize_summary_templates(use_faab: bool) -> dict:
    """
    Initialize all summary templates.
    
    Args:
        use_faab: Whether FAAB is used in the league
    
    Returns:
        Dictionary containing all template structures:
        - yearly_summary_template
        - weekly_summary_template
        - weekly_summary_template_not_in_playoffs
        - top_level_summary_template
    """
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
        "points_for":     deepcopy(matchup_data_float),
        "points_against": deepcopy(matchup_data_float),
        "total_matchups": deepcopy(matchup_data_int),
        "wins":           deepcopy(matchup_data_int),
        "losses":         deepcopy(matchup_data_int),
        "ties":           deepcopy(matchup_data_int)
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
        #         # "player_name": {
        #         #     'num_bids_won': 0,
        #         #     'total_faab_spent': 0
        #         # }
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

    if use_faab:
        transaction_data["faab"] = deepcopy(faab_template)
    
    yearly_summary_template = {
        "matchup_data": {
            "overall":        deepcopy(full_matchup_data),
            "regular_season": deepcopy(full_matchup_data),
            "playoffs":       deepcopy(full_matchup_data)
        },
        "transactions": deepcopy(transaction_data)
    }

    weekly_summary_template = {
        "matchup_data": {
            "opponent_manager": None,
            "result": None,  # "win", "loss", "tie"
            "points_for": 0.0,
            "points_against": 0.0
        },
        "transactions": deepcopy(transaction_data)
    }

    weekly_summary_template_not_in_playoffs = {
        "matchup_data": {}, # No matchup data when not in playoffs
        "transactions": deepcopy(transaction_data)
    }

    weekly_summary_template["transactions"]["trades"]["transaction_ids"] = []
    weekly_summary_template["transactions"]["adds"]["transaction_ids"] = []
    weekly_summary_template["transactions"]["drops"]["transaction_ids"] = []
    weekly_summary_template_not_in_playoffs["transactions"]["trades"]["transaction_ids"] = []
    weekly_summary_template_not_in_playoffs["transactions"]["adds"]["transaction_ids"] = []
    weekly_summary_template_not_in_playoffs["transactions"]["drops"]["transaction_ids"] = []

    if use_faab:
        weekly_summary_template["transactions"]["faab"]["transaction_ids"] = []

    top_level_summary_template = deepcopy(yearly_summary_template)
    top_level_summary_template["overall_data"] = {
        "placement": {
            # "year": placement
        },
        "playoff_appearances": [ 
            # list of years with playoff appearances 
        ]
    }


    return {
        "yearly_summary_template": yearly_summary_template,
        "weekly_summary_template": weekly_summary_template,
        "weekly_summary_not_in_playoffs_template": weekly_summary_template_not_in_playoffs,
        "top_level_summary_template": top_level_summary_template
    }