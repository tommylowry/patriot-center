"""Utility functions for formatting and normalizing data structures."""

from typing import Any


def flatten_dict(
    d: dict[Any, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """Recursively flatten a nested dict into a single-level dict.

    Keys are concatenated with the provided separator. Non-dict values are
    copied directly. Non-dict inputs yield an empty dict.

    Args:
        d: Nested dict to flatten. If not a dict, returns an empty dict.
        parent_key: Prefix carried through recursive calls.
        sep: Separator for concatenated keys.

    Returns:
        Flattened dictionary.
    """
    out = {}

    if not isinstance(d, dict):
        return out

    # Safe iteration: handles None/non-dict inputs gracefully
    for k, v in (d or {}).items():
        # Build nested key path using separator
        nk = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recurse into nested dicts to flatten deeper levels
            out.update(flatten_dict(v, nk, sep))
        else:
            # Leaf value: add to output with full key path
            out[nk] = v
    return out


def to_records(data: Any, key_name: str = "key") -> list[dict[str, Any]]:
    """Normalize mixed dict/list structures into a list of record dicts.

    - Lists of dicts -> flattened dict per item.
    - Dicts -> each key becomes a record; nested dict/list values are expanded.
    - Scalars -> wrapped into a single record.

    Args:
        data: Input structure.
        key_name: Field name to assign original dict keys.

    Returns:
        List of normalized record dictionaries.
    """
    # Handle list inputs: flatten each item
    if isinstance(data, list):
        for item in data:
            return (
                [flatten_dict(item)]
                if isinstance(item, dict)
                else [{"value": item}]
            )

    # Handle dict inputs: convert to list of records with key field
    if isinstance(data, dict):
        rows = []
        for k, v in data.items():
            if isinstance(v, list):
                # Expand list values: create one record per list item
                for item in v:
                    row = {key_name: k}
                    row.update(
                        flatten_dict(item)
                        if isinstance(item, dict)
                        else {"value": item}
                    )
                    rows.append(row)
            elif isinstance(v, dict):
                # Nested dict: flatten and merge into record
                row = {key_name: k}
                row.update(flatten_dict(v))
                rows.append(row)
            else:
                # Scalar value: simple key-value record
                rows.append({key_name: k, "value": v})

        # Sort records alphabetically by key field for consistent ordering
        rows.sort(key=lambda item: item.get(key_name, ""), reverse=False)

        return rows

    # Fallback for scalar inputs: wrap in single-item list
    return [{"value": data}]
