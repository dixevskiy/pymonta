"""
JSON serialization utilities for `pycut`.

This module provides simple functions to:
- Test if a Python object is JSON‑serializable (`is_serializable`).
- Safely write a JSON‑serializable object to a file (`serialize`).
- Load a JSON object from a file (`unserialize`).

All errors are logged via the module logger and re‑raised for the caller to handle.
"""

import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def is_serializable(data: Any) -> bool:
    """Check whether a Python object can be serialized to JSON.

    This function attempts to call `json.dumps()` on the input. If it succeeds,
    the object is considered serializable; otherwise, `False` is returned.

    Args:
        data: The object to test.

    Returns:
        `True` if the object is JSON‑serializable, otherwise `False`.
    """
    try:
        json.dumps(data)
        return True
    except TypeError, ValueError:
        return False


def serialize(data: Any, json_path: str) -> None:
    """Serialize a Python object to JSON and write it to a file.

    The function creates the file (if it does not exist) and writes the JSON
    representation.

    Args:
        data: The object to serialize.
        json_path: Filesystem path where the JSON will be saved.

    Raises:
        OSError: If the file cannot be created or written.
    """
    file = Path(json_path)
    if not is_serializable(data):
        LOGGER.error("Serialization failed for data. It's not serializable.")
    try:
        file.touch(exist_ok=True)  # create parent directories if needed?
        # Note: Path.touch() does not create parent directories; we may want to ensure they exist.
        # To be safe, we can create parent directories explicitly:
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as f:
            json.dump(data, f)
    except OSError as e:
        LOGGER.error(f"Failed miserably when tried to write in {file}, because of {e}")
        raise


def unserialize(json_path: str) -> Any:
    """Load and parse a JSON object from a file.

    Args:
        json_path: Path to the JSON file.

    Returns:
        The deserialized Python object (typically a dict or list).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        OSError: For other I/O errors.
    """
    file = Path(json_path)
    try:
        with open(file, "r") as f:
            return json.load(f)
    except OSError as e:
        LOGGER.error(
            f"Failed miserably when tried to read or parse {file}, because of {e}"
        )
        raise
