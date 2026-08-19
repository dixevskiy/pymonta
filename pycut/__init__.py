"""
a Python video editing toolkit for tech nerds.

pycut provides an abstraction over FFmpeg's filter graphs. It allows you
to compose complex video/audio edits using simple, chainable filters without
writing raw FFmpeg commands.
Import speech modules manually.

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
from pycut.jsons import is_serializable, serialize, unserialize

# from pycut.speech import transcribe_file, generate_srt, find_keywords
from pycut.proj_funcs import generate_project
from pycut.video.classes import (
    ChangeSpeed,
    ChangeVolume,
    Cut,
    Filter,
    HardSubtitles,
    InsertAudio,
    Locations,
    Media,
    MuteRange,
    NewAudio,
    Pipe,
    RemoveAudio,
    Trim,
    VideoAdjustments,
    VideoOverlay,
    audio_filter,
    video_filter,
)
from pycut.video.functions import (
    bake_filters,
    compose,
    detect_silence_fragments,
    digest_pillow,
    get_duration,
    render_text,
)

__all__ = [
    "ChangeSpeed",
    "ChangeVolume",
    "Cut",
    "Filter",
    "HardSubtitles",
    "InsertAudio",
    "Locations",
    "Media",
    "MuteRange",
    "NewAudio",
    "Pipe",
    "RemoveAudio",
    "Trim",
    "VideoAdjustments",
    "VideoOverlay",
    "audio_filter",
    "bake_filters",
    "compose",
    "detect_silence_fragments",
    "digest_pillow",
    "generate_project",
    "get_duration",
    "is_serializable",
    "render_text",
    "serialize",
    "unserialize",
    "video_filter",
]
