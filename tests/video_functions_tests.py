import asyncio
import unittest

from pymonta import (
    RemoveAudio,
    VideoAdjustments,
    detect_silence_fragments,
    get_duration,
)
from pymonta.video.filters import _VideoCut
from pymonta.video.functions import build_pipelines


class TestVideoFunctions(unittest.TestCase):
    def test_detect_silence_fragments(self):
        approx = [(0.0, 5.0), (6.5, 10.0), (12.0, 15.0), (20.0, 24.5), (26.0, 27.5)]
        silences = asyncio.run(
            detect_silence_fragments("tests/sample.mp4", min_duration=1)
        )
        for i in range(len(silences)):
            self.assertAlmostEqual(silences[i][0], approx[i][0], delta=0.3)
            self.assertAlmostEqual(silences[i][1], approx[i][1], delta=0.3)

    def test_get_duration(self):
        calc_dur = get_duration("tests/sample.mp4")
        real_dur = 30
        self.assertEqual(calc_dur, real_dur)

    def test_build_pipelines(self):
        video_filtres = [VideoAdjustments(brightness=1.0), _VideoCut(1, 5)]
        audio_filtres = [RemoveAudio()]
        vout_p, aout_p = build_pipelines([*video_filtres, *audio_filtres])

        assigned_vf = vout_p.get_all_filters()
        assigned_af = aout_p.get_all_filters()

        self.assertEqual(video_filtres, assigned_vf)
        self.assertEqual(audio_filtres, assigned_af)

        self.assertEqual(
            vout_p.compile_filter(),
            "[0:v]eq=brightness=1.0:contrast=1:gamma=1:saturation=1[vout];[vout]select='not(between(t,1,5))',setpts=N/FRAME_RATE/TB[vout];",
        )
        self.assertEqual(aout_p.compile_filter(), "[0:a]volume=0[aout];")


if __name__ == "__main__":
    unittest.main()
