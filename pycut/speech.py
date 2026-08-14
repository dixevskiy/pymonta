import logging
from fnmatch import fnmatch
from time import strftime

import whisper_timestamped as whisper

LOGGER = logging.getLogger(__name__)


def transcribe_file(file_path: str, language: str, model_size="small"):
    LOGGER.info("Starting video transcribing process... This can take a while.")
    model = whisper.load_model(model_size)
    result = model.transcribe(file_path, language=language)
    LOGGER.info("Transcribing process finished!")
    return result["segments"]


def generate_srt(transcription) -> str:
    preprocess = []
    for segment in transcription:
        text = segment["text"]  # pyright: ignore[reportArgumentType]
        srt_start = strftime("%H:%M:%S", segment["start"])
        srt_end = strftime("%H:%M:%S", segment["start"])
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
