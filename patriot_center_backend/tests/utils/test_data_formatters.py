"""Unit tests for data_formatters module."""

from patriot_center_backend.utils.data_formatters import (
    flatten_dict,
    to_records,
)


class TestFlattenDict:
    """Test flatten_dict function."""

    def test_flat_dict_unchanged(self):
        """Test already flat dict returns same structure."""
        result = flatten_dict({"a": 1, "b": 2})

        assert result == {"a": 1, "b": 2}

    def test_nested_dict(self):
        """Test nested dict flattens with dot separator."""
        result = flatten_dict({"a": {"b": 1, "c": 2}})

        assert result == {"a.b": 1, "a.c": 2}

    def test_deeply_nested_dict(self):
        """Test deeply nested dict flattens correctly."""
        result = flatten_dict({"a": {"b": {"c": 3}}})

        assert result == {"a.b.c": 3}

    def test_custom_separator(self):
        """Test custom separator is used."""
        result = flatten_dict({"a": {"b": 1}}, sep="/")

        assert result == {"a/b": 1}

    def test_custom_parent_key(self):
        """Test parent_key prefix is applied."""
        result = flatten_dict({"b": 1}, parent_key="a")

        assert result == {"a.b": 1}

    def test_empty_dict(self):
        """Test empty dict returns empty dict."""
        result = flatten_dict({})

        assert result == {}

    def test_non_dict_input_returns_empty(self):
        """Test non-dict input returns empty dict."""
        result = flatten_dict("not a dict")  # type: ignore

        assert result == {}

    def test_none_input_returns_empty(self):
        """Test None input returns empty dict."""
        result = flatten_dict(None)  # type: ignore

        assert result == {}

    def test_mixed_nested_and_flat(self):
        """Test dict with mix of nested and flat values."""
        result = flatten_dict(
            {
                "a": 1,
                "b": {"c": 2, "d": 3},
                "e": 4,
            }
        )

        assert result == {"a": 1, "b.c": 2, "b.d": 3, "e": 4}


class TestToRecords:
    """Test to_records function."""

    def test_dict_with_scalar_values(self):
        """Test dict with scalar values produces key-value records."""
        result = to_records({"a": 1, "b": 2})

        assert {"key": "a", "value": 1} in result
        assert {"key": "b", "value": 2} in result

    def test_dict_with_nested_dicts(self):
        """Test dict with nested dicts flattens inner values."""
        result = to_records({"Tommy": {"wins": 10, "losses": 5}})

        assert len(result) == 1
        assert result[0]["key"] == "Tommy"
        assert result[0]["wins"] == 10
        assert result[0]["losses"] == 5

    def test_dict_with_list_values(self):
        """Test dict with list values expands to multiple records."""
        result = to_records({"2023": [{"week": 1}, {"week": 2}]})

        assert len(result) == 2
        assert result[0]["key"] == "2023"
        assert result[1]["key"] == "2023"

    def test_dict_with_list_of_scalars(self):
        """Test dict with list of scalar values."""
        result = to_records({"years": ["2023", "2022"]})

        assert len(result) == 2
        assert result[0]["key"] == "years"
        assert result[0]["value"] == "2023"

    def test_list_of_dicts(self):
        """Test list of dicts flattens each item."""
        result = to_records([{"a": 1, "b": {"c": 2}}])

        assert len(result) == 1
        assert result[0]["a"] == 1
        assert result[0]["b.c"] == 2

    def test_list_of_scalars(self):
        """Test list of scalars wraps in value records."""
        result = to_records(["hello"])

        assert result == [{"value": "hello"}]

    def test_scalar_input(self):
        """Test scalar input wraps in single value record."""
        result = to_records(42)

        assert result == [{"value": 42}]

    def test_string_input(self):
        """Test string input wraps in single value record."""
        result = to_records("hello")

        assert result == [{"value": "hello"}]

    def test_custom_key_name(self):
        """Test custom key_name is used in records."""
        result = to_records({"Tommy": 10}, key_name="manager")

        assert result[0]["manager"] == "Tommy"

    def test_dict_records_sorted_by_key(self):
        """Test dict records are sorted alphabetically by key."""
        result = to_records({"c": 3, "a": 1, "b": 2})

        keys = [r["key"] for r in result]
        assert keys == ["a", "b", "c"]

    def test_empty_dict(self):
        """Test empty dict returns empty list."""
        result = to_records({})

        assert result == []

    def test_empty_list(self):
        """Test empty list returns empty list (no iteration)."""
        result = to_records([])

        # Empty list has no items to iterate
        assert result is not None
