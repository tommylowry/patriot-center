"""
Unit tests for templates module.

Tests template initialization with both good and bad scenarios.
"""
from copy import deepcopy
from unittest.mock import patch

import pytest

from patriot_center_backend.managers.templates import (
    faab_template,
    initialize_faab_template,
    initialize_summary_templates,
)


class TestFaabTemplate:
    """Test faab_template constant."""

    def test_faab_template_structure(self):
        """Test that faab_template has correct structure."""
        assert "total_lost_or_gained" in faab_template
        assert "players" in faab_template
        assert "traded_away" in faab_template
        assert "acquired_from" in faab_template

    def test_faab_template_initial_values(self):
        """Test that faab_template has correct initial values."""
        assert faab_template["total_lost_or_gained"] == 0
        assert faab_template["players"] == {}
        assert faab_template["traded_away"]["total"] == 0
        assert faab_template["acquired_from"]["total"] == 0

    def test_faab_template_immutability(self):
        """Test that modifying copy doesn't affect original."""
        copy = deepcopy(faab_template)
        copy["total_lost_or_gained"] = 100

        assert faab_template["total_lost_or_gained"] == 0


class TestInitializeFaabTemplate:
    """Test initialize_faab_template function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.managers.templates.CACHE_MANAGER.get_manager_cache') as mock_get_manager_cache:
            
            self.mock_manager_cache = {}
            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = self.mock_manager_cache
            
            yield

    def test_initialize_all_levels(self):
        """Test initializing FAAB template at all cache levels."""
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "transactions": {}
                },
                "years": {
                    "2023": {
                        "summary": {
                            "transactions": {}
                        },
                        "weeks": {
                            "1": {
                                "transactions": {}
                            }
                        }
                    }
                }
            }
        })

        manager = "Manager 1"
        year = "2023"
        week = "1"
        
        initialize_faab_template(manager, year, week)

        # Top-level summary
        assert "faab" in self.mock_manager_cache[manager]["summary"]["transactions"]
        assert self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["total_lost_or_gained"] == 0

        # Yearly summary
        assert "faab" in self.mock_manager_cache[manager]["years"][year]["summary"]["transactions"]
        assert self.mock_manager_cache[manager]["years"][year]["summary"]["transactions"]["faab"]["total_lost_or_gained"] == 0

        # Weekly summary
        assert "faab" in self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]
        assert "transaction_ids" in self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["faab"]
        assert self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["faab"]["transaction_ids"] == []

    def test_skip_existing_top_level_faab(self):
        """Test that existing top-level FAAB is not overwritten."""
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "transactions": {
                        "faab": {
                            "total_lost_or_gained": 50,
                            "players": {"Player A": {"num_bids_won": 1, "total_faab_spent": 25}}
                        }
                    }
                },
                "years": {
                    "2023": {
                        "summary": {
                            "transactions": {}
                        },
                        "weeks": {
                            "1": {
                                "transactions": {}
                            }
                        }
                    }
                }
            }
        })

        manager = "Manager 1"
        year = "2023"
        week = "1"

        initialize_faab_template(manager, year, week)

        # Existing FAAB should be preserved
        assert self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["total_lost_or_gained"] == 50
        assert "Player A" in self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]["players"]

    def test_skip_existing_yearly_faab(self):
        """Test that existing yearly FAAB is not overwritten."""
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "transactions": {}
                },
                "years": {
                    "2023": {
                        "summary": {
                            "transactions": {
                                "faab": {
                                    "total_lost_or_gained": 30,
                                    "players": {}
                                }
                            }
                        },
                        "weeks": {
                            "1": {
                                "transactions": {}
                            }
                        }
                    }
                }
            }
        })

        manager = "Manager 1"
        year = "2023"
        week = "1"

        initialize_faab_template(manager, year, week)

        # Existing yearly FAAB should be preserved
        assert self.mock_manager_cache[manager]["years"][year]["summary"]["transactions"]["faab"]["total_lost_or_gained"] == 30

    def test_skip_existing_weekly_faab(self):
        """Test that existing weekly FAAB is not overwritten."""
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "transactions": {}
                },
                "years": {
                    "2023": {
                        "summary": {
                            "transactions": {}
                        },
                        "weeks": {
                            "1": {
                                "transactions": {
                                    "faab": {
                                        "total_lost_or_gained": 20,
                                        "transaction_ids": ["trans1", "trans2"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        })

        manager = "Manager 1"
        year = "2023"
        week = "1"
        
        initialize_faab_template(manager, year, week)

        # Existing weekly FAAB should be preserved
        assert self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["faab"]["total_lost_or_gained"] == 20
        assert len(self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["faab"]["transaction_ids"]) == 2

    def test_weekly_template_has_transaction_ids(self):
        """Test that weekly FAAB template includes transaction_ids."""
        self.mock_manager_cache.update({
            "Manager 1": {
                "summary": {
                    "transactions": {}
                },
                "years": {
                    "2023": {
                        "summary": {
                            "transactions": {}
                        },
                        "weeks": {
                            "1": {
                                "transactions": {}
                            }
                        }
                    }
                }
            }
        })
        
        manager = "Manager 1"
        year = "2023"
        week = "1"

        initialize_faab_template(manager, year, week)

        # Weekly should have transaction_ids, but top-level and yearly should not
        assert "transaction_ids" in self.mock_manager_cache[manager]["years"][year]["weeks"][week]["transactions"]["faab"]
        assert "transaction_ids" not in self.mock_manager_cache[manager]["summary"]["transactions"]["faab"]
        assert "transaction_ids" not in self.mock_manager_cache[manager]["years"][year]["summary"]["transactions"]["faab"]


class TestInitializeSummaryTemplates:
    """Test initialize_summary_templates function."""

    def test_with_faab_enabled(self):
        """Test template initialization with FAAB enabled."""
        templates = initialize_summary_templates(use_faab=True)

        assert "yearly_summary_template" in templates
        assert "weekly_summary_template" in templates
        assert "weekly_summary_not_in_playoffs_template" in templates
        assert "top_level_summary_template" in templates

        # Check that FAAB is present
        assert "faab" in templates["yearly_summary_template"]["transactions"]
        assert "faab" in templates["weekly_summary_template"]["transactions"]
        assert "faab" in templates["weekly_summary_not_in_playoffs_template"]["transactions"]
        assert "faab" in templates["top_level_summary_template"]["transactions"]

        # Weekly FAAB should have transaction_ids
        assert "transaction_ids" in templates["weekly_summary_template"]["transactions"]["faab"]

    def test_with_faab_disabled(self):
        """Test template initialization with FAAB disabled."""
        templates = initialize_summary_templates(use_faab=False)

        # Check that FAAB is not present
        assert "faab" not in templates["yearly_summary_template"]["transactions"]
        assert "faab" not in templates["weekly_summary_template"]["transactions"]
        assert "faab" not in templates["weekly_summary_not_in_playoffs_template"]["transactions"]
        assert "faab" not in templates["top_level_summary_template"]["transactions"]

    def test_yearly_summary_structure(self):
        """Test yearly summary template structure."""
        templates = initialize_summary_templates(use_faab=True)
        yearly = templates["yearly_summary_template"]

        # Matchup data
        assert "matchup_data" in yearly
        assert "overall" in yearly["matchup_data"]
        assert "regular_season" in yearly["matchup_data"]
        assert "playoffs" in yearly["matchup_data"]

        # Each matchup section should have proper fields
        for section in ["overall", "regular_season", "playoffs"]:
            assert "points_for" in yearly["matchup_data"][section]
            assert "points_against" in yearly["matchup_data"][section]
            assert "total_matchups" in yearly["matchup_data"][section]
            assert "wins" in yearly["matchup_data"][section]
            assert "losses" in yearly["matchup_data"][section]
            assert "ties" in yearly["matchup_data"][section]

        # Transactions
        assert "transactions" in yearly
        assert "trades" in yearly["transactions"]
        assert "adds" in yearly["transactions"]
        assert "drops" in yearly["transactions"]

    def test_weekly_summary_structure(self):
        """Test weekly summary template structure."""
        templates = initialize_summary_templates(use_faab=True)
        weekly = templates["weekly_summary_template"]

        # Matchup data
        assert "matchup_data" in weekly
        assert weekly["matchup_data"]["opponent_manager"] is None
        assert weekly["matchup_data"]["result"] is None
        assert weekly["matchup_data"]["points_for"] == 0.0
        assert weekly["matchup_data"]["points_against"] == 0.0

        # Transactions with transaction_ids
        assert "transaction_ids" in weekly["transactions"]["trades"]
        assert "transaction_ids" in weekly["transactions"]["adds"]
        assert "transaction_ids" in weekly["transactions"]["drops"]

    def test_weekly_not_in_playoffs_structure(self):
        """Test weekly not-in-playoffs template structure."""
        templates = initialize_summary_templates(use_faab=True)
        weekly_not_playoffs = templates["weekly_summary_not_in_playoffs_template"]

        # Should have empty matchup data
        assert "matchup_data" in weekly_not_playoffs
        assert weekly_not_playoffs["matchup_data"] == {}

        # But still have transaction tracking
        assert "transactions" in weekly_not_playoffs
        assert "transaction_ids" in weekly_not_playoffs["transactions"]["trades"]

    def test_top_level_summary_structure(self):
        """Test top-level summary template structure."""
        templates = initialize_summary_templates(use_faab=True)
        top_level = templates["top_level_summary_template"]

        # Should have same structure as yearly plus overall_data
        assert "matchup_data" in top_level
        assert "transactions" in top_level
        assert "overall_data" in top_level

        # Overall data structure
        assert "placement" in top_level["overall_data"]
        assert "playoff_appearances" in top_level["overall_data"]
        assert isinstance(top_level["overall_data"]["placement"], dict)
        assert isinstance(top_level["overall_data"]["playoff_appearances"], list)

    def test_matchup_data_initial_values(self):
        """Test that matchup data has correct initial values."""
        templates = initialize_summary_templates(use_faab=False)
        yearly = templates["yearly_summary_template"]

        # Check integer fields
        assert yearly["matchup_data"]["overall"]["total_matchups"]["total"] == 0
        assert yearly["matchup_data"]["overall"]["wins"]["total"] == 0
        assert yearly["matchup_data"]["overall"]["losses"]["total"] == 0
        assert yearly["matchup_data"]["overall"]["ties"]["total"] == 0

        # Check float fields
        assert yearly["matchup_data"]["overall"]["points_for"]["total"] == 0.0
        assert yearly["matchup_data"]["overall"]["points_against"]["total"] == 0.0

        # Check opponent dicts are empty
        assert yearly["matchup_data"]["overall"]["wins"]["opponents"] == {}

    def test_transaction_data_initial_values(self):
        """Test that transaction data has correct initial values."""
        templates = initialize_summary_templates(use_faab=False)
        yearly = templates["yearly_summary_template"]

        assert yearly["transactions"]["trades"]["total"] == 0
        assert yearly["transactions"]["adds"]["total"] == 0
        assert yearly["transactions"]["drops"]["total"] == 0
        assert yearly["transactions"]["trades"]["trade_partners"] == {}
        assert yearly["transactions"]["adds"]["players"] == {}
        assert yearly["transactions"]["drops"]["players"] == {}

    def test_template_isolation(self):
        """Test that modifying one template doesn't affect others."""
        templates = initialize_summary_templates(use_faab=True)

        # Modify yearly template
        templates["yearly_summary_template"]["matchup_data"]["overall"]["wins"]["total"] = 100

        # Weekly should still be 0
        assert templates["weekly_summary_template"]["matchup_data"]["points_for"] == 0.0

        # Top-level should still be 0
        assert templates["top_level_summary_template"]["matchup_data"]["overall"]["wins"]["total"] == 0

    def test_nested_structure_isolation(self):
        """Test that nested structures are properly isolated."""
        templates = initialize_summary_templates(use_faab=True)

        # Modify regular_season wins
        templates["yearly_summary_template"]["matchup_data"]["regular_season"]["wins"]["total"] = 10

        # Playoffs and overall should still be 0
        assert templates["yearly_summary_template"]["matchup_data"]["playoffs"]["wins"]["total"] == 0
        assert templates["yearly_summary_template"]["matchup_data"]["overall"]["wins"]["total"] == 0

    def test_faab_structure_in_transactions(self):
        """Test FAAB structure when enabled."""
        templates = initialize_summary_templates(use_faab=True)
        faab = templates["yearly_summary_template"]["transactions"]["faab"]

        assert faab["total_lost_or_gained"] == 0
        assert faab["players"] == {}
        assert faab["traded_away"]["total"] == 0
        assert faab["traded_away"]["trade_partners"] == {}
        assert faab["acquired_from"]["total"] == 0
        assert faab["acquired_from"]["trade_partners"] == {}

    def test_transaction_ids_only_in_weekly(self):
        """Test that transaction_ids only appear in weekly templates."""
        templates = initialize_summary_templates(use_faab=True)

        # Weekly should have transaction_ids
        assert "transaction_ids" in templates["weekly_summary_template"]["transactions"]["trades"]
        assert "transaction_ids" in templates["weekly_summary_template"]["transactions"]["adds"]
        assert "transaction_ids" in templates["weekly_summary_template"]["transactions"]["drops"]
        assert "transaction_ids" in templates["weekly_summary_template"]["transactions"]["faab"]

        # Yearly should not have transaction_ids
        assert "transaction_ids" not in templates["yearly_summary_template"]["transactions"]["trades"]
        assert "transaction_ids" not in templates["yearly_summary_template"]["transactions"]["adds"]
        assert "transaction_ids" not in templates["yearly_summary_template"]["transactions"]["drops"]
        assert "transaction_ids" not in templates["yearly_summary_template"]["transactions"]["faab"]

        # Top-level should not have transaction_ids
        assert "transaction_ids" not in templates["top_level_summary_template"]["transactions"]["trades"]
