import shutil
from collections.abc import Sequence
from pathlib import Path

from pymonta.video.filters import (
    Filter,
    TransitionMethod,
    _AudioConcat,
    _AudioCut,
    _AudioTransition,
    _AudioTrim,
    _ChangeAudioSpeed,
    _ChangeVideoSpeed,
    _time_converter,
    _TransitionMeta,
    _VideoConcat,
    _VideoCut,
    _VideoTransition,
    _VideoTrim,
)
from pymonta.video.functions import bake_filters, get_duration


class ClipTransition:
    def __init__(self, method: TransitionMethod, duration: float = 0.5) -> None:
        self.method = method
        self.duration = duration

    def use(
        self, joining_video: str, meta: _TransitionMeta
    ) -> tuple[_VideoTransition, _AudioTransition]:
        vt = _VideoTransition(joining_video, meta)
        at = _AudioTransition(vt._send_id, meta)
        return (vt, at)


class ClipConcat:
    def use(self, joining_video: str) -> tuple[_VideoConcat, _AudioConcat]:
        vc = _VideoConcat(joining_video)
        ac = _AudioConcat(vc._send_id)
        return (vc, ac)


class ClipSpeed:
    def __new__(
        cls, desired_speed: float
    ) -> tuple[_ChangeAudioSpeed, _ChangeVideoSpeed]:
        return (
            _ChangeAudioSpeed(desired_speed),
            _ChangeVideoSpeed(desired_speed),
        )


class Trim:
    """Factory that returns a tuple of audio and video trim filters.

    The returned filters keep only the specified time range.
    """

    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioTrim, _VideoTrim]:
        """Create a pair of `_AudioTrim` and `_VideoTrim` filters.

        Args:
            start_time: Start of the segment to keep (human-readable).
            end_time: End of the segment to keep (human-readable).

        Returns:
            A tuple `(_AudioTrim, _VideoTrim)`.
        """
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioTrim(s, e), _VideoTrim(s, e))


class Cut:
    """Factory that returns a tuple of audio and video cut filters.

    The returned filters remove the specified time range from both streams.
    """

    def __new__(cls, start_time: str, end_time: str) -> tuple[_AudioCut, _VideoCut]:
        """Create a pair of `_AudioCut` and `_VideoCut` filters.

        Args:
            start_time: Start of the segment to remove (human-readable).
            end_time: End of the segment to remove (human-readable).

        Returns:
            A tuple `(_AudioCut, _VideoCut)`.
        """
        s, e = _time_converter(start_time), _time_converter(end_time)
        return (_AudioCut(s, e), _VideoCut(s, e))


class Video:
    def __init__(self, path: str) -> None:
        self.path = path
        self.duration = get_duration(path)


class Clip:
    def __init__(self, video_path: str, filters: Sequence[Filter]) -> None:
        self.video = Video(video_path)
        self.filters = filters
        self.baked_path = None

    def bake(self) -> None:
        self.baked_path = bake_filters(self.video.path, self.filters)
        self.video.duration = get_duration(self.baked_path)


class Scene:
    def __init__(self, root_clip: Clip) -> None:
        self.root = root_clip
        self._clip_stack = [self.root]
        self._head: Clip | None = None

    def bake_clips(self) -> None:
        for clip in self._clip_stack:
            if not clip.baked_path:
                clip.bake()

    def add_clip(
        self, clip: Clip, concat_method: ClipTransition | ClipConcat | None = None
    ) -> None:
        if not concat_method:
            concat_method = ClipConcat()
        self._clip_stack.append(clip)
        self.bake_clips()
        assert clip.baked_path
        assert self.root.baked_path
        if isinstance(concat_method, ClipTransition):
            glue_filters = [
                *concat_method.use(
                    clip.baked_path,
                    _TransitionMeta(
                        concat_method.method,
                        concat_method.duration,
                        self.root.video.duration
                        if not self._head
                        else self._head.video.duration,
                    ),
                )
            ]
        else:
            glue_filters = [*concat_method.use(clip.baked_path)]

        if not self._head:
            self._head = Clip(bake_filters(self.root.baked_path, glue_filters), [])
        else:
            self._head = Clip(bake_filters(self._head.video.path, glue_filters), [])

    def show_timeline(self) -> str:
        res_str = []
        for clip in self._clip_stack:
            res_str.append(f"{clip.video.path} ({clip.video.duration} seconds) -> ")
        res_str.append("END")
        res_str.append(
            f"\nTotal duration: {sum([x.video.duration for x in self._clip_stack])} seconds"
        )
        return "".join(res_str)

    def render(self, output_path: str) -> str:
        self.bake_clips()
        assert self.root.baked_path
        res = None
        if not self._head:
            res = self.root.baked_path
        else:
            res = self._head.video.path
        if Path(output_path).exists():
            raise RuntimeError("Output file exists. Please handle it manualy.")
        shutil.copy(res, output_path)
        return output_path
