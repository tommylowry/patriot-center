"""Cache query helpers for reading transaction related manager metadata."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import TOMMY_USER_ID
from patriot_center_backend.models import Manager, Player, Transaction
from patriot_center_backend.models.transaction import TransactionType
from patriot_center_backend.utils.formatters import extract_dict_data


@dataclass
class Trades:
    """Trades class."""
    total: int = 0
    top_trade_partners: dict[Manager, int] = field(default_factory=dict)
    most_acquired_players: dict[Player, int] = field(default_factory=dict)
    most_sent_players: dict[Player, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the trades to a dictionary.

        Returns:
            The trades as a dictionary.
        """
        return {
            "total": self.total,
            "top_trade_partners": extract_dict_data(
                {
                    str(m): self.top_trade_partners[m]
                    for m in self.top_trade_partners
                },
                Manager,
            ),
            "most_acquired_players": extract_dict_data(
                {
                    str(p): self.most_acquired_players[p]
                    for p in self.most_acquired_players
                },
                Player,
                cutoff=0,
            ),
            "most_sent_players": extract_dict_data(
                {
                    str(p): self.most_sent_players[p]
                    for p in self.most_sent_players
                },
                Player,
                cutoff=0,
            ),
        }

    def add_partners(self, partners: set[Manager]) -> None:
        """Add trade partners to the trades.

        Args:
            partners: The partners to add.
        """
        for partner in partners:
            if partner in self.top_trade_partners:
                self.top_trade_partners[partner] += 1
            else:
                self.top_trade_partners[partner] = 1

    def add_acquired_players(self, players: set[Player]) -> None:
        """Add an acquired player to the trades.

        Args:
            players: The players to add.
        """
        for player in players:
            if player in self.most_acquired_players:
                self.most_acquired_players[player] += 1
            else:
                self.most_acquired_players[player] = 1

    def add_sent_players(self, players: set[Player]) -> None:
        """Add a sent player to the trades.

        Args:
            players: The player to add.
        """
        for player in players:
            if player in self.most_sent_players:
                self.most_sent_players[player] += 1
            else:
                self.most_sent_players[player] = 1

