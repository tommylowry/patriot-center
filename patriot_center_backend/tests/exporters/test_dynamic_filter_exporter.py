"""Unit tests for dynamic_filter_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.dynamic_filter_exporter import (
    get_dynamic_filter_options,
)

MODULE_PATH = "patriot_center_backend.exporters.dynamic_filter_exporter"


class TestGetDynamicFilterOptions:
    """Test get_dynamic_filter_options method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_dynamic_filter_options_from_cache`:
            `mock_get_dynamic_filter_options`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_dynamic_filter_options_from_cache"
            ) as mock_get_dynamic_filter_options,
        ):
            self.mock_get_dynamic_filter_options = (
                mock_get_dynamic_filter_options
            )
            self.mock_get_dynamic_filter_options.return_value = {
                "years": [],
                "weeks": [],
                "managers": [],
                "positions": [],
            }

            yield

    def test_get_dynamic_filter_options_no_filters(self):
        """Test getting filter options with no selections."""
        result = get_dynamic_filter_options(
            year=None,
            week=None,
            manager=None,
            position=None,
            player=None,
        )

        assert "years" in result
        assert "weeks" in result
        assert "managers" in result
        assert "positions" in result

    def test_get_dynamic_filter_options_with_year(self):
        """Test getting filter options with year selected."""
        self.mock_get_dynamic_filter_options.return_value = {
            "years": ["2023"],
            "weeks": ["1", "2", "3"],
            "managers": ["Tommy", "Benz"],
            "positions": ["QB", "RB"],
        }

        result = get_dynamic_filter_options(
            year="2023",
            week=None,
            manager=None,
            position=None,
            player=None,
        )

        assert result["years"] == ["2023"]
        assert len(result["weeks"]) == 3

    def test_get_dynamic_filter_options_with_all_params(self):
        """Test getting filter options with all params."""
        get_dynamic_filter_options(
            year="2023",
            week="1",
            manager="Tommy",
            position="QB",
            player="Jayden Daniels",
        )

        self.mock_get_dynamic_filter_options.assert_called_once_with(
            "2023", "1", "Tommy", "QB", "Jayden Daniels"
        )

    def test_get_dynamic_filter_options_propagates_value_error(self):
        """Test that ValueError from cache query propagates."""
        self.mock_get_dynamic_filter_options.side_effect = ValueError(
            "Invalid year"
        )

        with pytest.raises(ValueError, match="Invalid year"):
            get_dynamic_filter_options(
                year="9999",
                week=None,
                manager=None,
                position=None,
                player=None,
            )
