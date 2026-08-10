import asyncio
from enum import Enum
import math
from pathlib import Path

from ffmpeg.asyncio import FFmpeg


class Locations(Enum):
    CENTER = "x=(w-tw)/2:y=(h-th)/2"
    BOTTOM_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"
    BOTTOM_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2+(h-th)/3"
    UPPER_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2-(h-th)/3"
    UPPER_LEFT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"


def paste_text(
    start_time: int,
    text: str,
    location: Locations,
    size: int = 34,
    /,
    end_time: int | None = None,
    wraplenght: int = 32,
    text_align: str = "C",
) -> dict[str, str]:
    """
    Place text in your video.

    Returns:
        FFmpeg instance for chaining.
    Confusing arguments:
        text_align can be: C=center, L=left, R=right.
        end_time calculates automatically based on length of text.
    """
    # calculate end time based on average reading speed
    # average wpm is 150, average word length is 4, 150*4/60 = 10 symbols per second
    end_time = start_time + math.ceil(len(text) / 10) if not end_time else end_time

    # cli safeguard
    text = text.replace("'", "")

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
        text = " ".join(wrapped_string_build)

    return {
        "vf": rf"drawtext=enable='between(t,{start_time},{end_time})':text='{text}':fontcolor=white:text_align={text_align}:fontsize={size}:{location.value}"
    }


def paste_imgae(
    start_time: int,
    image_path: str,
    location: Locations,
    size: int = 34,
    /,
    end_time: int | None = None,
) -> dict[str, str]: ...


async def main():
    video = "input.mp4"
    if Path("o.mp4").exists():
        Path("o.mp4").unlink()
    # ffmpeg = paste_text(
    #     FFmpeg().input(video),
    #     1,
    #     "Здесь.",
    #     Locations.UPPER_RIGHT,
    # )
    ffmpeg = (
        FFmpeg()
        .input(video)
        .output(
            "o.mp4",
            # Use pipe operator | for dict combining
            paste_text(1, "Мяу", Locations.BOTTOM_LEFT),  # pyright: ignore[reportArgumentType]
        )
    )

    await asyncio.create_task(ffmpeg.execute())


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
