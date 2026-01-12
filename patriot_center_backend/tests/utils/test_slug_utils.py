"""Unit tests for slug_utils module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.utils.slug_utils import slug_to_name, slugify


class TestSlugify:
    """Unit tests for the slugify function. """

    def test_slugify_with_spaces(self):
        """
        Test that the slugify function replaces spaces with %20.
        """
        result = slugify("Patrick Mahomes")

        assert result == "patrick%20mahomes"

    def test_slugify_with_apostrophes(self):
        """
        Test that the slugify function replaces apostrophes with %27.
        """
        result = slugify("Ja'Marr Chase")

        assert result == "ja%27marr%20chase"

    def test_slugify_unchanged(self):
        """
        Test that the slugify function leaves unchanged strings unchanged.
        """
        result = slugify("patrick%20mahomes")

        assert result == "patrick%20mahomes"

class TestSlugToName:
    """Unit tests for the slug_to_name function. """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup a mock for CACHE_MANAGER.get_players_cache.

        This fixture will be executed automatically before each test.
        It patches CACHE_MANAGER.get_players_cache to return a mock object, and assigns it to self.get_players_cache.
        """
        with patch('patriot_center_backend.utils.slug_utils.CACHE_MANAGER.get_players_cache') as mock_get_players_cache:
            self.get_players_cache = mock_get_players_cache
            yield
    
    def test_slug_to_name_found(self):
        """
        Test that the slug_to_name function returns the correct full name when given a slug that exists in the cache.
        """
        self.get_players_cache.return_value = {
            "Ja'Marr Chase":   {"slug": "ja%27marr%20chase", 'full_name': "Ja'Marr Chase"},
            "Patrick Mahomes": {"slug": "patrick%20mahomes", 'full_name': "Patrick Mahomes"}
        }
        result = slug_to_name("ja%27marr%20chase")

        assert result == "Ja'Marr Chase"

    def test_slug_to_name_not_found(self):
        """
        Test that the slug_to_name function returns the slug unchanged when given a slug that does not exist in the cache.
        """
        self.get_players_cache.return_value = {
            "Ja'Marr Chase":   {"slug": "ja%27marr%20chase", 'full_name': "Ja'Marr Chase"},
            "Patrick Mahomes": {"slug": "patrick%20mahomes", 'full_name': "Patrick Mahomes"}
        }

        result = slug_to_name("amon-ra%20st.%20brown")

        assert result == "amon-ra%20st.%20brown"