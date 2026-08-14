import logging
from fnmatch import fnmatch

import whisper_timestamped as whisper

LOGGER = logging.getLogger(__name__)


def transcribe_file(file_path: str, language: str, model_size="small"):
    LOGGER.info("Starting video transcribing process... This can take a while.")
    model = whisper.load_model(model_size)
    result = model.transcribe(file_path, language=language)
    LOGGER.info("Transcribing process finished!")
    return result["segments"]


def _format_srt_time(total_seconds: float) -> str:
    """
    Convert total seconds to SRT timestamp format: HH:MM:SS,mmm
    (milliseconds separated by comma, as per SRT spec).
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


def generate_srt(transcription) -> str:
    preprocess = []
    for segment in transcription:
        text = segment["text"]  # pyright: ignore[reportArgumentType]
        srt_start = _format_srt_time(segment["start"])
        srt_end = _format_srt_time(segment["end"])
        preprocess.append(f"{len(preprocess) + 1}\n{srt_start} --> {srt_end}\n{text}\n")
    return "\n".join(preprocess)


def find_keywords(transcription, keyword: str) -> list[tuple[int, int]] | None:
    """
    Function which transcribes video and returns timestamps of keyword accurance.

    Returns:
        list of tuples with timestamps, first is start, second is end in seconds.
    """
    result = []

    for segment in transcription:
        text = segment["text"]  # pyright: ignore[reportArgumentType]
        if fnmatch(text, f"*{keyword}*"):
            result.append((segment["start"], segment["end"]))
    if len(result) > 0:
        return result
    return None
