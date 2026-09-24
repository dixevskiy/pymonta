"""
a Python video editing toolkit for tech nerds.

pymonta provides an abstraction over FFmpeg's filter graphs. It allows you
to compose complex video/audio edits using simple, chainable filters without
writing raw FFmpeg commands.
Import speech modules manually `pymonta.speech`.

Main features:
- Declarative filter composition using `Pipe` and `Filter` abstractions.
- Common edits: trimming, cutting, overlaying text/images, adjusting volume,
  mixing audio, burning subtitles, and more.
- Speech transcription with Whisper (timestamped) and keyword search.
- JSON serialization utilities for saving/loading edit configurations.
- Project initialisation via CLI to get started quickly.

Subpackages:
- `pymonta.video.classes` : Core classes
- `pymonta.video.functions` : High-level functions
- `pymonta.jsons` : JSON helpers
- `pymonta.speech` : Whisper transcription
- `pymonta.proj_funcs` : Project generator
"""

# Import core types and functions for easy access
from pymonta.jsons import deserialize, is_serializable, serialize

# from pymonta.speech import transcribe_file, generate_srt, find_keywords
from pymonta.proj_funcs import generate_project
from pymonta.video.abstractions import (
    Clip,
    ClipConcat,
    ClipSpeed,
    ClipTransition,
    Cut,
    Scene,
    Trim,
    Video,
)
from pymonta.video.filters import (
    ChangeVolume,
    Filter,
    HardSubtitles,
    InsertAudio,
    Locations,
    Media,
    MuteRange,
    NewAudio,
    Pipe,
    RemoveAudio,
    VideoAdjustments,
    VideoOverlay,
    audio_filter,
    video_filter,
)
from pymonta.video.functions import (
    bake_filters,
    compose,
    detect_silence_fragments,
    digest_pillow,
    get_duration,
    render_text,
)

__all__ = [
    "ChangeVolume",
    "Clip",
    "ClipConcat",
    "ClipSpeed",
    "ClipTransition",
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
    "Scene",
    "Trim",
    "Video",
    "VideoAdjustments",
    "VideoOverlay",
    "audio_filter",
    "bake_filters",
    "compose",
    "deserialize",
    "detect_silence_fragments",
    "digest_pillow",
    "generate_project",
    "get_duration",
    "is_serializable",
    "render_text",
    "serialize",
    "video_filter",
]
