"""Unit tests for cache_manager module."""

import json
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pytest

from patriot_center_backend.cache.cache_manager import (
    CacheManager,
    get_cache_manager,
)


class TestCacheManagerInit:
    """Test CacheManager initialization."""

    def test_init_sets_all_caches_to_none(self):
        """Test __init__ sets all cache references to None."""
        manager = CacheManager()

        assert manager._manager_cache is None
        assert manager._transaction_ids_cache is None
        assert manager._players_cache is None
        assert manager._player_ids_cache is None
        assert manager._starters_cache is None
        assert manager._player_data_cache is None
        assert manager._replacement_score_cache is None
        assert manager._valid_options_cache is None
        assert manager._image_urls_cache is None


class TestLoadCache:
    """Test _load_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `os.path.exists`: `mock_exists`
        - `open`: `mock_file_open`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_manager."
                "os.path.exists"
            ) as mock_exists,
            patch(
                "patriot_center_backend.cache.cache_manager.open",
                mock_open(read_data='{"key": "value"}')
            ),
        ):
            self.mock_exists = mock_exists
            self.mock_exists.return_value = True

            yield

    def test_returns_dict_when_file_exists(self):
        """Test returns parsed JSON when file exists."""
        manager = CacheManager()

        result = manager._load_cache("/path/to/cache.json")

        assert result == {"key": "value"}

    def test_returns_empty_dict_when_file_not_exists(self):
        """Test returns empty dict when file does not exist."""
        self.mock_exists.return_value = False
        manager = CacheManager()

        result = manager._load_cache("/path/to/cache.json")

        assert result == {}


class TestSaveCache:
    """Test _save_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `builtins.open`: `mock_file_open`
        - `Path.mkdir`: `mock_mkdir`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_manager"
                ".open", mock_open()
            ) as mock_file_open,
            patch("pathlib.Path.mkdir") as mock_mkdir,
        ):
            self.mock_file_open = mock_file_open
            self.mock_mkdir = mock_mkdir

            yield

    def test_writes_json_to_file(self):
        """Test writes JSON data to file with proper formatting."""
        manager = CacheManager()
        data = {"key": "value"}

        manager._save_cache("/path/to/cache.json", data)

        self.mock_file_open.assert_called_once_with("/path/to/cache.json", "w")
        handle = self.mock_file_open()
        written_data = "".join(
            call.args[0] for call in handle.write.call_args_list
        )
        assert json.loads(written_data) == data

    def test_creates_parent_directories(self):
        """Test creates parent directories if they don't exist."""
        manager = CacheManager()
        data = {"key": "value"}

        manager._save_cache("/path/to/cache.json", data)

        self.mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGetManagerCache:
    """Test get_manager_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"Tommy": {"summary": {}}}

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_manager_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"Tommy": {"summary": {}}}

    def test_returns_cached_value_on_subsequent_access(self):
        """Test returns in-memory cache on subsequent access."""
        manager = CacheManager()
        manager.get_manager_cache()

        manager.get_manager_cache()

        assert self.mock_load_cache.call_count == 1

    def test_reloads_when_force_reload_true(self):
        """Test reloads from disk when force_reload=True."""
        manager = CacheManager()
        manager.get_manager_cache()

        manager.get_manager_cache(force_reload=True)

        assert self.mock_load_cache.call_count == 2


class TestSaveManagerCache:
    """Test save_manager_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._save_cache`: `mock_save_cache`

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_save_cache") as mock_save_cache,
        ):
            self.mock_save_cache = mock_save_cache

            yield

    def test_saves_provided_cache(self):
        """Test saves provided cache to disk."""
        manager = CacheManager()
        cache = {"Tommy": {"summary": {}}}

        manager.save_manager_cache(cache)

        self.mock_save_cache.assert_called_once()
        assert self.mock_save_cache.call_args[0][1] == cache

    def test_saves_in_memory_cache_when_none_provided(self):
        """Test saves in-memory cache when no cache provided."""
        manager = CacheManager()
        manager._manager_cache = {"Tommy": {"summary": {}}}

        manager.save_manager_cache()

        self.mock_save_cache.assert_called_once()

    def test_raises_error_when_no_cache_to_save(self):
        """Test raises ValueError when no cache data to save."""
        manager = CacheManager()

        with pytest.raises(ValueError) as exc_info:
            manager.save_manager_cache()

        assert "No manager cache data" in str(exc_info.value)


class TestIsPlayerIdsCacheStale:
    """Test is_player_ids_cache_stale method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `os.path.getmtime`: `mock_getmtime`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_manager.os.path.getmtime"
            ) as mock_getmtime,
        ):
            self.mock_getmtime = mock_getmtime

            yield

    def test_returns_true_when_file_not_found(self):
        """Test returns True when cache file doesn't exist."""
        self.mock_getmtime.side_effect = FileNotFoundError()
        manager = CacheManager()

        result = manager.is_player_ids_cache_stale()

        assert result is True

    def test_returns_true_when_file_older_than_week(self):
        """Test returns True when cache file is older than 1 week."""
        old_time = (datetime.now() - timedelta(weeks=2)).timestamp()
        self.mock_getmtime.return_value = old_time
        manager = CacheManager()

        result = manager.is_player_ids_cache_stale()

        assert result is True

    def test_returns_false_when_file_within_week(self):
        """Test returns False when cache file is less than 1 week old."""
        recent_time = (datetime.now() - timedelta(days=3)).timestamp()
        self.mock_getmtime.return_value = recent_time
        manager = CacheManager()

        result = manager.is_player_ids_cache_stale()

        assert result is False


class TestGetStartersCache:
    """Test get_starters_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CacheManager._load_cache`: `mock_load_cache`
        - `LEAGUE_IDS`: `mock_league_ids`

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
            patch(
                "patriot_center_backend.cache.cache_manager.LEAGUE_IDS",
                {2023: "league2023", 2024: "league2024"},
            ),
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {}

            yield

    def test_initializes_for_update_when_cache_empty(self):
        """Test initializes cache structure when for_update=True and empty."""
        manager = CacheManager()

        result = manager.get_starters_cache(for_update=True)

        assert "Last_Updated_Season" in result
        assert "Last_Updated_Week" in result
        assert "2023" in result
        assert "2024" in result

    def test_removes_metadata_fields_when_not_for_update(self):
        """Test removes metadata fields when for_update=False."""
        self.mock_load_cache.return_value = {
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": 5,
            "2024": {},
        }
        manager = CacheManager()

        result = manager.get_starters_cache(for_update=False)

        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result
        assert "2024" in result


