import unittest
from random import randint

from pymonta.video.filters import _time_converter


class TestTimeConverter(unittest.TestCase):
    def test_time_converter_seconds(self):

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}s"), r)

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}"), r)

    def test_time_converter_minutes(self):

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}m"), r * 60)

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}m{r}"), r * 60 + r)

    def test_time_converter_hours(self):

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}h"), r * 3600)

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}h{r}m"), r * 3600 + r * 60)

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}h{r}m{r}"), r * 3600 + r * 60 + r)

        for _ in range(100):
            r = randint(0, 10000)
            self.assertEqual(_time_converter(f"{r}h{r}m{r}s"), r * 3600 + r * 60 + r)


if __name__ == "__main__":
    unittest.main()
