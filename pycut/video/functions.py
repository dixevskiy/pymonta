import logging
import re
from collections.abc import Sequence
from itertools import chain
from pathlib import Path

import cv2
from ffmpeg.asyncio import FFmpeg
from ffmpeg.progress import Progress

from pycut.video.classes import (
    Filter,
    Media,
    Pipe,
    _MixAudioStreams,
    _MixVideoStreams,
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
            vn=None,
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


async def get_duration(video_path: str) -> int:
    v = cv2.VideoCapture(video_path)
    frames = v.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = v.get(cv2.CAP_PROP_FPS)
    return round(frames / fps)

## Scheduled on rewriting
# def compose_piped(
#     video_path: str,
#     output_path: str,
#     video_pipes: Sequence[Pipe],
#     audio_pipes: Sequence[Pipe],
#     **ffmpeg_output_args,
# ) -> FFmpeg:

#     LOGGER.info(f"Starting piped composition process for {video_path}.")

#     if Path(output_path).exists():
#         raise RuntimeError(
#             "Output file already exists! Handle it manually. Halting video composing."
#         )

#     ffmpeg = FFmpeg().input(video_path)

#     @ffmpeg.on("progress")
#     def on_progress(progress: Progress):
#         LOGGER.info(
#             f"Working on {progress.frame} frame, current fps = {progress.fps}, output size: ~{progress.size / 1024 / 1024}MB"
#         )

#     for pipe in chain(video_pipes, audio_pipes):
#         for path in pipe.get_all_media_paths():
#             ffmpeg.input(path)

#     output_video_streams = [pipe.output for pipe in video_pipes]
#     last_stream_name = video_pipes[$outpu-2t].stream_name
#     vout = Pipe("vout").join(
#         Pipe(last_stream_name, _MixVideoStreams(output_video_streams))
#     )
#     video_filters = (
#         "".join([pipe.combine_filter() for pipe in video_pipes]) + vout.combine_filter()
#     )

#     output_audio_streams = [pipe.output for pipe in audio_pipes]
#     aout = Pipe("aout").join(Pipe("", _MixAudioStreams(output_audio_streams)))
#     audio_filters = (
#         "".join([pipe.combine_filter() for pipe in audio_pipes]) + aout.combine_filter()
#     )

#     filters = video_filters + audio_filters
    
#     LOGGER.debug(
#         f"Recieved: {len(video_pipes)} video pipes and {len(audio_pipes)} audio pipes.\nComposed to {filters}. \nStream name for glueing used: {last_stream_name}\n Custom ffmpeg args is: {ffmpeg_output_args}"
#     )

#     ffmpeg = ffmpeg.output(
#         output_path,
#         acodec="aac",
#         filter_complex=filters,
#         map=["[vout]", "[aout]"],
#         **ffmpeg_output_args,
#     )
#     return ffmpeg


def compose(
    video_path: str,
    output_path: str,
    video_filters: Sequence[Filter],
    audio_filters: Sequence[Filter],
    **ffmpeg_output_flags,
) -> FFmpeg:
    """
    High level video composition function

    Returns:
        ffmpeg instance which can be further modified
    """
    if Path(output_path).exists():
        raise RuntimeError(
            "Output file already exists! Handle it manually. Halting video composing."
        )
    LOGGER.info(f"Starting composition process for {video_path}.")
    ffmpeg = FFmpeg().input(video_path)
    # pipelines
    vout = Pipe("vout")
    aout = Pipe("aout")
    # flags
    audio_changed = False
    video_changed = False
    for filter in chain(video_filters, audio_filters):
        if isinstance(filter, Media):
            ffmpeg.input(filter.path)
    for filter in chain(reversed(video_filters), reversed(audio_filters)):
        if filter.stream_type == "audio":
            aout = aout.join(Pipe("0:a", filter))
            audio_changed = True
        if filter.stream_type == "video":
            vout = vout.join(Pipe("0:v", filter))
            video_changed = True

    filter_complex = f"{vout.combine_filter()}{aout.combine_filter()}"

    acodec = "aac" if audio_changed else "copy"
    astream = "[aout]" if audio_changed else "0:a"
    vstream = "[vout]" if video_changed else "0:v"

    LOGGER.debug(
        f"filter: {filter_complex}\n- video_output:{vstream}\n- audio_output:{astream}, audio_codec:{acodec}"
    )

    ffmpeg = ffmpeg.output(
        output_path,
        acodec=acodec,
        filter_complex=filter_complex,
        map=[vstream, astream],
        **ffmpeg_output_flags,
    )

    @ffmpeg.on("progress")
    def on_progress(progress: Progress):
        LOGGER.info(
            f"Working on {progress.frame} frame, current fps = {progress.fps}, output size: ~{progress.size / 1024 / 1024}MB"
        )

    return ffmpeg
