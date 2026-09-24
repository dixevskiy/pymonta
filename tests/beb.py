import logging
import sys

from pymonta import (
    ClipTransition,
    Locations,
    VideoAdjustments,
    VideoOverlay,
    render_text,
)
from pymonta.video.abstractions import Clip, Scene, TransitionMethod, Video

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    c1 = Clip(Video("tests/v1.mp4"), [VideoAdjustments(contrast=1.0)])
    c2 = Clip(Video("tests/2.mp4"), [VideoAdjustments(contrast=0.5)])
    c3 = Clip(Video("tests/3.mp4"), [VideoAdjustments(contrast=0.2)])
    c3_1 = Clip(
        Video("tests/3.mp4"),
        [
            VideoAdjustments(contrast=0.1),
            VideoOverlay(render_text("test"), "1s", Locations.BOTTOM_LEFT),
        ],
    )
    s = Scene(c1)
    s.add_clip(c2)
    s.add_clip(c3, ClipTransition(TransitionMethod.CIRCLECLOSE))
    s.add_clip(c3_1)
    s.render("o.mp4")
