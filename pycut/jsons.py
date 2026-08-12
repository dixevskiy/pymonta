import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def is_serializable(data: object) -> bool:
    try:
        json.dumps(data)
        return True
    except:
        return False


def serialize(data: object, json_path: str):
    file = Path(json_path)
    try:
        file.touch()
        with open(file, "w") as f:
            json.dump(data, f)
    except OSError as e:
        LOGGER.error(f"Failed miserably when tried to write in {file}, because of {e}")
        raise


def unserialize(json_path) -> object:
    file = Path(json_path)
    try:
        with open(file, "r") as f:
            return json.load(f)
    except OSError as e:
        LOGGER.error(
            f"Failed miserably when tried to read or parse {file}, because of {e}"
        )
        raise
