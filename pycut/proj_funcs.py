from pathlib import Path

DEFAULT_SCRIPT = """
# This is a python script! Yes, you can edit videos with Python now!
# Moreover, you can modify and interfere with the mere lib you using to edit videos.
# Let me create some basic stuff for you...

import logging
from pycut.video.classes import *
from pycut.video.functions import *
import asyncio

# For information use docstrings from the lib.
# help(pycut)

logging.basicConfig(
    level=logging.INFO,  
    format="%(name)s - %(levelname)s - %(message)s", 
    stream=sys.stderr,
)

# You can look for this keyword with pycut.speech.find_keywords()
keyword = "монтаж"

video_edit = [
    *Trim("1s","10s")
]

audio_edit = [
    *Trim("1s","10s")
]

async def edit():
    await compose("input.mp4", "output.mp4", video_edit, audio_edit)

asyncio.run(edit())
"""


def generate_project(proj_dir: str):
    proj_path = Path(proj_dir)
    proj_path.mkdir(exist_ok=True)
    with open(proj_path / "video_script.py", "w+") as f:
        f.write(DEFAULT_SCRIPT)