class TestReloadAllCaches:
    """Test reload_all_caches method."""

    def test_clears_all_in_memory_caches(self):
        """Test clears all in-memory cache references."""
        manager = CacheManager()
        manager._manager_cache = {"data": "value"}
        manager._transaction_ids_cache = {"data": "value"}
        manager._players_cache = {"data": "value"}
        manager._player_ids_cache = {"data": "value"}
        manager._starters_cache = {"data": "value"}
        manager._player_data_cache = {"data": "value"}
        manager._replacement_score_cache = {"data": "value"}
        manager._valid_options_cache = {"data": "value"}
        manager._image_urls_cache = {"data": "value"}

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


class TestSaveAllCaches:
    """Test save_all_caches method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - Various save methods on CacheManager

        Yields:
            None
        """
        with (
            patch.object(
                CacheManager, "save_manager_cache"
            ) as mock_save_manager,
            patch.object(
                CacheManager, "save_transaction_ids_cache"
            ) as mock_save_trans,
            patch.object(
                CacheManager, "save_players_cache"
            ) as mock_save_players,
            patch.object(
                CacheManager, "save_player_ids_cache"
            ) as mock_save_player_ids,
            patch.object(
                CacheManager, "save_starters_cache"
            ) as mock_save_starters,
            patch.object(
                CacheManager, "save_player_data_cache"
            ) as mock_save_player_data,
            patch.object(
                CacheManager, "save_replacement_score_cache"
            ) as mock_save_replacement,
            patch.object(
                CacheManager, "save_valid_options_cache"
            ) as mock_save_valid,
            patch.object(
                CacheManager, "save_image_urls_cache"
            ) as mock_save_image,
        ):
            self.mock_save_manager = mock_save_manager
            self.mock_save_trans = mock_save_trans
            self.mock_save_players = mock_save_players
            self.mock_save_player_ids = mock_save_player_ids
            self.mock_save_starters = mock_save_starters
            self.mock_save_player_data = mock_save_player_data
            self.mock_save_replacement = mock_save_replacement
            self.mock_save_valid = mock_save_valid
            self.mock_save_image = mock_save_image

            yield

    def test_saves_only_loaded_caches(self):
        """Test only saves caches that have been loaded."""
        manager = CacheManager()
        manager._manager_cache = {"data": "value"}
        manager._starters_cache = {"data": "value"}

        manager.save_all_caches()

        self.mock_save_manager.assert_called_once()
        self.mock_save_starters.assert_called_once()
        self.mock_save_trans.assert_not_called()
        self.mock_save_players.assert_not_called()

    def test_saves_all_loaded_caches(self):
        """Test saves all caches when all are loaded."""
        manager = CacheManager()
        manager._manager_cache = {}
        manager._transaction_ids_cache = {}
        manager._players_cache = {}
        manager._player_ids_cache = {}
        manager._starters_cache = {}
        manager._player_data_cache = {}
        manager._replacement_score_cache = {}
        manager._valid_options_cache = {}
        manager._image_urls_cache = {}

        manager.save_all_caches()

        self.mock_save_manager.assert_called_once()
        self.mock_save_trans.assert_called_once()
        self.mock_save_players.assert_called_once()
        self.mock_save_player_ids.assert_called_once()
        self.mock_save_starters.assert_called_once()
        self.mock_save_player_data.assert_called_once()
        self.mock_save_replacement.assert_called_once()
        self.mock_save_valid.assert_called_once()
        self.mock_save_image.assert_called_once()


