from pathlib import Path

DEFAULT_SCRIPT = """
# This is a python script! Yes, you can edit videos with Python now!
# Moreover, you can modify and interfere with the mere lib you using to edit videos.
# Let me create some basic stuff for you...

import pycut.video
import asyncio

# You have this tools at your disposal:
# -----
# From pycut.video:
# Classes for editing:
# - VideoImage
# - VideoText
# - VideoTrim
# - VideoCut
# Useful functions:
# - detect_silence_fragments() -> list[tuple[int, int]]
# And main composing function:
# - compose() -> FFmpeg
# To render your final video you must .execute() the instance of FFmpeg class.
# -----
# From pycut.speech:
# Useful functions:
# - find_keywords() -> list[tuple[int, int]]
# -----
# From pycut.jsons:
# Useful functions:
# - is_serializable() -> bool
# - serialize() -> None
# - unserialize() -> object
# -----
# For more information use docstrings from the lib.
# help(pycut)

# You can look for this keyword with pycut.speech.find_keywords()
keyword = "монтаж"

editing = [
    pycut.video.VideoTrim("1s","10s")
]

async def edit():
    baked = await pycut.video.compose("input.mp4", "output.mp4", *editing)
    await baked.execute()

asyncio.run(edit())
"""


def generate_project(proj_dir: str):
    proj_path = Path(proj_dir)
    proj_path.mkdir(exist_ok=True)
    with open(proj_path / "video_script.py", "w+") as f:
        f.write(DEFAULT_SCRIPT)
