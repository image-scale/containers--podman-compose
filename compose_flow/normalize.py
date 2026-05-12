"""
Data normalization utilities for compose file processing.

Provides functions to convert between different data formats (list/dict),
parse time strings, compare version numbers, and parse mount specifications.
"""

from __future__ import annotations

import os
import re
from typing import Any


def is_iterable(obj: Any) -> bool:
    """
    Check if object is iterable but not a string or dict.

    Args:
        obj: Any object to check

    Returns:
        True if obj is an iterable collection (list, tuple, etc.) but not str/dict
    """
    return (
        not isinstance(obj, str)
        and not isinstance(obj, dict)
        and hasattr(obj, "__iter__")
    )


def as_list(src: dict[str, Any] | list[Any] | str | None) -> list[Any]:
    """
    Convert various inputs to a list format.

    - None -> []
    - dict {key: value} -> ["key=value"] (None values become just "key")
    - list -> passed through
    - str -> [str]
    - other iterable -> list(iterable)

    Args:
        src: The input to convert

    Returns:
        A list representation of the input
    """
    if src is None:
        return []
    if isinstance(src, dict):
        return [(f"{k}={v}" if v is not None else k) for k, v in src.items()]
    if is_iterable(src):
        return list(src)
    return [src]


def as_dict(src: None | dict[str, str | None] | list[str] | str) -> dict[str, str | None]:
    """
    Convert various inputs to a dict format.

    - None -> {}
    - dict -> passed through (copied)
    - list ["key=value", "key2"] -> {"key": "value", "key2": None}
    - str "key=value" -> {"key": "value"}
    - str "key" -> {"key": None}

    Args:
        src: The input to convert

    Returns:
        A dict representation of the input

    Raises:
        ValueError: If input is not a recognized type
    """
    if src is None:
        return {}
    if isinstance(src, dict):
        return dict(src)
    if is_iterable(src):
        result = {}
        for item in src:
            if not item:
                continue
            parts = item.split("=", 1)
            if len(parts) == 2:
                result[parts[0]] = parts[1]
            else:
                result[parts[0]] = None
        return result
    if isinstance(src, str):
        if "=" in src:
            key, value = src.split("=", 1)
            return {key: value}
        return {src: None}
    raise ValueError("dictionary or iterable is expected")


def filter_empty(items: list[str]) -> list[str]:
    """Filter out empty strings from a list."""
    return [i for i in items if i]


def normalize_ulimit(value: dict | list | int | str) -> str:
    """
    Normalize ulimit value to "soft:hard" format.

    Args:
        value: Can be:
            - dict with "soft" and/or "hard" keys
            - list of key=value strings
            - int or str (returned as-is)

    Returns:
        String in "soft:hard" format, or the input as string

    Raises:
        ValueError: If dict doesn't contain soft or hard keys
    """
    if isinstance(value, dict):
        if not value.keys() & {"soft", "hard"}:
            raise ValueError("expected at least one soft or hard limit")
        soft = value.get("soft", value.get("hard"))
        hard = value.get("hard", value.get("soft"))
        return f"{soft}:{hard}"
    if is_iterable(value):
        return normalize_ulimit(as_dict(value))  # type: ignore
    # int or string - return as-is
    return str(value) if isinstance(value, int) else value  # type: ignore


# Pattern for parsing time strings like "3m", "30s", "1m30s", "1:30"
TIME_PATTERN = re.compile(r"^(?:(\d+)[m:])?(?:(\d+(?:\.\d+)?)s?)?$")


def time_to_seconds(txt: int | str | None) -> int | None:
    """
    Parse a time string to integer seconds.

    Supports formats:
        - "30" or "30s" -> 30
        - "3m" -> 180
        - "1m30s" or "1:30" -> 90
        - Already int -> returned as-is

    Args:
        txt: Time string or integer

    Returns:
        Integer seconds, or None if input is None or unparseable
    """
    if not txt:
        return None
    if isinstance(txt, (int, float)):
        return int(txt)

    txt = str(txt).strip()
    match = TIME_PATTERN.match(txt)
    if not match:
        return None

    minutes_str, seconds_str = match.groups()
    minutes = int(minutes_str) if minutes_str else 0
    seconds = float(seconds_str) if seconds_str else 0

    # Return as int since podman stop only accepts integer seconds
    return int(minutes * 60 + seconds)


