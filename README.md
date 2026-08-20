# pycut

Video redacting library built on top of ffmpeg, whisper and opencv for the nerds.

It was built for personal usage, but I decided to make it open-source from the start.

# Dependencies

- ffmpeg (specific version to be specified)

## Current features

- Speech recognition
- Automatic subtitles (srt) generation
- Keyword search in transcription with timestamps
- Filter based declaritive editing
- Integration with Pillow
- Wrapper around scenedetect

# Roadmanp

## Planned features

- Transition effects
- Track based editing
- Tests for code

# How to use

1. Install latest release file in your environment.
2. Use `pycut help` for onboarding information
3. Use simple `python video_script.py` to render videos.