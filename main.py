import asyncio
import math
from enum import Enum
from itertools import count
from pathlib import Path

from ffmpeg.asyncio import FFmpeg


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


class VideoText:
    def __init__(
        self,
        start_time: int,
        text: str,
        location: TextLocations,
        size: int = 34,
        /,
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
        """
        self.start_time = start_time
        self.location = location
        self.size = size
        self.wraplenght = wraplenght
        self.text_align = text_align
        self.base_stream = base_stream
        # calculate end time based on average reading speed
        # average wpm is 150, average word length is 4, 150*4/60 = 10 symbols per second
        self.end_time = (
            start_time + math.ceil(len(text) / 10) if not end_time else end_time
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
        return f"{self.base_stream}drawtext=enable='between(t,{self.start_time},{self.end_time})':text='{self.text}':fontcolor=white:text_align={self.text_align}:fontsize={self.size}:{self.location.value}[overlayed]"


class VideoImage:
    _id = count(1)

    def __init__(
        self,
        start_time: int,
        location: ImageLocations,
        size: int = 320,
        /,
        linked_text: VideoText | None = None,
        base_stream: str = "[overlayed]",
        end_time: int | None = None,
    ) -> None:
        self.start_time = start_time
        self.location = location.value
        self.size = size
        self.base_stream = base_stream
        self.end_time = start_time + 5 if not end_time else end_time
        self.linked_text = None

        # total count of VideoImage instances
        self.image_index = next(self._id)

        # link image to provided text
        if linked_text:
            self.linked_text = linked_text
            self.start_time = linked_text.start_time
            self.end_time = linked_text.end_time

    def __str__(self):
        return f"[{self.image_index}:v]scale={self.size}:-1[img];{self.base_stream}[img]overlay={self.location}:enable='between(t,{self.start_time},{self.end_time})'[overlayed]"


def compose_complex_filter(
    images: list[VideoImage] | None, texts: list[VideoText] | None
) -> str:
    """
    High level video composition function
    """
    base_video = "[0:v]"
    filter_complex = ""
    # Handles images first, but it doesn't matter
    if images:
        images[0].base_stream = base_video
        filter_complex = f"{';'.join(map(str, images))};"
        for image in images:
            if image.linked_text:
                filter_complex += f"{image.linked_text!s};"
        if texts:
            filter_complex += ";".join(map(str, texts))
        return filter_complex
    if texts:
        texts[0].base_stream = base_video
        filter_complex = f"{';'.join(map(str, texts))};"
        if images:
            filter_complex += ";".join(map(str, images))
        return filter_complex
    return filter_complex


async def main():
    video = "input.mp4"
    if Path("o.mp4").exists():
        Path("o.mp4").unlink()

    overlays = [
        VideoImage(1, ImageLocations.UPPER_RIGHT, linked_text=VideoText(1, "Это АРА!\nПрикольни реплика <3", TextLocations.HORIZONTAL_RIGHT)),
        VideoImage(
            1,
            ImageLocations.BOTTOM_LEFT,
            340,
            linked_text=VideoText(1, "Это экспи!", TextLocations.HORIZONTAL_LEFT),
        ),
    ]
    texts = [
        VideoText(1, "Я МОГУ ВСЕ!!!", TextLocations.BOTTOM_RIGHT),
        VideoText(0, "Действительно...", TextLocations.UPPER_LEFT),
    ]

    filter_complex = compose_complex_filter(overlays, texts)

    ffmpeg = (
        FFmpeg()
        .input(video)
        .input("sig2.png")
        .input("p1.jpg")
        .output(
            "o.mp4", filter_complex=filter_complex, map="[overlayed]", acodec="copy"
        )
    )

    await asyncio.create_task(ffmpeg.execute())


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
