"""
FFmpeg filter and pipe abstractions for video/audio composition.

This module defines the building blocks for constructing complex FFmpeg filter
graphs in a Pythonic way. It provides:
- `Pipe`: a chainable representation of a stream with filters.
- `Filter`: base class for all filters (video/audio adjustments, overlays, etc.).
- `Media`: mixin for filters that reference external files (images, audio).
- Concrete filter classes: `VideoText`, `VideoImage`, `VideoAdjustments`,
  `ChangeVolume`, `InsertAudio`, `HardSubtitles`, and more.
- Utility functions like `_time_converter` for human‑readable time strings.
- Convenience factories (`Cut`, `Trim`) that return paired video/audio filters.

The classes are designed to work with the `compose` function from the main
module, building a filter_complex string via `Pipe.combine_filter()`.
"""

import math
from abc import ABC, abstractmethod
from enum import Enum
from string import Template
from typing import Optional, Sequence, Union


class TextLocations(Enum):
    """Predefined positions for text overlay (used by `VideoText`).

    Each value is an FFmpeg `drawtext` position expression.
    """

    CENTER = "x=(w-tw)/2:y=(h-th)/2"
    BOTTOM_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"
    BOTTOM_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2+(h-th)/3"
    UPPER_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2-(h-th)/3"
    UPPER_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2-(h-th)/3"
    HORIZONTAL_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2"
    HORIZONTAL_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2"
    HORIZONTAL_UP = "x=(w-tw)/2:y=(h-th)/2-(h-th)/3"
    HORIZONTAL_DOWN = "x=(w-tw)/2:y=(h-th)/2+(h-th)/3"


class ImageLocations(Enum):
    """Predefined positions for image overlay (used by `VideoImage`).

    Each value is an FFmpeg `overlay` position expression.
    """

    CENTER = "x=(W-w)/2:y=(H-h)/2"
    BOTTOM_RIGHT = "x=(W-w)/2+(W-w)/2.5:y=(H-h)/2+(H-h)/3"
    BOTTOM_LEFT = "x=(W-w)/2-(W-w)/2.5:y=(H-h)/2+(H-h)/3"
    UPPER_RIGHT = "x=(W-w)/2+(W-w)/2.5:y=(H-h)/2-(H-h)/3"
    UPPER_LEFT = "x=(W-w)/2-(W-w)/2.5:y=(H-h)/2-(H-h)/3"
    HORIZONTAL_RIGHT = "x=(W-w)/2+(W-w)/3:y=(H-h)/2"
    HORIZONTAL_LEFT = "x=(W-w)/2-(W-w)/3:y=(H-h)/2"
    HORIZONTAL_UP = "x=(W-w)/2:y=(H-h)/2-(H-h)/3"
    HORIZONTAL_DOWN = "x=(W-w)/2:y=(H-h)/2+(H-h)/3"


