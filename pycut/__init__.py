"""
a Python video editing toolkit for tech nerds.

pycut provides an abstraction over FFmpeg's filter graphs. It allows you
to compose complex video/audio edits using simple, chainable filters without
writing raw FFmpeg commands.

Main features:
- Declarative filter composition using `Pipe` and `Filter` abstractions.
- Common edits: trimming, cutting, overlaying text/images, adjusting volume,
  mixing audio, burning subtitles, and more.
- Speech transcription with Whisper (timestamped) and keyword search.
- JSON serialization utilities for saving/loading edit configurations.
- Project initialisation via CLI to get started quickly.

Subpackages:
- `pycut.video.classes` : Core classes
- `pycut.video.functions` : High-level functions
- `pycut.jsons` : JSON helpers
- `pycut.speech` : Whisper transcription
- `pycut.proj_funcs` : Project generator
"""

# Import core types and functions for easy access
from pycut.video.classes import (
    Filter,
    Media,
    Pipe,
    TextLocations,
    ImageLocations,
    VideoText,
    VideoImage,
    ChangeVolume,
    VideoAdjustments,
    NewAudio,
    InsertAudio,
    RemoveAudio,
    MuteRange,
    HardSubtitles,
    Cut,
    Trim,
)
from pycut.video.functions import compose, detect_silence_fragments, get_duration
from pycut.jsons import serialize, unserialize, is_serializable
from pycut.speech import transcribe_file, generate_srt, find_keywords
from pycut.proj_funcs import generate_project

__all__ = [
    # Core classes
    "Filter",
    "Media",
    "Pipe",
    "TextLocations",
    "ImageLocations",
    "VideoText",
    "VideoImage",
    "ChangeVolume",
    "VideoAdjustments",
    "NewAudio",
    "InsertAudio",
    "RemoveAudio",
    "MuteRange",
    "HardSubtitles",
    "Cut",
    "Trim",
    # High-level functions
    "compose",
    "detect_silence_fragments",
    "get_duration",
    # JSON utilities
    "serialize",
    "unserialize",
    "is_serializable",
    # Speech utilities
    "transcribe_file",
    "generate_srt",
    "find_keywords",
    # Project generation
    "generate_project",
]