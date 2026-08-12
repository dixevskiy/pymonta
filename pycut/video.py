import logging
import math
import re
from abc import ABC, abstractmethod
from enum import Enum
from itertools import count
from pathlib import Path
from string import Template

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


class Pipe:
    media_type: str = "generic"

    def __init__(
        self,
        stream_name: str,
        filter: Filter | None = None,
        input_pipe: Pipe | None = None,
        output_pipe: Pipe | None = None,
    ) -> None:
        self.filter = filter
        self.stream_name = stream_name
        self._input_pipe = input_pipe
        self._output_pipe = output_pipe

        # link pipes both ways
        if output_pipe is not None:
            output_pipe._input_pipe = self
        if input_pipe is not None:
            input_pipe._output_pipe = self

    @property
    def input(self):
        if self._input_pipe:
            return self._input_pipe.output
        return self.stream_name

    @property
    def output(self):
        if self._output_pipe:
            return self._output_pipe.output
        return self.stream_name

    def combine_filter(self) -> str:
        res = ""
        if self.filter:
            # Build placeholder names like "video_input", "audio_output"
            prefix = self.media_type
            placeholders = {
                f"{prefix}_input": self.input,
                f"{prefix}_output": self.output,
            }
            res = self.filter.apply().safe_substitute(**placeholders)
        if self._output_pipe:
            res += self._output_pipe.combine_filter()
        return res

    def join(self, pipe: Pipe) -> Pipe:
        self._input_pipe = pipe
        pipe._output_pipe = self
        return pipe

    def change_output_stream(self, new_stream_name) -> None:
        if self._output_pipe:
            self._output_pipe.stream_name = new_stream_name
            self._output_pipe.change_output_stream(new_stream_name)
        else:
            self.stream_name = new_stream_name


class VideoPipe(Pipe):
    media_type = "video"
    # You can enforce filter type here if desired:
    # def __init__(self, *args, filter: VideoFilter = None, **kwargs):
    #     super().__init__(*args, filter=filter, **kwargs)


class AudioPipe(Pipe):
    media_type = "audio"


class Media(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        pass


class Filter(ABC):
    @abstractmethod
    def apply(self) -> Template:
        pass


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


class VideoText(Filter):
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

    def apply(self) -> Template:
        return Template(
            f"[$video_input]drawtext=enable='between(t,{self.start_time},{self.end_time})':text='{self.text}':fontcolor={self.font_color}:text_align={self.text_align}:fontsize={self.size}:{self.location.value}[$video_output];"
        )


class VideoImage(Filter, Media):
    _id = count(1)

    def __init__(
        self,
        image_path: str,
        start_time: str,
        location: ImageLocations,
        size: int = 320,
        /,
        end_time: int | None = None,
    ) -> None:
        """
        Create instance of VideoImage

        Strange arguments:
            start_time can be formatted as "1m20s", "1:20", "80", "1m20"
        """
        self.img_path = image_path
        self.start_time = _time_converter(start_time)
        self.location = location.value
        self.size = size
        self.end_time = self.start_time + 5 if not end_time else end_time
        self.linked_text = None

        # total count of VideoImage instances
        self.image_index = next(self._id)

    @property
    def path(self) -> str:
        return self.img_path

    def apply(self) -> Template:
        return Template(
            f"[{self.image_index}:v]scale={self.size}:-1[img];[$video_input][img]overlay={self.location}:enable='between(t,{self.start_time},{self.end_time})'[$video_output];"
        )


class _VideoTrim(Filter):
    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self):
        return Template(
            f"[$video_input]trim=start={self.start_time}:end={self.end_time},setpts=PTS-STARTPTS[$video_output];"
        )


class _AudioTrim(Filter):
    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$audio_input]atrim=start={self.start_time}:end={self.end_time},asetpts=PTS-STARTPTS[$audio_output];"
        )


class _VideoCut(Filter):
    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$video_input]select='not(between(t,{self.start_time},{self.end_time}))',setpts=N/FRAME_RATE/TB[$video_output];"
        )


class _AudioCut(Filter):
    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$audio_input]aselect='not(between(t,{self.start_time},{self.end_time}))',asetpts=N/SR/TB[$audio_output];"
        )


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


async def compose(
    video_path: str, output_path: str, video_filters, audio_filters
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
    ffmpeg = FFmpeg().input(video_path)
    vout = VideoPipe("vout")
    aout = AudioPipe("aout")
    for filter in video_filters:
        if isinstance(filter, Media):
            ffmpeg.input(filter.path)
    for filter in video_filters:
        vout = vout.join(VideoPipe("0:v", filter))
    for filter in audio_filters:
        aout = aout.join(AudioPipe("0:a", filter))

    filter_complex = "".join([vout.combine_filter(), aout.combine_filter()])
    ffmpeg = ffmpeg.output(
        output_path,
        acodec="aac",
        filter_complex=filter_complex,
        map=["[vout]", "[aout]"],
    )

    return ffmpeg


import asyncio


async def main():
    video = "whisper_test.mp4"
    if Path("o.mp4").exists():
        Path("o.mp4").unlink()

    video_edit = [
        _VideoTrim(1, 5),
        VideoText("1s", "Hi!", TextLocations.BOTTOM_LEFT),
        VideoImage("sig2.png", "1s", ImageLocations.BOTTOM_LEFT)
    ]
    audio_edit = [_AudioTrim(1, 5)]
    bake = await compose("whisper_test.mp4", "o.mp4", video_edit, audio_edit)
    await bake.execute()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