class Pipe:
    """A node in a filter graph, representing a stream with optional filters.

    `Pipe` objects form a doubly-linked list: each pipe knows its input pipe
    and output pipe. The `combine_filter()` method recursively builds the
    complete filter string by chaining `.apply()` outputs.

    Attributes:
        stream_name (str): The label for this pipe (e.g., `"vout"`).
        filter (Filter | None): The filter applied at this node.
        _input_pipe (Pipe | None): The preceding pipe in the chain.
        _output_pipe (Pipe | None): The following pipe in the chain.
    """

    def __init__(
        self,
        stream_name: str,
        filter: Optional["Filter"] = None,
        input_pipe: Optional["Pipe"] = None,
        output_pipe: Optional["Pipe"] = None,
    ) -> None:
        """Initialize a pipe with an optional filter and neighbouring pipes.

        Args:
            stream_name: The label for this pipe (e.g., `"vout"`).
            filter: The filter to apply at this node (if any).
            input_pipe: The pipe that feeds into this one.
            output_pipe: The pipe that this one feeds into.

        Note:
            If `input_pipe` or `output_pipe` are provided, the bidirectional
            links are established automatically.
        """
        self.filter = filter
        self.stream_name = stream_name
        self._input_pipe = input_pipe
        self._output_pipe = output_pipe

        if output_pipe is not None:
            output_pipe._input_pipe = self
        if input_pipe is not None:
            input_pipe._output_pipe = self

    @property
    def input(self) -> str:
        """Get the stream label for the input side of this pipe chain.

        Returns:
            The stream name of the input pipe, if present; otherwise,
            the pipe's own `stream_name`.
        """
        if self._input_pipe:
            return self._input_pipe.output
        return self.stream_name

    @property
    def output(self) -> str:
        """Get the stream label for the output side of this pipe chain.

        Returns:
            The stream name of the output pipe, if present; otherwise,
            the pipe's own `stream_name`.
        """
        if self._output_pipe:
            return self._output_pipe.output
        return self.stream_name

    def combine_filter(self) -> str:
        """Recursively build the filter string for this pipe and all subsequent pipes.

        Returns:
            A complete filter_complex string (e.g., `"[0:v]drawtext=...;[vout]"`).
        """
        res = ""
        if self.filter:
            placeholders = {
                "input": self.input,
                "output": self.output,
            }
            res = self.filter.apply().safe_substitute(**placeholders)
        if self._output_pipe:
            res += self._output_pipe.combine_filter()
        return res

    def join(self, pipe: "Pipe") -> "Pipe":
        """Link this pipe as the output of the given pipe.

        Args:
            pipe: The pipe that will feed into this one.

        Returns:
            The `pipe` argument (for chaining).
        """
        self._input_pipe = pipe
        pipe._output_pipe = self
        return pipe

    def get_all_media_paths(self) -> list[str]:
        """Collect all external media file paths referenced in this pipe chain.

        Returns:
            A list of paths (from `Media` filters) in the chain.
        """
        res = []
        if self.filter and isinstance(self.filter, Media):
            res = [self.filter.path]
        if self._output_pipe:
            res += self._output_pipe.get_all_media_paths()
        return res


class Media(ABC):
    """Mixin for filters that reference an external media file (image, audio).

    Subclasses must implement `path` and `set_id()` to assign a unique stream ID.
    """

    @property
    @abstractmethod
    def path(self) -> str:
        """The filesystem path to the media file."""
        pass

    @abstractmethod
    def set_id(self, id: int) -> None:
        """Assign a stream index (ID) for use in filter graphs.

        Args:
            id: The unique integer ID (e.g., for `[id:v]` or `[id:a]`).
        """
        pass


class Filter(ABC):
    """Base class for all filter operations.

    Subclasses must implement `apply()` to return a `Template` with
    placeholders `$input` and `$output`, and `stream_type` to indicate
    whether the filter operates on video or audio.
    """

    @abstractmethod
    def apply(self) -> Template:
        """Return the filter string template.

        The template must contain `$input` and `$output` placeholders.
        """
        pass

    @property
    @abstractmethod
    def stream_type(self) -> str:
        """Return `"video"` or `"audio"`."""
        pass


def _time_converter(human_time: str) -> int:
    """Convert a human‑readable time string to seconds (integer).

    Supported formats:
        - `"0:1:20"` → 80 seconds
        - `"1m20s"` → 80 seconds
        - `"1h2m3s"` → 3723 seconds
        - `"80"` → 80 seconds

    Args:
        human_time: The time string.

    Returns:
        Total seconds as an integer.

    Raises:
        ValueError: If the format is unrecognised.
    """
    human_time = human_time.replace("s", "")
    if ":" in human_time:
        hours, min, sec = human_time.split(":")
        return int(hours) * 3600 + int(min) * 60 + int(sec)
    if "m" in human_time and "h" not in human_time:
        min, sec = human_time.split("m")
        return int(min) * 60 + int(sec)
    if "h" in human_time:
        hours, min, sec = human_time.replace("h", ":").replace("m", ":").split(":")
        return int(hours) * 3600 + int(min) * 60 + int(sec)
    return int(human_time)


