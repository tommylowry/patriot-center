import pytest


@pytest.fixture
def mock_manager_cache():
    """Create a sample cache for testing."""
    return {
        "Manager 1": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 10, "opponents": {"Manager 2": 7, "Manager 3": 3}},
                        "losses": {"total": 5, "opponents": {"Manager 2": 3, "Manager 3": 2}},
                        "ties": {"total": 1, "opponents": {"Manager 2": 1}},
                        "points_for": {"total": 1500.50, "opponents": {"Manager 2": 1000.00, "Manager 3": 500.50}},
                        "points_against": {"total": 1400.25, "opponents": {"Manager 2": 900.00, "Manager 3": 500.25}}
                    },
                    "regular_season": {
                        "wins": {"total": 8, "opponents": {}},
                        "losses": {"total": 4, "opponents": {}},
                        "ties": {"total": 1, "opponents": {}},
                        "points_for": {"total": 1300.00, "opponents": {}},
                        "points_against": {"total": 1200.00, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 2, "opponents": {}},
                        "losses": {"total": 1, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 200.50, "opponents": {}},
                        "points_against": {"total": 200.25, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 5,
                        "trade_partners": {"Manager 2": 3, "Manager 3": 2},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 10, "players": {}},
                    "drops": {"total": 10, "players": {}}
                },
                "overall_data": {
                    "placement": {"2023": 1, "2022": 3},
                    "playoff_appearances": ["2023", "2022"]
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 6, "opponents": {}},
                                "losses": {"total": 2, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 800.00, "opponents": {}},
                                "points_against": {"total": 700.00, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 5, "opponents": {}},
                                "losses": {"total": 2, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 700.00, "opponents": {}},
                                "points_against": {"total": 600.00, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 1, "opponents": {}},
                                "losses": {"total": 0, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 100.00, "opponents": {}},
                                "points_against": {"total": 100.00, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {
                                "total": 2,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {}
                            },
                            "adds": {"total": 5, "players": {}},
                            "drops": {"total": 5, "players": {}}
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Manager 2",
                                "result": "win",
                                "points_for": 120.5,
                                "points_against": 100.0
                            }
                        }
                    }
                }
            }
        },
        "Manager 2": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 5, "opponents": {"Manager 1": 3}},
                        "losses": {"total": 10, "opponents": {"Manager 1": 7}},
                        "ties": {"total": 1, "opponents": {"Manager 1": 1}},
                        "points_for": {"total": 1400.25, "opponents": {"Manager 1": 900.00}},
                        "points_against": {"total": 1500.50, "opponents": {"Manager 1": 1000.00}}
                    },
                    "regular_season": {
                        "wins": {"total": 4, "opponents": {}},
                        "losses": {"total": 8, "opponents": {}},
                        "ties": {"total": 1, "opponents": {}},
                        "points_for": {"total": 1200.00, "opponents": {}},
                        "points_against": {"total": 1300.00, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 1, "opponents": {}},
                        "losses": {"total": 2, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 200.25, "opponents": {}},
                        "points_against": {"total": 200.50, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 3,
                        "trade_partners": {"Manager 1": 3},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 8, "players": {}},
                    "drops": {"total": 8, "players": {}}
                },
                "overall_data": {
                    "placement": {"2023": 5, "2022": 7},
                    "playoff_appearances": ["2023", "2022"]
                }
            },
            "years": {
                "2023": {
                    "summary": {
                        "matchup_data": {
                            "overall": {
                                "wins": {"total": 2, "opponents": {}},
                                "losses": {"total": 6, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 700.00, "opponents": {}},
                                "points_against": {"total": 800.00, "opponents": {}}
                            },
                            "regular_season": {
                                "wins": {"total": 2, "opponents": {}},
                                "losses": {"total": 5, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 600.00, "opponents": {}},
                                "points_against": {"total": 700.00, "opponents": {}}
                            },
                            "playoffs": {
                                "wins": {"total": 0, "opponents": {}},
                                "losses": {"total": 1, "opponents": {}},
                                "ties": {"total": 0, "opponents": {}},
                                "points_for": {"total": 100.00, "opponents": {}},
                                "points_against": {"total": 100.00, "opponents": {}}
                            }
                        },
                        "transactions": {
                            "trades": {
                                "total": 1,
                                "trade_partners": {},
                                "trade_players_acquired": {},
                                "trade_players_sent": {}
                            },
                            "adds": {"total": 3, "players": {}},
                            "drops": {"total": 3, "players": {}}
                        }
                    },
                    "weeks": {
                        "1": {
                            "matchup_data": {
                                "opponent_manager": "Manager 1",
                                "result": "loss",
                                "points_for": 100.0,
                                "points_against": 120.5
                            }
                        }
                    }
                }
            }
        },
        "Manager 3": {
            "summary": {
                "matchup_data": {
                    "overall": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    },
                    "regular_season": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    },
                    "playoffs": {
                        "wins": {"total": 0, "opponents": {}},
                        "losses": {"total": 0, "opponents": {}},
                        "ties": {"total": 0, "opponents": {}},
                        "points_for": {"total": 0.0, "opponents": {}},
                        "points_against": {"total": 0.0, "opponents": {}}
                    }
                },
                "transactions": {
                    "trades": {
                        "total": 2,
                        "trade_partners": {"Manager 1": 2},
                        "trade_players_acquired": {},
                        "trade_players_sent": {}
                    },
                    "adds": {"total": 0, "players": {}},
                    "drops": {"total": 0, "players": {}}
                },
                "overall_data": {
                    "placement": {},
                    "playoff_appearances": []
                }
            },
            "years": {}
        }
    }