@dataclass
class Adds:
    """Adds class."""
    total: int = 0
    top_players_added: dict[Player, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the adds to a dictionary.

        Returns:
            The adds as a dictionary.
        """
        return {
            "total": self.total,
            "top_players_added": self.top_players_added,
        }

    def add_players(self, players: set[Player]) -> None:
        """Add a player to the adds.

        Args:
            players: The player to add.
        """
        for player in players:
            if player in self.top_players_added:
                self.top_players_added[player] += 1
            else:
                self.top_players_added[player] = 1

@dataclass
class Drops:
    """Drops class."""
    total: int = 0
    top_players_dropped: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the drops to a dictionary.

        Returns:
            The drops as a dictionary.
        """
        return {
            "total": self.total,
            "top_players_dropped": self.top_players_dropped,
        }

@dataclass
class Faab:
    """Faab class."""
    total_spent: int = 0
    biggest_acquisitions: list[dict[str, Any]] = field(default_factory=list)
    faab_traded: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the faab to a dictionary.

        Returns:
            The faab as a dictionary.
        """
        return {
            "total_spent": self.total_spent,
            "biggest_acquisitions": self.biggest_acquisitions,
            "faab_traded": self.faab_traded,
        }

@dataclass
class ObjectCount:
    """Object count class."""
    object: Manager | Player
    count: int = 0



def get_transaction_details_from_cache(  # this is next
    manager_obj: Manager, year: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get comprehensive transaction summary with formatted data and image URLs.

    Extracts and formats trades, adds, drops, and FAAB spending including:
    - Trade partners and most acquired/sent players
    - Top added/dropped players
    - FAAB spending and trading

    All player/manager names enriched with image URLs.

    Args:
        manager_obj: Manager object
        year: Season year (optional - defaults to all-time stats)

    Returns:
        Dictionary with trades, adds, drops, and faab summaries
    """
    manager = manager_obj.real_name  # TODO: use manager object

    main_manager_cache = CACHE_MANAGER.get_manager_metadata_cache()
    manager_data = deepcopy(main_manager_cache[manager])

    transaction_summary = {"trades": {}, "adds": {}, "drops": {}, "faab": {}}

    # Get all-time stats by default, or single season stats if year specified
    trans_cache = manager_data["summary"]["transactions"]
    if year:
        trans_cache = manager_data["years"][year]["summary"]["transactions"]

    # Flatten FAAB player data to just total spent (if FAAB exists)
    if "faab" in trans_cache:
        players = trans_cache["faab"]["players"]
        for player in list(players):
            players[player] = players[player]["total_faab_spent"]

    trades = {
        "total": trans_cache["trades"]["total"],
        "top_trade_partners": extract_dict_data(
            deepcopy(trans_cache["trades"]["trade_partners"]), Manager
        ),
    }

    # ---- Trades Summary ----
    # Most Aquired Players
    trade_players_acquired = trans_cache["trades"]["trade_players_acquired"]
    most_acquired_players = extract_dict_data(
        deepcopy(trade_players_acquired), Player
    )
    for player in most_acquired_players:
        player_details = deepcopy(trade_players_acquired[player["name"]])
        player["from"] = extract_dict_data(
            deepcopy(player_details.get("trade_partners", {})),
            Manager,
            cutoff=0,
        )
    trades["most_acquired_players"] = most_acquired_players

    # Most Sent Players
    trade_players_sent = trans_cache["trades"]["trade_players_sent"]
    most_sent_players = extract_dict_data(deepcopy(trade_players_sent), Player)
    for player in most_sent_players:
        player_details = deepcopy(trade_players_sent.get(player["name"], {}))
        player["to"] = extract_dict_data(
            player_details.get("trade_partners", {}), Manager, cutoff=0
        )
    trades["most_sent_players"] = most_sent_players

    transaction_summary["trades"] = trades

    # ---- Adds Summary ----
    adds = {
        "total": trans_cache["adds"]["total"],
        "top_players_added": extract_dict_data(
            deepcopy(trans_cache["adds"]["players"]), Player
        ),
    }
    transaction_summary["adds"] = adds

    # ---- Drops Summary ----
    drops = {
        "total": trans_cache["drops"]["total"],
        "top_players_dropped": extract_dict_data(
            deepcopy(trans_cache["drops"]["players"]), Player
        ),
    }
    transaction_summary["drops"] = drops

    # ---- FAAB Summary ----
    # Handle cases where FAAB doesn't exist
    # (e.g., older years before FAAB was implemented)
    if trans_cache.get("faab"):
        faab = {
            "total_spent": abs(trans_cache["faab"]["total_lost_or_gained"]),
            "biggest_acquisitions": extract_dict_data(
                deepcopy(trans_cache["faab"]["players"]),
                Player,
                value_name="amount",
            ),
        }

        # FAAB Traded
        sent = trans_cache["faab"]["traded_away"]["total"]
        received = trans_cache["faab"]["acquired_from"]["total"]
        net = received - sent
        faab["faab_traded"] = {"sent": sent, "received": received, "net": net}
    else:
        # FAAB not available for this year/manager
        faab = {
            "total_spent": 0,
            "biggest_acquisitions": [],
            "faab_traded": {"sent": 0, "received": 0, "net": 0},
        }
    transaction_summary["faab"] = faab

    # Return final transaction summary
    return deepcopy(transaction_summary)


def new_get_transaction_details_from_cache(
    manager: Manager, year: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get comprehensive transaction summary.

    Extracts and formats trades, adds, drops, and FAAB spending including:
    - Trade partners and most acquired/sent players
    - Top added/dropped players
    - FAAB spending and trading

    All player/manager names enriched with image URLs.

    Args:
        manager_obj: Manager object
        year: Season year (optional - defaults to all-time stats)

    Returns:
        Dictionary with trades, adds, drops, and faab summaries
    """
    transactions = Transaction.get_transactions(
        manager_involved=manager, year=year
    )

    trades = Trades()
    adds = Adds()
    drops = Drops()
    faab = Faab()

    for transaction in transactions:
        if TransactionType.TRADE in transaction.transaction_types:
            _scrape_trade_info(transaction, manager, trades)




def get_trade_history_between_two_managers(
    manager1: Manager,
    manager2: Manager,
    year: str | None = None,
) -> list[dict[str, Any]]:
    """Get complete trade history between two managers.

    Finds all trades involving both managers and returns formatted trade cards.

    Args:
        manager1: First manager
        manager2: Second manager
        year: Season year (optional - defaults to all-time if None)

    Returns:
        List of trade cards in reverse chronological order (newest first)
    """
    transactions = Transaction.get_transactions(
        managers_involved=[manager1, manager2], year=year
    )

    return [t.to_dict() for t in transactions]

def _scrape_trade_info(trade: Transaction, manager: Manager, trades: Trades) -> None:
    """Scrape trade info from transaction object.

    Args:
        trade: Transaction object
        manager: Manager object
        year: Season year
        trades: Trades object
    """
    trades.total += 1

    if trade.gained.get(manager):
        trades.most_acquired_players.append(
            deepcopy(trade.gained.get(manager).pop())
        )
    if trade.lost.get(manager):
        trades.most_sent_players.append(
            deepcopy(trade.lost.get(manager).pop())
        )

get_transaction_details_from_cache(Manager(TOMMY_USER_ID))