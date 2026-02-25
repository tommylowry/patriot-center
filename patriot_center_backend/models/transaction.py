"""Transaction class."""

from __future__ import annotations

import logging
from copy import deepcopy
from enum import StrEnum
from typing import Any, ClassVar

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.models.manager import Manager
from patriot_center_backend.models.player import Player

logger = logging.getLogger(__name__)

class TransactionType(StrEnum):
    """Enum for transaction types."""
    TRADE = "trade"
    ADD = "add"
    DROP = "drop"


class Transaction:
    """Transaction class.

    Uses singleton pattern via __new__ - instances are stored in
    _instances and never garbage collected. B019 warnings for
    @cache on methods are safe to suppress in this context.
    """
    _instances: ClassVar[dict[str, Transaction]] = {}

    def __new__(cls, transaction_id: str) -> Transaction:
        """Create a new transaction instance or return the existing one.

        Args:
            transaction_id: The transaction ID

        Returns:
            The transaction instance
        """
        if transaction_id in cls._instances:
            return cls._instances[transaction_id]
        instance = super().__new__(cls)
        cls._instances[transaction_id] = instance
        return instance

    def __init__(self, transaction_id: str) -> None:
        """Transaction class.

        Args:
            transaction_id: The transaction ID
        """
        if hasattr(self, "_initialized"):
            return  # Already initialized
        self._initialized = True
        self.set = False

        self.transaction_id = transaction_id

        self.commish_action: bool = False

        self.transaction_types: set[TransactionType] = set()
        self.gained: dict[Manager, set[Player]] = {}
        self.lost: dict[Manager, set[Player]] = {}

        self.managers_involved: set[Manager] = set()
        self.players_involved: set[Player] = set()

        self.faab_spent: int | None = None

        self._load_from_cache()

    def __str__(self) -> str:
        """String representation of the transaction.

        Returns:
            The transaction ID
        """
        return self.transaction_id

    @classmethod
    def load_all_transactions(cls) -> None:
        """Load all transactions into the cache."""
        cls.get_transactions()

    @classmethod
    def get_transactions(
        cls,
        year: str | None = None,
        week: str | None = None,
        transaction_types: list[TransactionType] | None = None,
        transaction_type: TransactionType | None = None,
        managers_involved: list[Manager] | None = None,
        manager_involved: Manager | None = None,
        players_involved: list[Player] | None = None,
        player_involved: Player | None = None
    ) -> list[Transaction]:
        """Get all data entries matching the given filters.

        Args:
            year: Filter by year.
            week: Filter by week.
            transaction_types: Filter by transaction types.
            transaction_type: Filter by transaction type.
            managers_involved: Filter by trade partners.
            manager_involved: Filter by trade partner.
            players_involved: Filter by players involved.
            player_involved: Filter by player involved.

        Note:
            Cannot filter by both transaction_type and transaction_types
            Cannot filter by both manager_involved and managers_involved
            Cannot filter by both player_involved and players_involved

        Returns:
            List of matching data entries.

        Raises:
            ValueError: If both transaction_type and transaction_types
                are provided.
            ValueError: If both manager_involved and managers_involved are
                provided.
            ValueError: If both player_involved and players_involved
                are provided.
        """
        transaction_cache = CACHE_MANAGER.get_transaction_cache()

        if not transaction_cache:
            return []

        if transaction_type and transaction_types:
            raise ValueError(
                "Cannot filter by both transaction_type and transaction_types"
            )
        if manager_involved and managers_involved:
            raise ValueError(
                "Cannot filter by both manager_involved and managers_involved"
            )
        if player_involved and players_involved:
            raise ValueError(
                "Cannot filter by both player_involved and players_involved"
            )

        if transaction_type:
            transaction_types = [transaction_type]
        if manager_involved:
            managers_involved = [manager_involved]
        if player_involved:
            players_involved = [player_involved]

        returning_transactions = []

        for transaction_id in transaction_cache:
            transaction = cls(transaction_id)
            if year and transaction.year != year:
                continue
            if week and transaction.week != week:
                continue
            if transaction_types and not (
                set(transaction_types) & transaction.transaction_types
            ):
                continue
            if managers_involved and not set(managers_involved).issubset(
                transaction.managers_involved
            ):
                continue
            if players_involved and not set(players_involved).issubset(
                transaction.players_involved
            ):
                continue
            returning_transactions.append(transaction)

        returning_transactions.reverse()
        return returning_transactions

    def apply_transaction(
        self, year: str, week: str, transaction: dict[str, Any],
    ) -> bool:
        """Apply transaction to cache.

        Args:
            year: The year of the transaction.
            week: The week of the transaction.
            transaction: The transaction data.

        Returns:
            Whether the transaction was applied.
        """
        from patriot_center_backend.utils.sleeper_helpers import (
            get_roster_ids_map,
        )

        self.year = year
        self.week = week

        # Only for this function
        self._transaction = transaction
        self._roster_id_map = get_roster_ids_map(
            int(year), int(week), ignore_playoffs=True
        )
        self._input_adds: dict[str, int] | None = transaction.get("adds")
        self._input_drops: dict[str, int] | None = transaction.get("drops")
        self._input_draft_picks: list[dict[str, Any]] | None = (
            transaction.get("draft_picks")
        )

        res = self._set_transaction_types()
        if not res:
            self.delete()
            return False

        self._set_gained()
        self._set_lost()
        self._set_draft_picks()
        self._set_faab()

        self.managers_involved = (
            set(self.gained) | set(self.lost)
        )
        self.players_involved = (
            {p for ps in self.gained.values() for p in ps}
            | {p for ps in self.lost.values() for p in ps}
        )

        del self._transaction
        del self._roster_id_map
        del self._input_adds
        del self._input_drops
        del self._input_draft_picks

        self._apply_to_cache()

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert the transaction to a dictionary.

        Returns:
            The transaction as a dictionary.

        """
        return {
            "year": self.year,
            "week": self.week,
            "commish_action": self.commish_action,
            "transaction_types": [
                str(t) for t in self.transaction_types
            ],
            "gained": {
                str(m): [str(p) for p in ps] for m, ps in self.gained.items()
            },
            "lost": {
                str(m): [str(p) for p in ps] for m, ps in self.lost.items()
            },
            "faab_spent": self.faab_spent,
        }

    def delete(self) -> None:
        """Delete the transaction from the cache."""
        transaction_cache = CACHE_MANAGER.get_transaction_cache()
        if self.transaction_id in transaction_cache:
            del transaction_cache[self.transaction_id]
        Transaction._instances.pop(self.transaction_id, None)

    def _load_from_cache(self) -> None:
        """Loads transaction data from cache."""
        transaction_cache = CACHE_MANAGER.get_transaction_cache()

        if self.transaction_id not in transaction_cache:
            return

        transaction_data = deepcopy(transaction_cache[self.transaction_id])

        self.year = transaction_data["year"]
        self.week = transaction_data["week"]
        self.commish_action = transaction_data["commish_action"]

        self.transaction_types = {
            TransactionType(t)
            for t in transaction_data["transaction_types"]
        }

        self.gained: dict[Manager, set[Player]] = {
            Manager(m): {Player(p) for p in ps}
            for m, ps in transaction_data["gained"].items()
        }
        self.lost: dict[Manager, set[Player]] = {
            Manager(m): {Player(p) for p in ps}
            for m, ps in transaction_data["lost"].items()
        }

        self.faab_spent = transaction_data["faab_spent"]

        self.managers_involved = (
            set(self.gained) | set(self.lost)
        )
        self.players_involved = (
            {p for ps in self.gained.values() for p in ps}
            | {p for ps in self.lost.values() for p in ps}
        )

    def _apply_to_cache(self) -> None:
        """Applies the transaction data to the cache."""
        transaction_cache = CACHE_MANAGER.get_transaction_cache()

        transaction_cache[self.transaction_id] = self.to_dict()
        self.set = True

    def _set_transaction_types(self) -> bool:
        """Set the transaction types form the raw transaction data.

        Returns:
            Whether the transaction type was set.
        """
        raw_transaction_type = self._transaction.get("type")
        if not raw_transaction_type:
            logger.warning(
                f"Transaction {self._transaction} has no valid type, skipping."
            )
            return False

        self.commish_action = raw_transaction_type == "commissioner"
        if self.commish_action:
            return self._set_transaction_types_commish_action()

        if raw_transaction_type == "trade":
            self.transaction_types.add(TransactionType.TRADE)
            return True

        if self._transaction.get("adds"):
            self.transaction_types.add(TransactionType.ADD)
        if self._transaction.get("drops"):
            self.transaction_types.add(TransactionType.DROP)

        if not self.transaction_types:
            logger.warning(
                f"Transaction {self._transaction} has no valid type, skipping."
            )
            return False

        return True

    def _set_gained(self) -> None:
        """Set the gained players."""
        if not self._input_adds:
            return

        for player_id, roster_id in self._input_adds.items():
            player = Player(player_id)
            manager = self._roster_id_map[roster_id]

            self.gained.setdefault(manager, set()).add(player)

    def _set_lost(self) -> None:
        """Set the lost players."""
        if not self._input_drops:
            return

        for player_id, roster_id in self._input_drops.items():
            player = Player(player_id)
            manager = self._roster_id_map[roster_id]

            self.lost.setdefault(manager, set()).add(player)

    def _set_draft_picks(self) -> None:
        """Set the draft picks.

        Example:
        >>> draft_pick = {
        ...     "season": "2019", # the season this draft pick belongs to
        ...     "round": 5,      # which round this draft pick is
        ...     "roster_id": 1,  # original owner's roster_id
        ...     "previous_owner_id": 1,  # previous owner's roster id (in this trade)
        ...     "owner_id": 2,   # the new owner of this pick after the trade
        ... }
        """  # noqa: E501
        # TODO: change to draft pick object when draft picks are implemented
        if not self._input_draft_picks:
            return

        required = {"round", "roster_id", "previous_owner_id", "owner_id"}
        for draft_pick in self._input_draft_picks:
            if not required.issubset(draft_pick):
                logger.warning(
                    f"Draft pick {draft_pick} missing "
                    f"required fields, skipping."
                )
                continue
            round_num = draft_pick["round"]
            origin_manager_roster_id = draft_pick["roster_id"]
            gained_manager_roster_id = draft_pick["owner_id"]
            lost_manager_roster_id = draft_pick["previous_owner_id"]

            origin_manager = self._roster_id_map[origin_manager_roster_id]

            gained_manager = self._roster_id_map[gained_manager_roster_id]
            lost_manager = self._roster_id_map[lost_manager_roster_id]

            player = Player(
                f"{origin_manager.real_name}'s {self.year} "
                f"Round {round_num} Draft Pick"
            )

            self.gained.setdefault(gained_manager, set()).add(player)
            self.lost.setdefault(lost_manager, set()).add(player)

    def _set_faab(self) -> None:
        """Set the FAAB spent."""
        if TransactionType.ADD in self.transaction_types:
            self._set_faab_add()
        elif TransactionType.TRADE in self.transaction_types:
            self._set_faab_trade()

    def _set_faab_add(self) -> None:
        """Set the FAAB spent for an add transaction."""
        faab_details = self._transaction.get("settings")
        if not faab_details or "waiver_bid" not in faab_details:
            return
        self.faab_spent = faab_details["waiver_bid"]

    def _set_faab_trade(self) -> None:
        """Set the FAAB spent for a trade."""
        faab_details = self._transaction.get("waiver_budget")
        if not faab_details:
            return

        gained_manager_faab_map: dict[Manager, list[int]] = {}
        lost_manager_faab_map: dict[Manager, list[int]] = {}

        for budget_entry in self._transaction["waiver_budget"]:
            if "amount" not in budget_entry:
                continue

            gained_manager_roster_id = budget_entry["receiver"]
            lost_manager_roster_id = budget_entry["sender"]

            gained_manager = self._roster_id_map[gained_manager_roster_id]
            lost_manager = self._roster_id_map[lost_manager_roster_id]

            # Consolidate FAABs for managers
            (
                gained_manager_faab_map
                .setdefault(gained_manager, [])
                .append(budget_entry['amount'])
            )
            (
                lost_manager_faab_map
                .setdefault(lost_manager, [])
                .append(budget_entry['amount'])
            )

        # Instead of having individual faab for
        # each manager, consolidate them to a single sum.
        self._consolidate_faab(gained_manager_faab_map, lost_manager_faab_map)

    def _consolidate_faab(
        self,
        gained_manager_faab_map: dict[Manager, list[int]],
        lost_manager_faab_map: dict[Manager, list[int]],
    ) -> None:
        """Consolidate FAABs for managers.

        Args:
            gained_manager_faab_map: Dict mapping managers gaining FAAB and
                their amounts.
            lost_manager_faab_map: Dict mapping managers losing FAAB and
                their amounts.
        """
        for mgr, faabs in gained_manager_faab_map.items():
            player = Player(f"${sum(faabs)} FAAB")

            self.gained.setdefault(mgr, set()).add(player)

        for mgr, faabs in lost_manager_faab_map.items():
            player = Player(f"${sum(faabs)} FAAB")

            self.lost.setdefault(mgr, set()).add(player)

    def _set_transaction_types_commish_action(self) -> bool:
        """Handle commissioner forced transactions.

        Returns:
            Whether the transaction was processed.
        """
        adds = self._transaction.get("adds", {})
        drops = self._transaction.get("drops", {})

        if not adds and not drops:
            logger.warning(
                f"Transaction {self._transaction} has no valid type, skipping."
            )
            return False
        elif adds and not drops:
            self.transaction_types.add(TransactionType.ADD)
        elif drops and not adds:
            self.transaction_types.add(TransactionType.DROP)
        elif len(adds) == 1 and len(drops) == 1:
            self.transaction_types = {
                TransactionType.ADD, TransactionType.DROP
            }
        else:
            # If there are multiple adds or drops, it's a trade
            self.transaction_types.add(TransactionType.TRADE)

        return True
