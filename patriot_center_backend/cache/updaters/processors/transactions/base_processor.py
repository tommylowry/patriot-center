"""Transaction processing for manager metadata."""

import logging
from typing import Any

from patriot_center_backend.cache.updaters._validators import (
    validate_transaction,
)
from patriot_center_backend.cache.updaters.processors.transactions.add_drop_processor import (  # noqa: E501
    process_add_or_drop_transaction,
)
from patriot_center_backend.cache.updaters.processors.transactions.trade_processor import (  # noqa: E501
    process_trade_transaction,
)
from patriot_center_backend.cache.updaters.processors.transactions.transaction_reverter import (  # noqa: E501
    check_for_reverse_transactions,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.models import Manager
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_roster_ids_map,
    is_faab_used,
)

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Processes fantasy transactions with reversal detection and FAAB tracking.

    Handles:
    - Trade processing (multi-party, draft picks, FAAB)
    - Add/drop/waiver processing
    - Transaction reversal detection (joke trades, accidental transactions)
    - FAAB spending and trading
    - Transaction deduplication
    - Cache updates at 3 levels (weekly, yearly, all-time)

    Key Features:
    - Detects and reverts reversed transactions (same managers,
    opposite players)
    - Tracks FAAB spent on waivers and traded between managers
    - Handles commissioner actions separately
    - Maintains global transaction ID cache for deduplication

    Uses session state pattern for thread safety during week processing.
    """

    def __init__(self, year: int, week: int) -> None:
        """Initialize transaction processor with cache references."""
        # Session state (set externally before processing)
        self._year = year
        self._week = week
        self._weekly_transaction_ids: list[str] = []

    def scrub_transaction_data(self) -> None:
        """Fetch and process all transactions for a given week.

        Workflow:
        1. Fetch transactions from Sleeper API
        2. Reverse order (Sleeper returns newest first, we want oldest first)
        3. Process each transaction via _process_transaction
        4. Transactions are validated, categorized, and cached

        Raises:
            ValueError: If no year or week is set,
                or if no league ID found for the year
        """
        league_id = LEAGUE_IDS.get(int(self._year), "")
        if not league_id:
            raise ValueError(f"No league ID found for year {self._year}.")

        transactions_list = fetch_sleeper_data(
            f"league/{league_id}/transactions/{self._week}"
        )
        if not isinstance(transactions_list, list):
            raise ValueError(
                "Sleeper API call failed to retreieve "
                "transactions in the expected list format."
            )

        use_faab = is_faab_used(self._year)
        roster_ids_map = get_roster_ids_map(
            self._year, self._week, ignore_playoffs=True
        )

        # transactions come from sleeper newest first, we want to put them
        # in oldest first so that when they're shown they show up its
        # oldest at the top for a week.
        transactions_list.reverse()

        for transaction in transactions_list:
            self._process_transaction(transaction, use_faab, roster_ids_map)

        check_for_reverse_transactions(self._weekly_transaction_ids)

    def _process_transaction(
        self, transaction: dict[str, Any],
        use_faab: bool,
        roster_ids_map: dict[int, Manager]
    ) -> None:
        """Process a single transaction by routing to appropriate handler.

        Workflow:
        1. Determine transaction type (trade, add_or_drop, waiver, commissioner)
        2. Normalize type (free_agent/waiver → add_or_drop)
        3. Detect commissioner actions
        4. Validate transaction
        5. Route to appropriate processor (`_process_trade_transaction`
            or `_process_add_or_drop_transaction`)

        Args:
            transaction: Raw transaction data from Sleeper API
            use_faab: Whether FAAB is used in the league
            roster_ids_map: Mapping of roster IDs to managers
        """
        transaction_type = transaction.get("type", "")
        commish_action = False

        if transaction_type in ["free_agent", "waiver"]:
            transaction_type = "add_or_drop"

        elif transaction_type == "commissioner":
            commish_action = True
            # No swap, so it must be add or drop
            if not transaction.get("adds") or not transaction.get("drops"):
                transaction_type = "add_or_drop"

            # if adds or drops is multiple players,
            # its commish forced swap/trade
            elif (
                len(transaction.get("adds", {})) >= 1
                or len(transaction.get("drops", {})) >= 1
            ):
                transaction_type = "trade"

            # only one add and only one drop, so add_or_drop
            else:
                transaction_type = "add_or_drop"

        if not validate_transaction(
            transaction, transaction_type, roster_ids_map
        ):
            return

        if transaction_type == "add_or_drop":
            process_add_or_drop_transaction(
                str(self._year),
                str(self._week),
                transaction,
                roster_ids_map,
                self._weekly_transaction_ids,
                commish_action,
                use_faab,
            )

        elif transaction_type == "trade":
            process_trade_transaction(
                str(self._year),
                str(self._week),
                transaction,
                roster_ids_map,
                self._weekly_transaction_ids,
                commish_action,
                use_faab,
            )

        else:
            logger.warning(
                f"Skipping unexpected trade type {transaction_type} "
                f"with transaction: {transaction}"
            )
