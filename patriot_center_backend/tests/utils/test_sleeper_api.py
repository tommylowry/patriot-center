"""Unit tests for sleeper_api module."""

from unittest.mock import MagicMock, patch

import pytest

from patriot_center_backend.utils.sleeper_api import SleeperApiClient

MODULE_PATH = "patriot_center_backend.utils.sleeper_api"


class TestSleeperApiClientFetch:
    """Test SleeperApiClient.fetch method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `requests.get`: `mock_requests_get`

        Yields:
            None
        """
        with patch(f"{MODULE_PATH}.requests.get") as mock_requests_get:
            self.mock_requests_get = mock_requests_get
            self.mock_response = MagicMock()
            self.mock_response.status_code = 200
            self.mock_response.json.return_value = {"data": "value"}
            self.mock_requests_get.return_value = self.mock_response

            self.client = SleeperApiClient()

            yield

    def test_returns_parsed_json(self):
        """Test returns parsed JSON from API."""
        result = self.client.fetch("league/123")

        assert result == {"data": "value"}

    def test_calls_correct_url(self):
        """Test calls the correct Sleeper API URL."""
        self.client.fetch("league/123/rosters")

        self.mock_requests_get.assert_called_once_with(
            "https://api.sleeper.app/v1/league/123/rosters"
        )

    def test_raises_on_non_200_status(self):
        """Test raises ConnectionAbortedError on non-200 status."""
        self.mock_response.status_code = 500

        with pytest.raises(ConnectionAbortedError, match="Failed to fetch"):
            self.client.fetch("league/123")

    def test_caches_response(self):
        """Test second call returns cached response without HTTP request."""
        self.client.fetch("league/123")
        self.client.fetch("league/123")

        self.mock_requests_get.assert_called_once()

    def test_different_endpoints_not_cached_together(self):
        """Test different endpoints make separate HTTP requests."""
        self.client.fetch("league/123")
        self.client.fetch("league/456")

        assert self.mock_requests_get.call_count == 2

    def test_bypass_cache_makes_new_request(self):
        """Test bypass_cache=True makes a new HTTP request."""
        self.client.fetch("league/123")
        self.client.fetch("league/123", bypass_cache=True)

        assert self.mock_requests_get.call_count == 2

    def test_bypass_cache_updates_cached_value(self):
        """Test bypass_cache=True updates the cached value."""
        self.client.fetch("league/123")

        self.mock_response.json.return_value = {"data": "updated"}
        result = self.client.fetch("league/123", bypass_cache=True)

        assert result == {"data": "updated"}

        # Subsequent non-bypass call returns updated value
        result_cached = self.client.fetch("league/123")
        assert result_cached == {"data": "updated"}


class TestSleeperApiClientClearCache:
    """Test SleeperApiClient.clear_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `requests.get`: `mock_requests_get`

        Yields:
            None
        """
        with patch(f"{MODULE_PATH}.requests.get") as mock_requests_get:
            self.mock_requests_get = mock_requests_get
            self.mock_response = MagicMock()
            self.mock_response.status_code = 200
            self.mock_response.json.return_value = {"data": "value"}
            self.mock_requests_get.return_value = self.mock_response

            self.client = SleeperApiClient()

            yield

    def test_clear_cache_forces_new_request(self):
        """Test clearing cache causes next fetch to make HTTP request."""
        self.client.fetch("league/123")
        self.client.clear_cache()
        self.client.fetch("league/123")

        assert self.mock_requests_get.call_count == 2

    def test_clear_cache_empties_internal_cache(self):
        """Test clearing cache empties the internal cache dict."""
        self.client.fetch("league/123")
        self.client.clear_cache()

        assert self.client._cache == {}


class TestGetSleeperClient:
    """Test get_sleeper_client singleton function."""

    def test_returns_sleeper_api_client_instance(self):
        """Test returns a SleeperApiClient instance."""
        with patch(f"{MODULE_PATH}._client_instance", None):
            from patriot_center_backend.utils.sleeper_api import (
                get_sleeper_client,
            )

            client = get_sleeper_client()

            assert isinstance(client, SleeperApiClient)

    def test_returns_same_instance(self):
        """Test returns same instance on repeated calls."""
        from patriot_center_backend.utils.sleeper_api import (
            get_sleeper_client,
        )

        client1 = get_sleeper_client()
        client2 = get_sleeper_client()

        assert client1 is client2
