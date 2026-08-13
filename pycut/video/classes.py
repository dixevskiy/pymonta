import math
from abc import ABC, abstractmethod
from enum import Enum
from itertools import count
from string import Template

_ids = count(1)


class TextLocations(Enum):
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
            placeholders = {
                "input": self.input,
                "output": self.output,
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


class Media(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        pass


class Filter(ABC):
    @abstractmethod
    def apply(self) -> Template:
        pass

    @property
    @abstractmethod
    def stream_type(self) -> str:
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

    @property
    def stream_type(self) -> str:
        return "video"

    def apply(self) -> Template:
        return Template(
            f"[$input]drawtext=enable='between(t,{self.start_time},{self.end_time})':text='{self.text}':fontcolor={self.font_color}:text_align={self.text_align}:fontsize={self.size}:{self.location.value}[$output];"
        )


class VideoImage(Filter, Media):
    @property
    def stream_type(self) -> str:
        return "video"

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
        self.image_index = next(_ids)

    @property
    def path(self) -> str:
        return self.img_path

    def apply(self) -> Template:
        return Template(
            f"[{self.image_index}:v]scale={self.size}:-1[img];[$input][img]overlay={self.location}:enable='between(t,{self.start_time},{self.end_time})'[$output];"
        )


class _VideoTrim(Filter):
    @property
    def stream_type(self) -> str:
        return "video"

    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self):
        return Template(
            f"[$input]trim=start={self.start_time}:end={self.end_time},setpts=PTS-STARTPTS[$output];"
        )


class _AudioTrim(Filter):
    @property
    def stream_type(self) -> str:
        return "audio"

    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$input]atrim=start={self.start_time}:end={self.end_time},asetpts=PTS-STARTPTS[$output];"
        )


class _VideoCut(Filter):
    @property
    def stream_type(self) -> str:
        return "video"

    def __init__(
        self,
        start_time: int,
        end_time: int,
    ):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$input]select='not(between(t,{self.start_time},{self.end_time}))',setpts=N/FRAME_RATE/TB[$output];"
        )


class _AudioCut(Filter):
    @property
    def stream_type(self) -> str:
        return "audio"

    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time

    def apply(self) -> Template:
        return Template(
            f"[$input]aselect='not(between(t,{self.start_time},{self.end_time}))',asetpts=N/SR/TB[$output];"
        )


class Cut:
    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioCut, _VideoCut]:
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioCut(s, e), _VideoCut(s, e))


class Trim:
    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioTrim, _VideoTrim]:
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioTrim(s, e), _VideoTrim(s, e))


class ChangeVolume(Filter):
    def __init__(self, volume: float):
        self.volume = volume

    @property
    def stream_type(self) -> str:
        return "audio"

    def apply(self) -> Template:
        return Template(f"[$input]volume={self.volume}[$output];")


class VideoAdjustments(Filter):
    def __init__(
        self,
        brightness: float | None = None,
        gamma: float | None = None,
        contrast: float | None = None,
        saturation: float | None = None,
    ) -> None:
        self.b = str(brightness) if brightness else "0"
        self.g = str(gamma) if gamma else "1"
        self.c = str(contrast) if contrast else "1"
        self.s = str(saturation) if saturation else "1"

    def apply(self) -> Template:
        return Template(
            f"[$input]eq=brightness={self.b}:contrast={self.c}:gamma={self.g}:saturation={self.s}[$output];"
        )

    @property
    def stream_type(self) -> str:
        return "video"


class NewAudio(Media, Filter):
    def __init__(self, audio_path: str, volume: float):
        self.audio_path = audio_path
        self.volume = volume
        self.stream_id = next(_ids)

    def apply(self) -> Template:
        return Template(
            f"[{self.stream_id}:a]volume={self.volume}[{self.stream_id}_edit];[$input][{self.stream_id}_edit]amix=inputs=2:duration=first[$output];"
        )

    @property
    def path(self) -> str:
        return self.audio_path

    @property
    def stream_type(self) -> str:
        return "audio"


class InsertAudio(NewAudio):
    def __init__(self, audio_path: str, volume: float, start_time: str, end_time: str):
        super().__init__(audio_path, volume)
        self.start_time = _time_converter(start_time)
        self.end_time = _time_converter(end_time)

    def apply(self) -> Template:
        return Template(
            f"[{self.stream_id}:a]atrim=0:{self.end_time},adelay={self.start_time * 1000}:all=1,volume={self.volume}[{self.stream_id}_inserted];[$input][{self.stream_id}_inserted]amix=inputs=2:duration=first[$output];"
        )

class RemoveAudio(Filter):

    def apply(self) -> Template:
        return Template(
            f"[$input]volume=0[$output];"
        )

    @property
    def stream_type(self) -> str:
        return "audio"

class MuteRange(Filter):
    
    def __init__(self, start_time: str, end_time: str) -> None:
        self.start_time = _time_converter(start_time)
        self.end_time = _time_converter(end_time)

    def apply(self) -> Template:
        return Template(
            f"[$input]volume=enable='between(t,{self.start_time},{self.end_time})':volume=0[$output];"
        )