class VideoText(Filter):
    """Filter to overlay text on a video stream.

    The text appears between `start_time` and an automatically computed
    `end_time` (based on text length, ~10 chars/second), unless overridden.
    Supports manual newline (`\n`) and automatic word wrapping.
    """

    def __init__(
        self,
        start_time: str,
        text: str,
        location: TextLocations,
        size: int = 34,
        /,
        font_color: str = "white",
        end_time: Optional[int] = None,
        wraplenght: int = 32,
        text_align: str = "C",
    ) -> None:
        """Initialise a text overlay filter.

        Args:
            start_time: When the text appears (human‑readable).
            text: The text to display.
            location: Position on screen (from `TextLocations`).
            size: Font size in pixels.
            font_color: Colour name or hex code (e.g., `"#FF0000"`).
            end_time: Optional override for when text disappears
                (if not given, estimated from text length).
            wraplenght: Max chars per line before wrapping.
            text_align: Alignment: `"C"` (center), `"L"` (left), `"R"` (right).

        Note:
            - The text is automatically wrapped to `wraplenght` characters.
            - Manual newlines (`\n`) are preserved.
            - Colons (`:`) are escaped for FFmpeg compatibility.
        """
        self.start_time = _time_converter(start_time)
        self.location = location
        self.size = size
        self.wraplenght = wraplenght
        self.text_align = text_align
        self.font_color = font_color
        # estimate reading time: average wpm=150, avg word length=4 -> 10 chars/sec
        self.end_time = (
            self.start_time + math.ceil(len(text) / 10) if end_time is None else end_time
        )

        # Strip single quotes (guard for FFmpeg)
        self.text = text.replace("'", "")

        # Wrap long lines
        if len(text) > wraplenght:
            text = text.replace("\n", "@@ ")  # preserve manual breaks
            words = text.split()
            wrapped_lines = []
            line_sum = 0
            for word in words:
                if "@@" in word: # preserve manual breaks
                    word = word.replace("@@", "")
                    wrapped_lines.append(f"{word}\n")
                    line_sum = 0
                    continue
                if len(word) + line_sum >= wraplenght:
                    wrapped_lines.append("\n")
                    line_sum = 0
                line_sum += len(word)
                wrapped_lines.append(word)
            self.text = " ".join(wrapped_lines)

        # Escape colons for FFmpeg
        self.text = self.text.replace(":", r"\:")

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(
            f"[$input]drawtext=enable='between(t,{self.start_time},{self.end_time})':text='{self.text}':fontcolor={self.font_color}:text_align={self.text_align}:fontsize={self.size}:{self.location.value}[$output];"
        )


class VideoImage(Filter, Media):
    """Filter to overlay an image on a video stream.

    The image is scaled to a given size, and appears between `start_time`
    and `end_time`. It uses the `overlay` filter with premultiplied alpha.
    """

    def __init__(
        self,
        image_path: str,
        start_time: str,
        location: ImageLocations,
        size: int = 320,
        /,
        end_time: Optional[str] = None,
    ) -> None:
        """Initialise an image overlay filter.

        Args:
            image_path: Path to the image.
            start_time: When the image appears (human‑readable).
            location: Position on screen (from `ImageLocations`).
            size: Width in pixels; height is scaled to keep aspect ratio.
            end_time: When the image disappears (human‑readable).
                If not given, defaults to start + 5 seconds.
        """
        self.img_path = image_path
        self.start_time = _time_converter(start_time)
        self.location = location.value
        self.size = size
        self.end_time = (
            self.start_time + 5 if end_time is None else _time_converter(end_time)
        )
        self.image_index = None

    @property
    def path(self) -> str:
        return self.img_path

    def set_id(self, id: int) -> None:
        self.image_index = id

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        if self.image_index is None:
            raise RuntimeError(f"Insertion ID for image {self.path} was not set.")
        return Template(
            f"[{self.image_index}:v]scale={self.size}:-2,format=rgba[img];[$input][img]overlay={self.location}:enable='between(t,{self.start_time},{self.end_time})':alpha=premultiplied[$output];"
        )


class _VideoTrim(Filter):
    """Internal filter to trim a video stream (keep a segment)."""

    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(
            f"[$input]trim=start={self.start_time}:end={self.end_time},setpts=PTS-STARTPTS[$output];"
        )


