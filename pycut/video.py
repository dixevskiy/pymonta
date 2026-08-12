import logging
import math
import re
from enum import Enum
from itertools import chain, count
from pathlib import Path

from ffmpeg.asyncio import FFmpeg

LOGGER = logging.getLogger(__name__)


class TextLocations(Enum):
    CENTER = "x=(w-tw)/2:y=(h-th)/2"
    BOTTOM_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"
    BOTTOM_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2+(h-th)/3"
    UPPER_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2-(h-th)/3"
    UPPER_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2-(h-th)/3"
    HORIZONTAL_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2"
    HORIZONTAL_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2"


class ImageLocations(Enum):
    CENTER = "x=(W-w)/2:y=(H-h)/2"
    BOTTOM_RIGHT = "x=(W-w)/2+(W-w)/2.5:y=(H-h)/2+(H-h)/3"
    BOTTOM_LEFT = "x=(W-w)/2-(W-w)/2.5:y=(H-h)/2+(H-h)/3"
    UPPER_RIGHT = "x=(W-w)/2+(W-w)/2.5:y=(H-h)/2-(H-h)/3"
    UPPER_LEFT = "x=(W-tw)/2-(W-w)/2.5:y=(H-h)/2-(H-h)/3"


def _time_converter(human_time: str) -> int:
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


class VideoText:
    def __init__(
        self,
        start_time: str,
        text: str,
        location: TextLocations,
        size: int = 34,
        /,
        font_color: str = "white",
        end_time: int | None = None,
        wraplenght: int = 32,
        text_align: str = "C",
        base_stream: str = "[overlayed]",
    ) -> None:
        """
        Place text in your video.

        Returns:
            FFmpeg instance for chaining.
        Confusing arguments:
            text_align can be: C=center, L=left, R=right.
            end_time calculates automatically based on length of text.
            font_color should be HEX to save your sanity.
        """
        self.start_time = _time_converter(start_time)
        self.location = location
        self.size = size
        self.wraplenght = wraplenght
        self.text_align = text_align
        self.base_stream = base_stream
        self.font_color = font_color
        # calculate end time based on average reading speed
        # average wpm is 150, average word length is 4, 150*4/60 = 10 symbols per second
        self.end_time = (
            self.start_time + math.ceil(len(text) / 10) if not end_time else end_time
        )

        # cli safeguard
        self.text = text.replace("'", "")

        # wrapping mechanism
        if len(text) > wraplenght:
            # preserve manually placed \n
            text = text.replace("\n", "@@ ")
            words = text.split()
            wrapped_string_build = []
            line_sum_symbols = 0
            for word in words:
                # preserve manually placed \n
                if "@@" in word:
                    word = word.replace("@@", "")
                    wrapped_string_build.append(f"{word}\n")
                    line_sum_symbols = 0
                    # skip, because we already processed word
                    continue
                # Next line if clause
                if len(word) + line_sum_symbols >= wraplenght:
                    wrapped_string_build.append("\n")
                    line_sum_symbols = 0
                line_sum_symbols += len(word)
                wrapped_string_build.append(word)
            self.text = " ".join(wrapped_string_build)

    def __str__(self):
        return f"{self.base_stream}drawtext=enable='between(t,{self.start_time},{self.end_time})':text='{self.text}':fontcolor={self.font_color}:text_align={self.text_align}:fontsize={self.size}:{self.location.value}[overlayed]"


class VideoImage:
    _id = count(1)

    def __init__(
        self,
        image_path: str,
        start_time: str,
        location: ImageLocations,
        size: int = 320,
        /,
        linked_text: VideoText | None = None,
        base_stream: str = "[overlayed]",
        end_time: int | None = None,
    ) -> None:
        """
        Create instance of VideoImage

        Strange arguments:
            start_time can be formatted as "1m20s", "1:20", "80", "1m20"
        """
        self.path = image_path
        self.start_time = _time_converter(start_time)
        self.location = location.value
        self.size = size
        self.base_stream = base_stream
        self.end_time = self.start_time + 5 if not end_time else end_time
        self.linked_text = None

        # total count of VideoImage instances
        self.image_index = next(self._id)

        # link image to provided text
        if linked_text:
            self.linked_text = linked_text
            self.start_time = linked_text.start_time
            self.end_time = linked_text.end_time

    def __str__(self):
        base = f"[{self.image_index}:v]scale={self.size}:-1[img];{self.base_stream}[img]overlay={self.location}:enable='between(t,{self.start_time},{self.end_time})'[overlayed]"
        if self.linked_text:
            return f"{base};{self.linked_text!s}"
        return base


