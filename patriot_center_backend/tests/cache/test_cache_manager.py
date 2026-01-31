"""Unit tests for cache_manager module."""

import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.cache_manager import (
    CacheManager,
    get_cache_manager,
)


class TestLoadCache:
    """Test CacheManager._load_cache method."""

    def test_loads_existing_file(self, tmp_path):
        """Test loads JSON from existing file.

        Args:
            tmp_path: pytest tmp_path fixture
        """
        cache_file = tmp_path / "test_cache.json"
        cache_file.write_text(json.dumps({"key": "value"}))

        manager = CacheManager()
        result = manager._load_cache(str(cache_file))

        assert result == {"key": "value"}

    def test_returns_empty_dict_for_missing_file(self):
        """Test returns empty dict when file does not exist."""
        manager = CacheManager()
        result = manager._load_cache("/nonexistent/path/cache.json")

        assert result == {}


class TestSaveCache:
    """Test CacheManager._save_cache method."""

    def test_saves_json_to_file(self, tmp_path):
        """Test saves JSON to file with proper formatting.

        Args:
            tmp_path: pytest tmp_path fixture
        """
        cache_file = tmp_path / "test_cache.json"

        manager = CacheManager()
        manager._save_cache(str(cache_file), {"key": "value"})

        with open(cache_file) as f:
            result = json.load(f)

        assert result == {"key": "value"}

    def test_creates_parent_directories(self, tmp_path):
        """Test creates parent directories if they don't exist.

        Args:
            tmp_path: pytest tmp_path fixture
        """
        cache_file = tmp_path / "nested" / "dir" / "cache.json"

        manager = CacheManager()
        manager._save_cache(str(cache_file), {"nested": True})

        assert cache_file.exists()


class TestGetManagerCache:
    """Test CacheManager.get_manager_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"Tommy": {"summary": {}}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_manager_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"Tommy": {"summary": {}}}

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_manager_cache()
        self.manager.get_manager_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_manager_cache()
        self.manager.get_manager_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveManagerCache:
    """Test CacheManager.save_manager_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        data = {"Tommy": {"summary": {}}}

        self.manager.save_manager_cache(data)

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._manager_cache = {"Tommy": {"summary": {}}}

        self.manager.save_manager_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_manager_cache()

        assert "No manager cache data to save" in str(exc_info.value)


class TestIsCacheStale:
    """Test CacheManager.is_cache_stale method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup CacheManager instance.

        Yields:
            None
        """
        self.manager = CacheManager()

        yield

    def test_returns_true_when_file_missing(self):
        """Test returns True when cache file does not exist."""
        with patch(
            "patriot_center_backend.cache.cache_manager.module"
        ) as mock_module:
            mock_module._PLAYER_IDS_CACHE_FILE = "/nonexistent/file.json"

            result = self.manager.is_cache_stale("player_ids")

        assert result is True

    def test_returns_true_when_file_older_than_max_age(self, tmp_path):
        """Test returns True when file is older than max_age.

        Args:
            tmp_path: pytest tmp_path fixture
        """
        cache_file = tmp_path / "test.json"
        cache_file.write_text("{}")

        old_time = (datetime.now() - timedelta(weeks=2)).timestamp()
        os.utime(cache_file, (old_time, old_time))

        with patch(
            "patriot_center_backend.cache.cache_manager.module"
        ) as mock_module:
            mock_module._PLAYER_IDS_CACHE_FILE = str(cache_file)

            result = self.manager.is_cache_stale("player_ids")

        assert result is True

    def test_returns_false_when_file_recent(self, tmp_path):
        """Test returns False when file is newer than max_age.

        Args:
            tmp_path: pytest tmp_path fixture
        """
        cache_file = tmp_path / "test.json"
        cache_file.write_text("{}")

        with patch(
            "patriot_center_backend.cache.cache_manager.module"
        ) as mock_module:
            mock_module._PLAYER_IDS_CACHE_FILE = str(cache_file)

            result = self.manager.is_cache_stale("player_ids")

        assert result is False

    def test_raises_for_unknown_cache_name(self):
        """Test raises ValueError for unknown cache name."""
        with patch(
            "patriot_center_backend.cache.cache_manager.module"
        ) as mock_module:
            del mock_module._NONEXISTENT_CACHE_FILE

            with pytest.raises(ValueError) as exc_info:
                self.manager.is_cache_stale("nonexistent")

        assert "Unknown cache name" in str(exc_info.value)