# Pattern for splitting version strings
NUM_SPLIT_PATTERN = re.compile(r"(\d+|\D+)")


def version_to_list(version: str) -> list[int | str]:
    """
    Convert version string to list for comparison.

    "1.2.3" -> [1, '.', 2, '.', 3]
    """
    result = []
    for part in NUM_SPLIT_PATTERN.findall(version or ""):
        try:
            result.append(int(part))
        except ValueError:
            result.append(part)
    return result


def version_less_than(a: str, b: str) -> bool:
    """
    Compare two version strings.

    Args:
        a: First version string
        b: Second version string

    Returns:
        True if version a < version b
    """
    return version_to_list(a or "") < version_to_list(b or "")


def safe_int(value: int | str, fallback: int | None = None) -> int | None:
    """
    Try to convert value to int, return fallback on failure.

    Args:
        value: Value to convert
        fallback: Value to return if conversion fails

    Returns:
        Integer value or fallback
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return fallback


def safe_float(value: int | str, fallback: float | None = None) -> float | None:
    """
    Try to convert value to float, return fallback on failure.

    Args:
        value: Value to convert
        fallback: Value to return if conversion fails

    Returns:
        Float value or fallback
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return fallback


# Pattern for recognizing directory-like paths
DIR_PATTERN = re.compile(r"^[~/\.]")

# Pattern for recognizing mount propagation options
PROPAGATION_PATTERN = re.compile(
    r"^(?:z|Z|O|U|r?shared|r?slave|r?private|r?unbindable|r?bind|(?:no)?(?:exec|dev|suid))$"
)


def parse_short_mount(mount_str: str, basedir: str = ".") -> dict[str, Any]:
    """
    Parse short-format volume mount string to a mount dictionary.

    Formats:
        - "/container" -> anonymous volume
        - "/host:/container" -> bind mount or named volume
        - "/host:/container:opts" -> with options
        - "name:/container" -> named volume

    Args:
        mount_str: The mount specification string
        basedir: Base directory for resolving relative paths

    Returns:
        Dictionary with mount configuration:
            - type: "bind" or "volume"
            - source: source path/name (None for anonymous)
            - target: target path in container
            - read_only: optional bool
            - consistency: optional str
            - bind: dict with propagation options

    Raises:
        ValueError: If mount string cannot be parsed
    """
    parts = mount_str.split(":")
    mount_options: dict[str, Any] = {}

    if len(parts) == 1:
        # Anonymous volume: just a container path
        source = None
        target = mount_str
        opts_str = None
    elif len(parts) == 2:
        source, target = parts
        # Check if "target" is actually options (starts with non-path char)
        if not target.startswith("/"):
            # It's "/path:options" not "/host:/target"
            target, opts_str = parts
            source = None
        else:
            opts_str = None
    elif len(parts) == 3:
        source, target, opts_str = parts
    else:
        raise ValueError(f"could not parse mount {mount_str}")

    # Determine mount type based on source
    if source and DIR_PATTERN.match(source):
        # Path-like source: bind mount
        mount_type = "bind"
        # Resolve relative and home-relative paths
        if os.name != 'nt' or (os.name == 'nt' and ".sock" not in source):
            source = os.path.abspath(os.path.join(basedir, os.path.expanduser(source)))
    else:
        # Named volume
        mount_type = "volume"

    # Parse options
    propagation_opts = []
    if opts_str:
        for opt in filter_empty(opts_str.split(",")):
            if opt == "ro":
                mount_options["read_only"] = True
            elif opt == "rw":
                mount_options["read_only"] = False
            elif opt in ("consistent", "delegated", "cached"):
                mount_options["consistency"] = opt
            elif PROPAGATION_PATTERN.match(opt):
                propagation_opts.append(opt)
            else:
                raise ValueError(f"unknown mount option {opt}")

    mount_options["bind"] = {"propagation": ",".join(propagation_opts)}

    return {
        "type": mount_type,
        "source": source,
        "target": target,
        **mount_options,
    }


def is_relative_path(path: str) -> bool:
    """
    Check if path is a relative reference.

    Args:
        path: Path to check

    Returns:
        True if path starts with ./ or ../ or .: or ..:
    """
    return (
        path.startswith("./")
        or path.startswith(".:")
        or path.startswith("../")
        or path.startswith("..:")
    )
