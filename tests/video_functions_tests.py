from pymonta.video.functions import build_pipelines
from pymonta import RemoveAudio
from pymonta import VideoAdjustments
from pymonta import get_duration
import asyncio
import unittest
from pymonta import detect_silence_fragments


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
        video_filtres = [VideoAdjustments(brightness=1.0)]
        audio_filtres = [RemoveAudio()]
        vout_p, aout_p = build_pipelines([*video_filtres, *audio_filtres])

        assigned_vf = vout_p.get_all_filters()
        assigned_af = aout_p.get_all_filters()

        self.assertEqual(video_filtres, assigned_vf)
        self.assertEqual(audio_filtres, assigned_af)


if __name__ == "__main__":
    unittest.main()
