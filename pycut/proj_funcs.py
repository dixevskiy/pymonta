"""
Project initialisation for `pycut`.

This module provides the `generate_project` function, which creates a new
project directory and populates it with a default Python script (`video_script.py`).
The script contains a basic example that demonstrates how to use `pycut` to
edit a video.

The default script includes:
- Imports for all core `pycut` modules.
- Logging configuration.
- A sample video edit (trimming the first 10 seconds).
- An `edit()` coroutine that calls `compose()` and executes the FFmpeg pipeline.
"""

from pathlib import Path

DEFAULT_SCRIPT = """
# This is a python script! Yes, you can edit videos with Python now!
# Moreover, you can modify and interfere with the mere lib you using to edit videos.
# Let me create some basic stuff for you...

import logging
import sys
import asyncio
from pycut import compose, Trim, VideoText, TextLocations

# For information use docstrings from the lib.
# help(pycut)

logging.basicConfig(
    level=logging.INFO,  
    format="%(name)s - %(levelname)s - %(message)s", 
    stream=sys.stderr,
)

video_filters = [
    *Trim("5s", "20s"),
    VideoText("10s", "Hello World!", TextLocations.CENTER)
]

async def main():
    ffmpeg = compose("input.mp4", "output.mp4", video_filters)
    await ffmpeg.execute()

asyncio.run(main())
"""


def generate_project(proj_dir: str) -> None:
    """Create a new `pycut` project directory with a default editing script.

    The function creates the specified directory (and any missing parent
    directories) and writes a `video_script.py` file containing a ready-to-run
    example that trims the first 10 seconds of `input.mp4` to `output.mp4`.

    Args:
        proj_dir: Path to the project root directory (will be created if it
            does not exist).

    Raises:
        OSError: If the directory cannot be created or the script file cannot
            be written.
    """
    proj_path = Path(proj_dir)
    proj_path.mkdir(exist_ok=True, parents=True)
    with open(proj_path / "video_script.py", "w+") as f:
        f.write(DEFAULT_SCRIPT)