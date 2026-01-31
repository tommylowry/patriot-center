"""Unit tests for _base module."""

import logging

import pytest

from patriot_center_backend.cache.updaters._base import log_cache_update


class TestLogCacheUpdate:
    """Test log_cache_update function."""

    def test_logs_single_digit_week_with_padding(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test logs single digit week with extra space padding.

        Args:
            caplog: pytest caplog fixture
        """
        with caplog.at_level(logging.INFO):
            log_cache_update(2024, 1, "Replacement Score")

        assert "Season 2024, Week 1:  Replacement Score Cache Updated." in (
            caplog.text
        )

    def test_logs_double_digit_week_without_padding(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test logs double digit week without extra space padding.

        Args:
            caplog: pytest caplog fixture
        """
        with caplog.at_level(logging.INFO):
            log_cache_update(2024, 10, "Weekly Data")

        assert "Season 2024, Week 10: Weekly Data Cache Updated." in (
            caplog.text
        )

    def test_logs_week_18(self, caplog: pytest.LogCaptureFixture):
        """Test logs week 18 without extra space padding.

        Args:
            caplog: pytest caplog fixture
        """
        with caplog.at_level(logging.INFO):
            log_cache_update(2024, 18, "Replacement Score")

        assert "Season 2024, Week 18: Replacement Score Cache Updated." in (
            caplog.text
        )

    def test_logs_week_9_with_padding(self, caplog: pytest.LogCaptureFixture):
        """Test logs week 9 with extra space padding (boundary).

        Args:
            caplog: pytest caplog fixture
        """
        with caplog.at_level(logging.INFO):
            log_cache_update(2024, 9, "Weekly Data")

        assert "Season 2024, Week 9:  Weekly Data Cache Updated." in (
            caplog.text
        )
