"""
Recursive substitution and merge functions for compose files.

Provides functions to apply variable interpolation recursively through
compose data structures and to merge multiple compose files together.
"""

from __future__ import annotations

from typing import Any, Iterable

from compose_flow.interpolation import interpolate
from compose_flow.normalize import is_iterable


def clone(value: Any) -> Any:
    """
    Create a shallow copy of lists and dicts, pass through other values.

    Args:
        value: Value to potentially copy

    Returns:
        A copy if list or dict, otherwise the original value
    """
    if isinstance(value, dict):
        return value.copy()
    if is_iterable(value):
        return list(value)
    return value


def recursive_substitute(
    value: dict | str | Iterable | Any,
    env: dict[str, Any]
) -> dict | str | Iterable | Any:
    """
    Apply variable interpolation recursively through a data structure.

    Handles:
    - Strings: apply interpolate() to resolve variables
    - Dicts: substitute in both keys and values, with special handling
      for 'environment' sections (service env vars are added to context)
    - Lists/iterables: substitute in each element
    - Other types: passed through unchanged

    Args:
        value: The data structure to process
        env: Dictionary of environment variables for substitution

    Returns:
        A new data structure with all variables resolved
    """
    if isinstance(value, dict):
        # Special handling for service environment sections
        if 'environment' in value and isinstance(value['environment'], dict):
            # Copy the substitution dict and add service environment variables
            env = env.copy()
            svc_envs = {
                k: v for k, v in value['environment'].items()
                if k not in env
            }
            # Service envs can reference each other, so substitute them first
            svc_envs = recursive_substitute(svc_envs, env)
            env.update(svc_envs)

        # Substitute in both keys and values
        return {
            recursive_substitute(k, env): recursive_substitute(v, env)
            for k, v in value.items()
        }
    elif isinstance(value, str):
        return interpolate(value, env)
    elif is_iterable(value):
        return [recursive_substitute(item, env) for item in value]
    return value


def recursive_merge_one(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """
    Merge source dictionary into target recursively.

    Behavior:
    - Keys only in source are added to target
    - Keys only in target are kept
    - For matching keys:
      - command/entrypoint: source replaces target
      - lists (except volumes): source is appended to target
      - volumes list: source replaces matching mount targets
      - dicts: recursively merged
      - other values: source replaces target

    Args:
        target: The target dictionary (modified in place)
        source: The source dictionary to merge from

    Returns:
        The modified target dictionary

    Raises:
        ValueError: If incompatible types are merged
    """
    # Track keys we've processed
    processed = set()

    # Add keys that are only in source
    for key, value in source.items():
        if key not in target:
            target[key] = clone(value)
            processed.add(key)

    # Process keys in target
    for key, target_value in target.items():
        if key in processed:
            continue

        if key not in source:
            # Handle None values in target that might get dicts merged in
            if target_value is None:
                continue
            continue

        source_value = source[key]

        # command and entrypoint are replaced, not merged
        if key in ("command", "entrypoint"):
            target[key] = clone(source_value)
            continue

        # Handle None in target - can merge dicts into it
        if target_value is None and isinstance(source_value, dict):
            target[key] = target_value = {}

        # Type check
        if not isinstance(source_value, type(target_value)):
            # Allow compatible types
            if not (target_value is None or source_value is None):
                raise ValueError(
                    f"can't merge value of [{key}] of type "
                    f"{type(target_value)} and {type(source_value)}"
                )

        # Merge based on type
        if is_iterable(source_value):
            if key == "volumes":
                # Special handling for volumes - remove duplicates by target path
                existing_targets = {
                    v.split(":", 2)[1] if ":" in v else v
                    for v in source_value
                    if isinstance(v, str)
                }
                # Remove conflicting entries from target
                filtered = []
                for v in target_value:
                    if isinstance(v, str) and ":" in v:
                        target_path = v.split(":", 2)[1]
                        if target_path in existing_targets:
                            continue
                    filtered.append(v)
                filtered.extend(source_value)
                target[key] = filtered
            else:
                # Normal list merge - append
                target_value.extend(source_value)
        elif isinstance(source_value, dict):
            recursive_merge_one(target_value, source_value)
        else:
            # Replace with source value
            target[key] = source_value

    return target


def recursive_merge(target: dict[str, Any], *sources: dict[str, Any]) -> dict[str, Any]:
    """
    Merge multiple source dictionaries into target recursively.

    Args:
        target: The target dictionary
        *sources: Any number of source dictionaries to merge

    Returns:
        The modified target dictionary
    """
    for source in sources:
        recursive_merge_one(target, source)
    return target
