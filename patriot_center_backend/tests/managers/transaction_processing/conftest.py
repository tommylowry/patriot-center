"""This module contains fixtures for testing the transaction processing."""

import pytest


@pytest.fixture
def mock_manager_cache():
    """Create a sample manager cache for testing.

    Returns:
        Sample manager cache
    """
    return {
        "Tommy": {
            "summary": {
                "transactions": {
                    "trades": {
                        "total": 0,
                        "trade_partners": {},
                        "trade_players_acquired": {},
                        "trade_players_sent": {},
                        "transaction_ids": [],
                    },
                    "adds": {"total": 0, "players": {}, "transaction_ids": []},
                    "drops": {"total": 0, "players": {}, "transaction_ids": []},
                    "faab": {
                        "total_lost_or_gained": 0,
                        "players": {},
                        "acquired_from": {"total": 0, "trade_partners": {}},
                        "traded_away": {"total": 0, "trade_partners": {}},
                        "transaction_ids": [],
                    },
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "transactions": {
                            "trades": {
                                "total": 0,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {},
                                "transaction_ids": [],
                            },
                            "adds": {
                                "total": 0,
                                "players": {},
                                "transaction_ids": [],
                            },
                            "drops": {
                                "total": 0,
                                "players": {},
                                "transaction_ids": [],
                            },
                            "faab": {
                                "total_lost_or_gained": 0,
                                "players": {},
                                "acquired_from": {
                                    "total": 0,
                                    "trade_partners": {},
                                },
                                "traded_away": {
                                    "total": 0,
                                    "trade_partners": {},
                                },
                                "transaction_ids": [],
                            },
                        }
                    },
                    "weeks": {
                        "1": {
                            "transactions": {
                                "trades": {
                                    "total": 0,
                                    "trade_partners": {},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": [],
                                },
                                "adds": {
                                    "total": 0,
                                    "players": {},
                                    "transaction_ids": [],
                                },
                                "drops": {
                                    "total": 0,
                                    "players": {},
                                    "transaction_ids": [],
                                },
                                "faab": {
                                    "total_lost_or_gained": 0,
                                    "players": {},
                                    "acquired_from": {
                                        "total": 0,
                                        "trade_partners": {},
                                    },
                                    "traded_away": {
                                        "total": 0,
                                        "trade_partners": {},
                                    },
                                    "transaction_ids": [],
                                },
                            }
                        }
                    },
                }
            },
        },
        "Jay": {
            "summary": {
                "transactions": {
                    "trades": {
                        "total": 0,
                        "trade_partners": {},
                        "trade_players_acquired": {},
                        "trade_players_sent": {},
                        "transaction_ids": [],
                    },
                    "adds": {"total": 0, "players": {}, "transaction_ids": []},
                    "drops": {"total": 0, "players": {}, "transaction_ids": []},
                    "faab": {
                        "total_lost_or_gained": 0,
                        "players": {},
                        "acquired_from": {"total": 0, "trade_partners": {}},
                        "traded_away": {"total": 0, "trade_partners": {}},
                        "transaction_ids": [],
                    },
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "transactions": {
                            "trades": {
                                "total": 0,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {},
                                "transaction_ids": [],
                            },
                            "adds": {
                                "total": 0,
                                "players": {},
                                "transaction_ids": [],
                            },
                            "drops": {
                                "total": 0,
                                "players": {},
                                "transaction_ids": [],
                            },
                            "faab": {
                                "total_lost_or_gained": 0,
                                "players": {},
                                "acquired_from": {
                                    "total": 0,
                                    "trade_partners": {},
                                },
                                "traded_away": {
                                    "total": 0,
                                    "trade_partners": {},
                                },
                                "transaction_ids": [],
                            },
                        }
                    },
                    "weeks": {
                        "1": {
                            "transactions": {
                                "trades": {
                                    "total": 0,
                                    "trade_partners": {},
                                    "trade_players_acquired": {},
                                    "trade_players_sent": {},
                                    "transaction_ids": [],
                                },
                                "adds": {
                                    "total": 0,
                                    "players": {},
                                    "transaction_ids": [],
                                },
                                "drops": {
                                    "total": 0,
                                    "players": {},
                                    "transaction_ids": [],
                                },
                                "faab": {
                                    "total_lost_or_gained": 0,
                                    "players": {},
                                    "acquired_from": {
                                        "total": 0,
                                        "trade_partners": {},
                                    },
                                    "traded_away": {
                                        "total": 0,
                                        "trade_partners": {},
                                    },
                                    "transaction_ids": [],
                                },
                            }
                        }
                    },
                }
            },
        },
    }
