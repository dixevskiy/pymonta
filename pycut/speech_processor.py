from fnmatch import fnmatch

import whisper_timestamped as whisper


async def find_keywords(
    video_path: str, keyword: str, model_size="small"
) -> list[tuple[int, int]] | None:
    """
    Function which transcribes video and returns timestamps of keyword accurance.

    Returns:
        list of tuples with timestamps, first is start, second is end in seconds.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, language="ru")

    segments = result["segments"]
    result = []

    for segment in segments:
        text = segment["text"]  # pyright: ignore[reportArgumentType]
        if fnmatch(text, f"*{keyword}*"):
            result.append((segment["start"], segment["end"]))
    if len(result) > 0:
        return result
    return None


if __name__ == "__main__":
    print(find_keywords("whisper_test.mp4", "монтаж"))