class _AudioTrim(Filter):
    """Internal filter to trim an audio stream (keep a segment)."""

    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        return Template(
            f"[$input]atrim=start={self.start_time}:end={self.end_time},asetpts=PTS-STARTPTS[$output];"
        )


class _VideoCut(Filter):
    """Internal filter to cut (remove) a segment from a video stream."""

    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(
            f"[$input]select='not(between(t,{self.start_time},{self.end_time}))',setpts=N/FRAME_RATE/TB[$output];"
        )


class _AudioCut(Filter):
    """Internal filter to cut (remove) a segment from an audio stream."""

    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        return Template(
            f"[$input]aselect='not(between(t,{self.start_time},{self.end_time}))',asetpts=N/SR/TB[$output];"
        )


class Cut:
    """Factory that returns a tuple of audio and video cut filters.

    The returned filters remove the specified time range from both streams.
    """

    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioCut, _VideoCut]:
        """Create a pair of `_AudioCut` and `_VideoCut` filters.

        Args:
            start_time: Start of the segment to remove (human‑readable).
            end_time: End of the segment to remove (human‑readable).

        Returns:
            A tuple `(_AudioCut, _VideoCut)`.
        """
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioCut(s, e), _VideoCut(s, e))


class Trim:
    """Factory that returns a tuple of audio and video trim filters.

    The returned filters keep only the specified time range.
    """

    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioTrim, _VideoTrim]:
        """Create a pair of `_AudioTrim` and `_VideoTrim` filters.

        Args:
            start_time: Start of the segment to keep (human‑readable).
            end_time: End of the segment to keep (human‑readable).

        Returns:
            A tuple `(_AudioTrim, _VideoTrim)`.
        """
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioTrim(s, e), _VideoTrim(s, e))


class ChangeVolume(Filter):
    """Adjust the volume of an audio stream by a gain factor."""

    def __init__(self, volume: float):
        """Initialise a volume filter.

        Args:
            volume: Gain factor (e.g., 0.5 = half, 2 = double).
        """
        self.volume = volume

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        return Template(f"[$input]volume={self.volume}[$output];")


class VideoAdjustments(Filter):
    """Adjust brightness, contrast, gamma, and saturation of a video stream."""

    def __init__(
        self,
        brightness: Optional[float] = None,
        gamma: Optional[float] = None,
        contrast: Optional[float] = None,
        saturation: Optional[float] = None,
    ) -> None:
        """Initialise a video adjustment filter.

        Args:
            brightness: Adjust brightness (0.0–1.0, default 0).
            gamma: Adjust gamma (default 1.0).
            contrast: Adjust contrast (default 1.0).
            saturation: Adjust saturation (default 1.0).

        Note:
            All parameters are optional; omitted values stay at their defaults.
        """
        self.b = str(brightness) if brightness is not None else "0"
        self.g = str(gamma) if gamma is not None else "1"
        self.c = str(contrast) if contrast is not None else "1"
        self.s = str(saturation) if saturation is not None else "1"

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(
            f"[$input]eq=brightness={self.b}:contrast={self.c}:gamma={self.g}:saturation={self.s}[$output];"
        )


class NewAudio(Media, Filter):
    """Add a new audio track mixed with the existing audio.

    This filter inserts a background track at full length, mixing with the
    original audio at a specified volume.
    """

    def __init__(self, audio_path: str, volume: float):
        """Initialise a new audio overlay.

        Args:
            audio_path: Path to the audio file.
            volume: Gain factor for the new track.

        Note:
            The stream ID must be set via `set_id()` before `apply()` if used manually.
        """
        self.audio_path = audio_path
        self.volume = volume
        self.stream_id = None

    @property
    def path(self) -> str:
        return self.audio_path

    def set_id(self, id: int) -> None:
        self.stream_id = id

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        if self.stream_id is None:
            raise RuntimeError(f"Insertion ID for audio {self.path} was not set.")
        return Template(
            f"[{self.stream_id}:a]volume={self.volume}[{self.stream_id}_edit];[$input][{self.stream_id}_edit]amix=inputs=2:duration=first[$output];"
        )