class TestGetTransactionIdsCache:
    """Test CacheManager.get_transaction_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"tx_001": {"type": "trade"}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_transaction_ids_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"tx_001": {"type": "trade"}}

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_transaction_ids_cache()
        self.manager.get_transaction_ids_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_transaction_ids_cache()
        self.manager.get_transaction_ids_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveTransactionIdsCache:
    """Test CacheManager.save_transaction_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_transaction_ids_cache({"tx_001": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._transaction_ids_cache = {"tx_001": {}}

        self.manager.save_transaction_ids_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_transaction_ids_cache()

        assert "No transaction IDs cache data to save" in str(exc_info.value)


class TestGetPlayersCache:
    """Test CacheManager.get_players_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"Tommy": {"4046": "QB"}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_players_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"Tommy": {"4046": "QB"}}

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_players_cache()
        self.manager.get_players_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_players_cache()
        self.manager.get_players_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSavePlayersCache:
    """Test CacheManager.save_players_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_players_cache({"Tommy": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._players_cache = {"Tommy": {}}

        self.manager.save_players_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_players_cache()

        assert "No players cache data to save" in str(exc_info.value)


class TestGetPlayerIdsCache:
    """Test CacheManager.get_player_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "4046": {"full_name": "Patrick Mahomes"},
            }
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_player_ids_cache()

        self.mock_load_cache.assert_called_once()
        assert "4046" in result

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_player_ids_cache()
        self.manager.get_player_ids_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_player_ids_cache()
        self.manager.get_player_ids_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSavePlayerIdsCache:
    """Test CacheManager.save_player_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_player_ids_cache({"4046": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._player_ids_cache = {"4046": {}}

        self.manager.save_player_ids_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_player_ids_cache()

        assert "No player IDs cache data to save" in str(exc_info.value)


class TestGetStartersCache:
    """Test CacheManager.get_starters_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"1": {}}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_starters_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"2024": {"1": {}}}

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_starters_cache()
        self.manager.get_starters_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_starters_cache()
        self.manager.get_starters_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveStartersCache:
    """Test CacheManager.save_starters_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_starters_cache({"2024": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._starters_cache = {"2024": {}}

        self.manager.save_starters_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_starters_cache()

        assert "No starters cache data to save" in str(exc_info.value)


class TestGetPlayerDataCache:
    """Test CacheManager.get_player_data_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"1": {"QB": {}}}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_player_data_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_player_data_cache()
        self.manager.get_player_data_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_player_data_cache()
        self.manager.get_player_data_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSavePlayerDataCache:
    """Test CacheManager.save_player_data_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_player_data_cache({"2024": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._player_data_cache = {"2024": {}}

        self.manager.save_player_data_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_player_data_cache()

        assert "No player data cache to save" in str(exc_info.value)


class TestGetReplacementScoreCache:
    """Test CacheManager.get_replacement_score_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"1": {"QB": 15.0}}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_replacement_score_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_replacement_score_cache()
        self.manager.get_replacement_score_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_replacement_score_cache()
        self.manager.get_replacement_score_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveReplacementScoreCache:
    """Test CacheManager.save_replacement_score_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_replacement_score_cache({"2024": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._replacement_score_cache = {"2024": {}}

        self.manager.save_replacement_score_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_replacement_score_cache()

        assert "No replacement score cache to save" in str(exc_info.value)


class TestGetValidOptionsCache:
    """Test CacheManager.get_valid_options_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "2024": {"1": {"positions": ["QB"]}},
            }
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_valid_options_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_valid_options_cache()
        self.manager.get_valid_options_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_valid_options_cache()
        self.manager.get_valid_options_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveValidOptionsCache:
    """Test CacheManager.save_valid_options_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_valid_options_cache({"2024": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._valid_options_cache = {"2024": {}}

        self.manager.save_valid_options_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_valid_options_cache()

        assert "No valid options cache to save" in str(exc_info.value)


class TestGetImageUrlsCache:
    """Test CacheManager.get_image_urls_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "Tommy": {"image_url": "https://example.com/tommy.jpg"},
            }
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_image_urls_cache()

        self.mock_load_cache.assert_called_once()
        assert "Tommy" in result

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_image_urls_cache()
        self.manager.get_image_urls_cache()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_image_urls_cache()
        self.manager.get_image_urls_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveImageUrlsCache:
    """Test CacheManager.save_image_urls_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_image_urls_cache({"Tommy": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._image_urls_cache = {"Tommy": {}}

        self.manager.save_image_urls_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_image_urls_cache()

        assert "No image urls cache to save" in str(exc_info.value)


class TestGetWeeklyDataProgressTracker:
    """Test CacheManager.get_weekly_data_progress_tracker method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_load_cache") as mock_load_cache:
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"last_updated": "5"}}
            self.manager = CacheManager()

            yield

    def test_loads_on_first_access(self):
        """Test loads cache from disk on first access."""
        result = self.manager.get_weekly_data_progress_tracker()

        self.mock_load_cache.assert_called_once()
        assert result == {"2024": {"last_updated": "5"}}

    def test_returns_cached_on_second_access(self):
        """Test returns in-memory cache on second access."""
        self.manager.get_weekly_data_progress_tracker()
        self.manager.get_weekly_data_progress_tracker()

        self.mock_load_cache.assert_called_once()

    def test_force_reload(self):
        """Test force_reload reloads from disk."""
        self.manager.get_weekly_data_progress_tracker()
        self.manager.get_weekly_data_progress_tracker(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveWeeklyDataProgressTracker:
    """Test CacheManager.save_weekly_data_progress_tracker method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_provided_cache(self):
        """Test saves explicitly provided cache data."""
        self.manager.save_weekly_data_progress_tracker({"2024": {}})

        self.mock_save_cache.assert_called_once()

    def test_saves_in_memory_cache(self):
        """Test saves in-memory cache when no arg provided."""
        self.manager._weekly_data_progress_tracker = {"2024": {}}

        self.manager.save_weekly_data_progress_tracker()

        self.mock_save_cache.assert_called_once()

    def test_raises_when_no_data(self):
        """Test raises ValueError when no data to save."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.save_weekly_data_progress_tracker()

        assert "No weekly data progress tracker to save" in str(
            exc_info.value
        )


class TestReloadAllCaches:
    """Test CacheManager.reload_all_caches method."""

    def test_clears_all_in_memory_caches(self):
        """Test sets all in-memory caches to None."""
        manager = CacheManager()
        manager._manager_cache = {"data": True}
        manager._transaction_ids_cache = {"data": True}
        manager._players_cache = {"data": True}
        manager._player_ids_cache = {"data": True}
        manager._starters_cache = {"data": True}
        manager._player_data_cache = {"data": True}
        manager._replacement_score_cache = {"data": True}
        manager._valid_options_cache = {"data": True}
        manager._image_urls_cache = {"data": True}
        manager._weekly_data_progress_tracker = {"data": True}

        manager.reload_all_caches()

        assert manager._manager_cache is None
        assert manager._transaction_ids_cache is None
        assert manager._players_cache is None
        assert manager._player_ids_cache is None
        assert manager._starters_cache is None
        assert manager._player_data_cache is None
        assert manager._replacement_score_cache is None
        assert manager._valid_options_cache is None
        assert manager._image_urls_cache is None
        assert manager._weekly_data_progress_tracker is None


class TestSaveAllCaches:
    """Test CacheManager.save_all_caches method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with patch.object(CacheManager, "_save_cache") as mock_save_cache:
            self.mock_save_cache = mock_save_cache
            self.manager = CacheManager()

            yield

    def test_saves_all_loaded_caches(self):
        """Test saves all caches that have been loaded (not None)."""
        self.manager._manager_cache = {"Tommy": {}}
        self.manager._transaction_ids_cache = {"tx": {}}
        self.manager._players_cache = {"p": {}}
        self.manager._player_ids_cache = {"4046": {}}
        self.manager._starters_cache = {"2024": {}}
        self.manager._player_data_cache = {"2024": {}}
        self.manager._replacement_score_cache = {"2024": {}}
        self.manager._valid_options_cache = {"2024": {}}
        self.manager._image_urls_cache = {"Tommy": {}}
        self.manager._weekly_data_progress_tracker = {"2024": {}}

        self.manager.save_all_caches()

        assert self.mock_save_cache.call_count == 10

    def test_saves_only_loaded_caches(self):
        """Test only saves caches that have been loaded (not None)."""
        self.manager._manager_cache = {"Tommy": {}}
        self.manager._starters_cache = {"2024": {}}

        self.manager.save_all_caches()

        assert self.mock_save_cache.call_count == 2

    def test_skips_none_caches(self):
        """Test does not save caches that are None."""
        self.manager.save_all_caches()

        self.mock_save_cache.assert_not_called()


class TestGetCacheManager:
    """Test get_cache_manager singleton function."""

    def test_returns_cache_manager_instance(self):
        """Test returns a CacheManager instance."""
        with patch(
            "patriot_center_backend.cache.cache_manager"
            "._cache_manager_instance",
            None,
        ):
            result = get_cache_manager()

        assert isinstance(result, CacheManager)

    def test_returns_same_instance(self):
        """Test returns the same instance on subsequent calls."""
        with patch(
            "patriot_center_backend.cache.cache_manager"
            "._cache_manager_instance",
            None,
        ):
            instance1 = get_cache_manager()
            instance2 = get_cache_manager()

        assert instance1 is instance2