class VideoTrim:
    def __init__(
        self,
        start_time: str,
        end_time: str,
        /,
        base_video_stream: str = "[overlayed]",
        base_audio_stream: str = "[overaudio]",
    ):
        self.start_time = _time_converter(start_time)
        self.end_time = _time_converter(end_time)
        self.base_stream = base_video_stream
        self.base_audio_stream = base_audio_stream

    def __str__(self):
        return f"{self.base_stream}trim=start={self.start_time}:end={self.end_time},setpts=PTS-STARTPTS[overlayed];{self.base_audio_stream}atrim=start={self.start_time}:end={self.end_time},asetpts=PTS-STARTPTS[overaudio]"


class VideoCut(VideoTrim):
    def __init__(
        self,
        start_time: str,
        end_time: str,
        /,
        base_video_stream: str = "[overlayed]",
        base_audio_stream: str = "[overaudio]",
    ):
        super().__init__(start_time, end_time, base_video_stream, base_audio_stream)

    def __str__(self):
        return f"{self.base_stream}select='not(between(t,{self.start_time},{self.end_time}))',setpts=N/FRAME_RATE/TB[overlayed];{self.base_audio_stream}aselect='not(between(t,{self.start_time},{self.end_time}))',asetpts=N/SR/TB[overaudio]"


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


async def compose(video_path: str, output_path: str, *filters) -> FFmpeg:
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
    trims_cnt = 0
    reencode_audio = False

    filters_seq = list(chain(filters))
    # To start filter chain the first one must use video as base
    filters_seq[0].base_stream = "[0:v]"

    for filter in filters:
        if isinstance(filter, VideoImage):
            ffmpeg = ffmpeg.input(filter.path)
        if isinstance(filter, VideoTrim):
            if trims_cnt == 0:
                filter.base_audio_stream = "[0:a]"
                reencode_audio = True
            trims_cnt += 1

    filter_complex = f"{';'.join(map(str, filters_seq))}"

    if not reencode_audio:
        ffmpeg = ffmpeg.output(
            output_path,
            acodec="copy",
            filter_complex=filter_complex,
            map=["[overlayed]", "0:a"],
        )
    else:
        ffmpeg = ffmpeg.output(
            output_path,
            acodec="aac",
            filter_complex=filter_complex,
            map=["[overlayed]", "[overaudio]"],
        )

    return ffmpeg


# async def main():
#     video = "whisper_test.mp4"
#     if Path("o.mp4").exists():
#         Path("o.mp4").unlink()

#     overlays = [
#         VideoTrim("11s", "19s"),
#         VideoImage(
#             "sig2.png",
#             "1",
#             ImageLocations.UPPER_RIGHT,
#             linked_text=VideoText(
#                 "1",
#                 "Это АРА!\nПрикольни реплика <3",
#                 TextLocations.HORIZONTAL_RIGHT,
#                 font_color="556B2F",
#             ),
#         ),
#         VideoImage(
#             "p1.jpg",
#             "1",
#             ImageLocations.BOTTOM_LEFT,
#             340,
#             linked_text=VideoText("0:0:1", "Это экспи!", TextLocations.HORIZONTAL_LEFT),
#         ),
#         VideoText("1s", "Я МОГУ ВСЕ!!!", TextLocations.BOTTOM_RIGHT),
#         VideoText("2s", "Действительно...", TextLocations.UPPER_LEFT),
#     ]

#     processed_video = await asyncio.create_task(
#         compose_video(video, "o.mp4", *overlays)
#     )
#     res = await asyncio.create_task(detect_silence_fragments(video))
#     print(res)
#     await asyncio.create_task(processed_video.execute())


# if __name__ == "__main__":
#     asyncio.run(main(), debug=True)