class InsertAudio(NewAudio):
    """Insert an audio clip at a specific time range, mixed with the original.

    The clip is placed starting at `start_time` and lasts until `end_time`.
    """

    def __init__(
        self,
        audio_path: str,
        volume: float,
        start_time: str,
        end_time: str,
    ):
        """Initialise an inserted audio clip.

        Args:
            audio_path: Path to the audio file.
            volume: Gain factor for the inserted clip.
            start_time: When the clip starts (human‑readable).
            end_time: When the clip ends (human‑readable).

        Note:
            The stream ID must be set via `set_id()` before `apply()` if used manually.
        """
        super().__init__(audio_path, volume)
        self.start_time = _time_converter(start_time)
        self.end_time = _time_converter(end_time)

    def apply(self) -> Template:
        if self.stream_id is None:
            raise RuntimeError(f"Insertion ID for audio {self.path} was not set.")
        return Template(
            f"[{self.stream_id}:a]atrim=0:{self.end_time},adelay={self.start_time * 1000}:all=1,volume={self.volume}[{self.stream_id}_inserted];[$input][{self.stream_id}_inserted]amix=inputs=2:duration=first[$output];"
        )


class RemoveAudio(Filter):
    """Completely remove the original audio track (mute it)."""

    def apply(self) -> Template:
        return Template("[$input]volume=0[$output];")

    @property
    def stream_type(self) -> str:
        return "audio"


class MuteRange(Filter):
    """Mute the audio during a specific time range."""

    def __init__(self, start_time: str, end_time: str) -> None:
        """Initialise a mute range filter.

        Args:
            start_time: Start of the mute period (human‑readable).
            end_time: End of the mute period (human‑readable).
        """
        self.start_time = _time_converter(start_time)
        self.end_time = _time_converter(end_time)

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        return Template(
            f"[$input]volume=enable='between(t,{self.start_time},{self.end_time})':volume=0[$output];"
        )


class HardSubtitles(Filter):
    """Burn subtitles into the video."""

    def __init__(self, subtitles_path: str) -> None:
        """Initialise a subtitles filter.

        Args:
            subtitles_path: Path to the subtitle file (e.g., `subs.srt`).
        """
        self.subtitles = subtitles_path

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(f"[$input]subtitles={self.subtitles}[$output];")


class _MixVideoStreams(Filter):
    """Internal filter to overlay multiple video streams on a base canvas.

    This is planned to be used by the `Pipe` system to combine several video inputs.
    """

    def __init__(self, streams: list[str]) -> None:
        """Initialise a mixer for video streams.

        Args:
            streams: List of stream labels (e.g., `["0:v", "1:v"]`).
        """
        self.streams = streams

    def apply(self) -> Template:
        n = len(self.streams)
        if n == 0:
            return Template("[$input]null[$output];")

        filter_parts = []
        current = "$input"
        for i, stream in enumerate(self.streams):
            next_label = f"ov{i}"
            filter_parts.append(f"[{current}][{stream}]overlay[{next_label}];")
            current = next_label

        filter_parts.append(f"[{current}]null[$output];")
        return Template("".join(filter_parts))

    @property
    def stream_type(self) -> str:
        return "video"


class _MixAudioStreams(Filter):
    """Internal filter to mix multiple audio streams together.
    
    This is planned to be used by the `Pipe` system to combine several video inputs.
    """

    def __init__(self, streams: list[str]) -> None:
        """Initialise a mixer for audio streams.

        Args:
            streams: List of stream labels (e.g., `["0:a", "1:a"]`).
        """
        self.streams = streams

    def apply(self) -> Template:
        if len(self.streams) == 1:
            return Template(f"[{self.streams[0]}]anull[$output];")
        inputs = "".join(f"[{name}]" for name in self.streams)
        return Template(f"{inputs}amix=inputs={len(self.streams)}[$output];")

    @property
    def stream_type(self) -> str:
        return "audio"