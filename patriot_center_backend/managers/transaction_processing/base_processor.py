"""
Transaction processing for manager metadata.

Handles all transaction-related operations including:
- Trade processing and reversal
- Add/drop/waiver processing
- FAAB tracking
- Transaction validation and deduplication
"""
from typing import Dict, List, Optional

from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.managers.transaction_processing import transaction_reverter
from patriot_center_backend.managers.transaction_processing.add_drop_processor import (
    process_add_or_drop_transaction,
)
from patriot_center_backend.managers.transaction_processing.trade_processor import (
    process_trade_transaction,
)
from patriot_center_backend.managers.validators import validate_transaction
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data


class TransactionProcessor:
    """
    Processes fantasy football transactions with reversal detection and FAAB tracking.

    Handles:
    - Trade processing (multi-party, draft picks, FAAB)
    - Add/drop/waiver processing
    - Transaction reversal detection (joke trades, accidental transactions)
    - FAAB spending and trading
    - Transaction deduplication
    - Cache updates at 3 levels (weekly, yearly, all-time)

    Key Features:
    - Detects and reverts reversed transactions (same managers, opposite players)
    - Tracks FAAB spent on waivers and traded between managers
    - Handles commissioner actions separately
    - Maintains global transaction ID cache for deduplication

    Uses session state pattern for thread safety during week processing.
    """

    def __init__(self, use_faab: bool) -> None:
        """
        Initialize transaction processor with cache references.

        Args:
            use_faab: Whether league uses FAAB (Free Agent Acquisition Budget)
        """
        self._use_faab = use_faab
        
        # Session state (set externally before processing)
        self._year: Optional[str] = None
        self._week: Optional[str] = None
        self._weekly_roster_ids: Dict[int, str] = {}
        self._weekly_transaction_ids: List[str] = []
    
    def set_session_state(self, year: str, week: str, weekly_roster_ids: Dict[int, str], use_faab: bool) -> None:
        """
        Set session state before processing transaction data.

        Must be called before scrub_transaction_data() to establish context.

        Args:
            year: Season year as string
            week: Week number as string
            weekly_roster_ids: Mapping of roster IDs to manager names for this week
            use_faab: Whether FAAB is used this season
        """
        self._year = year
        self._week = week
        self._weekly_roster_ids = weekly_roster_ids
        self._use_faab = use_faab
    
    def clear_session_state(self) -> None:
        """Clear session state after processing week."""
        self._year = None
        self._week = None
        self._weekly_roster_ids = {}
        self._weekly_transaction_ids = []

    def check_for_reverse_transactions(self) -> None:
        """Checks for reverse transactions"""
        transaction_reverter.check_for_reverse_transactions(self._weekly_transaction_ids)
    
    def scrub_transaction_data(self, year: str, week: str) -> None:
        """
        Fetch and process all transactions for a given week.

        Workflow:
        1. Fetch transactions from Sleeper API
        2. Reverse order (Sleeper returns newest first, we want oldest first)
        3. Process each transaction via _process_transaction
        4. Transactions are validated, categorized, and cached

        Args:
            year: Season year as string
            week: Week number as string

        Raises:
            ValueError: If no league ID found for the year
        """
        league_id = LEAGUE_IDS.get(int(year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {year}.")
        
        transactions_list = fetch_sleeper_data(f"league/{league_id}/transactions/{week}")
        
        # transactions come from sleeper newest first, we want to put them in oldest first so that when they're shown they show up its oldest at the top for a week.
        transactions_list.reverse()
        
        for transaction in transactions_list:
           self._process_transaction(transaction)
    
    def _process_transaction(self, transaction: dict) -> None:
        """
        Process a single transaction by categorizing and routing to appropriate handler.

        Workflow:
        1. Determine transaction type (trade, add_or_drop, waiver, commissioner)
        2. Normalize type (free_agent/waiver → add_or_drop)
        3. Detect commissioner actions
        4. Validate transaction
        5. Route to appropriate processor (_process_trade_transaction or _process_add_or_drop_transaction)

        Args:
            transaction: Raw transaction data from Sleeper API
        """
        transaction_type = transaction.get("type", "")
        commish_action = False

        if transaction_type in ["free_agent", "waiver"]:
            transaction_type = "add_or_drop"
        
        elif transaction_type == "commissioner":
            commish_action = True
            # No swap, so it must be add or drop
            if transaction.get("adds", None) is None:
                transaction_type = "add_or_drop"
            elif transaction.get("drops", None) is None:
                transaction_type = "add_or_drop"
            
            # if adds or drops is multiple players, its commish forced swap/trade
            elif len(transaction.get("adds", {})) >= 1 or len(transaction.get("drops", {})) >= 1:
                transaction_type = "trade"
            
            # only one add and only one drop, so add_or_drop
            else:
                transaction_type = "add_or_drop"
        

        if not validate_transaction(transaction, transaction_type, self._weekly_roster_ids):
            return
        
        if transaction_type == "add_or_drop":
            process_add_or_drop_transaction(self._year, self._week, transaction,
                                            self._weekly_roster_ids, self._weekly_transaction_ids,
                                            commish_action, self._use_faab)

        elif transaction_type == "trade":
            process_trade_transaction(self._year, self._week, transaction,
                                      self._weekly_roster_ids, self._weekly_transaction_ids,
                                      commish_action, self._use_faab)
        
        else:
            print(f"Warning, weird trade type {transaction_type}")
            print(f"     transaction: {transaction}")