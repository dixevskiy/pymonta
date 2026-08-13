import logging
import re
from pathlib import Path

from ffmpeg.asyncio import FFmpeg

from pycut.video.classes import (
    Filter,
    ImageLocations,
    Media,
    Pipe,
    TextLocations,
    VideoImage,
    VideoText,
    Cut
)

LOGGER = logging.getLogger(__name__)


async def detect_silence_fragments(
    video_path: str, silence_threshold=-40, min_duration=5
):
    ffmpeg = (
        FFmpeg()
        .input(video_path)
        .output(
            "-",
            af=f"silencedetect=noise={silence_threshold}dB:d={min_duration},ametadata=mode=print:file=silence_metadata.txt",
            f="null",
        )
    )
    await ffmpeg.execute()
    return _parse_silence_metadata("silence_metadata.txt")


def _parse_silence_metadata(filepath):
    """
    Parse ffmpeg's ametadata output to get silence intervals in seconds.
    Returns list of (start, end) tuples (floats in seconds).
    """
    with open(filepath, "r") as f:
        lines = f.readlines()

    silences = []
    current_start = None

    for line in lines:
        # Look for silence_start: value
        start_match = re.search(r"silence_start=([\d.]+)", line)
        if start_match:
            current_start = float(start_match.group(1))
        # Look for silence_end: value (which comes after the start)
        end_match = re.search(r"silence_end=([\d.]+)", line)
        if end_match and current_start is not None:
            end = float(end_match.group(1))
            silences.append((current_start, end))
            current_start = None

    return silences


async def compose(video_path: str, output_path: str, *filters: Filter) -> FFmpeg:
    """
    High level video composition function

    Returns:
        ffmpeg instance which can be further modified
    """
    if Path(output_path).exists():
        raise RuntimeError(
            "Output file already exists! Handle it manually. Halting video composing."
        )
    ffmpeg = FFmpeg().input(video_path)
    # pipelines
    vout = Pipe("vout")
    aout = Pipe("aout")
    # flags
    audio_changed = False
    for filter in filters:
        if isinstance(filter, Media):
            ffmpeg.input(filter.path)
        if filter.stream_type == "audio":
            aout = aout.join(Pipe("0:a", filter))
            audio_changed = True
        if filter.stream_type == "video":
            vout = vout.join(Pipe("0:v", filter))

    filter_complex = "".join([vout.combine_filter(), aout.combine_filter()])

    acodec = "aac" if audio_changed else "copy"
    astream = "[aout]" if audio_changed else "0:a"

    print(filter_complex)

    ffmpeg = ffmpeg.output(
        output_path,
        acodec=acodec,
        filter_complex=filter_complex,
        map=["[vout]", astream],
    )

    return ffmpeg


import asyncio


async def main():
    video = "whisper_test.mp4"
    if Path("o.mp4").exists():
        Path("o.mp4").unlink()

    edits = [
        # _VideoTrim(1, 5),
        *Cut("11s", "19s"),
        VideoText("1s", "Hi!", TextLocations.HORIZONTAL_UP),
        VideoImage("sig2.png", "1s", ImageLocations.HORIZONTAL_DOWN),
        # _AudioTrim(1, 5),
    ]
    bake = await compose(video, "o.mp4", *edits)
    await bake.execute()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