class TestGetCacheManager:
    """Test get_cache_manager singleton function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton before each test.

        Yields:
            None
        """
        import patriot_center_backend.cache.cache_manager as cm

        cm._cache_manager_instance = None

        yield

        cm._cache_manager_instance = None

    def test_returns_cache_manager_instance(self):
        """Test returns a CacheManager instance."""
        result = get_cache_manager()

        assert isinstance(result, CacheManager)

    def test_returns_same_instance_on_multiple_calls(self):
        """Test returns the same singleton instance on multiple calls."""
        result1 = get_cache_manager()
        result2 = get_cache_manager()

        assert result1 is result2


class TestGetTransactionIdsCache:
    """Test get_transaction_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"txn1": {"data": "value"}}

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_transaction_ids_cache()

        self.mock_load_cache.assert_called_once()
        assert result == {"txn1": {"data": "value"}}


class TestGetPlayersCache:
    """Test get_players_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "Patrick Mahomes": {"position": "QB"}
            }

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_players_cache()

        self.mock_load_cache.assert_called_once()
        assert "Patrick Mahomes" in result


class TestGetPlayerIdsCache:
    """Test get_player_ids_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "4046": {"full_name": "Patrick Mahomes"}
            }

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_player_ids_cache()

        self.mock_load_cache.assert_called_once()
        assert "4046" in result


class TestGetPlayerDataCache:
    """Test get_player_data_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"5": {}}}

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_player_data_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result


class TestGetReplacementScoreCache:
    """Test get_replacement_score_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {"2024": {"5": {"QB": 15.0}}}

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_replacement_score_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result


class TestGetValidOptionsCache:
    """Test get_valid_options_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "2024": {"managers": ["Tommy"]}
            }

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_valid_options_cache()

        self.mock_load_cache.assert_called_once()
        assert "2024" in result


class TestGetImageUrlsCache:
    """Test get_image_urls_cache method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch.object(CacheManager, "_load_cache") as mock_load_cache,
        ):
            self.mock_load_cache = mock_load_cache
            self.mock_load_cache.return_value = {
                "Tommy": {"image_url": "http://..."}
            }

            yield

    def test_loads_cache_on_first_access(self):
        """Test loads cache from disk on first access."""
        manager = CacheManager()

        result = manager.get_image_urls_cache()

        self.mock_load_cache.assert_called_once()
        assert "Tommy" in result
