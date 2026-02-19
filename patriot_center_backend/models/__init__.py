"""Domains package for Patriot Center backend."""

from patriot_center_backend.models.manager import Manager
from patriot_center_backend.models.player import Player
from patriot_center_backend.models.transaction import Transaction


def load_all_models() -> None:
    """Load all models into the cache."""
    Manager.load_all_managers()
    Player.load_all_players()
    Transaction.load_all_transactions()

__all__ = ["Manager", "Player", "Transaction"]
