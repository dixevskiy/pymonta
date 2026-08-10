import asyncio
from enum import Enum
from pathlib import Path

from ffmpeg.asyncio import FFmpeg


class Locations(Enum):
    CENTER = "x=(w-tw)/2:y=(h-th)/2"
    BOTTOM_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"
    BOTTOM_LEFT = "x=(w-tw)/2-(w-tw)/3:y=(h-th)/2+(h-th)/3"
    UPPER_RIGHT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2-(h-th)/3"
    UPPER_LEFT = "x=(w-tw)/2+(w-tw)/3:y=(h-th)/2+(h-th)/3"


def paste_text(
    ffmpeg: FFmpeg,
    start_time: int,
    text: str,
    location: Locations,
    size: int = 34,
    /,
    end_time: int | None = None,
    wraplenght: int = 32,
) -> FFmpeg:

    end_time = start_time + 10 if not end_time else end_time

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

    return ffmpeg.output(
        "o.mp4",
        vf=rf"drawtext=enable='between(t,{start_time},{end_time})':text='{text}':fontcolor=white:text_align=C:fontsize={size}:{location.value}",
    )


async def main():
    video = "input.mp4"
    if Path("o.mp4").exists():
        Path("o.mp4").unlink()
    ffmpeg = paste_text(
        FFmpeg().input(video),
        1,
        "Я немного просчитался.\nОйле была названа не в честь ученного, а в качестве аббревиатуры.",
        Locations.UPPER_RIGHT,
    )

    await asyncio.create_task(ffmpeg.execute())


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
