import logging
from fnmatch import fnmatch

import whisper_timestamped as whisper

LOGGER = logging.getLogger(__name__)


def transcribe_video(video_path: str, language: str, model_size="small"):
    LOGGER.info("Starting video transcribing process... This can take a while.")
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, language=language)
    LOGGER.info("Transcribing process finished!")
    return result["segments"]


def find_keywords(
    video_path: str, keyword: str, language: str, model_size="small"
) -> list[tuple[int, int]] | None:
    """
    Function which transcribes video and returns timestamps of keyword accurance.

    Returns:
        list of tuples with timestamps, first is start, second is end in seconds.
    """
    segments = transcribe_video(video_path, language, model_size)
    result = []

    for segment in segments:
        text = segment["text"]  # pyright: ignore[reportArgumentType]
        if fnmatch(text, f"*{keyword}*"):
            result.append((segment["start"], segment["end"]))
    if len(result) > 0:
        return result
    return None
