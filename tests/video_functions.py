import asyncio

from pycut.video.functions import render_text


if __name__ == "__main__":
    asyncio.run(render_text("Привет мир! Бебебе Бебебе БебебеБебебе", "tests"))
