import unittest

from pymonta import Clip, Locations, Scene, Trim, VideoOverlay, render_text


class TestVideoClips(unittest.TestCase):
    def test_clip_creation(self):
        vf = [
            *Trim("1", "5"),
            VideoOverlay(render_text("Hello world!"), "1", Locations.CENTER),
        ]
        clip = Clip("tests/sample.mp4", vf)

        self.assertEqual(clip.video.duration, 30)
        self.assertEqual(clip.video.path, "tests/sample.mp4")
        self.assertEqual(clip.filters, vf)

    def test_scene_creation(self):
        vf = [
            *Trim("1", "5"),
            VideoOverlay(render_text("Hello world!"), "1", Locations.CENTER),
        ]
        clip = Clip("tests/sample.mp4", vf)

        scene = Scene(clip)
        self.assertEqual(scene.root, clip)


if __name__ == "__main__":
    unittest.main()
