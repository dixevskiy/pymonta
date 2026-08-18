"""
Speech-to-text transcription and keyword search using Whisper.

This module provides functions to:
- Transcribe a video/audio file using `whisper_timestamped`.
- Convert transcription segments to SRT subtitle format.
- Search for keywords in the transcription and return their timestamps.

The module relies on the `whisper_timestamped` package, which adds word-level
timestamps to OpenAI's Whisper.
"""

import logging
from collections.abc import Sequence
from fnmatch import fnmatch
from typing import Any

import whisper_timestamped as whisper

LOGGER = logging.getLogger(__name__)


def transcribe_file(
    file_path: str,
    language: str,
    model_size: str = "small",
) -> object:
    """Transcribe an audio/video file using Whisper with timestamped segments.

    The function loads the specified Whisper model, runs transcription on the
    given file, and returns the segments with start/end timestamps.

    Args:
        file_path: Path to the media file (supports formats that Whisper can read).
        language: Language code (e.g., `"en"`, `"fr"`, `"ru"`).
        model_size: Whisper model size (`"tiny"`, `"base"`, `"small"`,
            `"medium"`, `"large"`). Defaults to `"small"`.

    Returns:
        A list of segment dictionaries, each containing:
        - `"text"`: transcribed text for the segment.
        - `"start"`: start time in seconds.
        - `"end"`: end time in seconds.
        - (other metadata from Whisper).

    Raises:
        FileNotFoundError: If `file_path` does not exist.
        RuntimeError: If the model fails to load or transcribe.
    """
    LOGGER.info("Starting video transcribing process... This can take a while.")
    model = whisper.load_model(model_size)
    result = model.transcribe(file_path, language=language)
    LOGGER.info("Transcribing process finished!")
    return result["segments"]


def _format_srt_time(total_seconds: float) -> str:
    """Convert a time in seconds to SRT timestamp format.

    The SRT format uses `HH:MM:SS,mmm` (with milliseconds separated by a comma).

    Args:
        total_seconds: Time in seconds (can be fractional).

    Returns:
        A string formatted as `HH:MM:SS,mmm` (e.g., `"00:01:23,456"`).

    Note:
        The rounding handles edge cases where milliseconds reach 1000, ensuring
        correct carryover to seconds/minutes/hours.
    """
    hours = int(total_seconds // 3600)
    remaining = total_seconds % 3600
    minutes = int(remaining // 60)
    seconds = remaining % 60

    secs_int = int(seconds)
    millis = round((seconds - secs_int) * 1000)

    if millis == 1000:
        millis = 0
        secs_int += 1
        if secs_int == 60:
            secs_int = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1

    return f"{hours:02d}:{minutes:02d}:{secs_int:02d},{millis:03d}"


def generate_srt(transcription: Sequence[dict[str, Any]]) -> str:
    """Generate an SRT subtitle file content from a Whisper transcription.

    Each segment is converted to an SRT entry with an index, timestamps, and text.

    Args:
        transcription: List of segment dictionaries (as returned by
            `transcribe_file`). Each must have `"text"`, `"start"`, and `"end"`.

    Returns:
        A string containing the complete SRT content, ready to be written to a
        `.srt` file.

    Example:
        >>> srt_content = generate_srt(segments)
        >>> with open("subtitles.srt", "w") as f:
        ...     f.write(srt_content)
    """
    preprocess = []
    for idx, segment in enumerate(transcription, start=1):
        text = segment["text"]
        srt_start = _format_srt_time(segment["start"])
        srt_end = _format_srt_time(segment["end"])
        preprocess.append(f"{idx}\n{srt_start} --> {srt_end}\n{text}\n")
    return "\n".join(preprocess)


def find_keywords(
    transcription: Sequence[dict[str, Any]],
    keyword: str,
) -> list[tuple[int, int]] | None:
    """Find all occurrences of a keyword in the transcription and return timestamps.

    The function performs a case-sensitive, whole word search on transcription.
    Look note for example.

    Args:
        transcription: List of segment dictionaries (as returned by
            `transcribe_file`). Each must have `"text"`, `"start"`, and `"end"`.
        keyword: The word or phrase to search for.

    Returns:
        A list of `(start, end)` tuples in seconds for each matching segment,
        or `None` if no matches are found.

    Note:
        The matching is done with `fnmatch(text, f"*{keyword}*")`, which means:
        - The keyword can appear anywhere within the segment text.
        - The match is **case-sensitive**.
        - It does not require word boundaries, so "montage" would match "montages".
        If you need case-insensitive matching, convert both strings to lower case
        before calling.
    """
    result = []
    for segment in transcription:
        text = segment["text"]
        if fnmatch(text, f"*{keyword}*"):
            result.append((segment["start"], segment["end"]))
    return result if result else None
