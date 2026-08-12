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
