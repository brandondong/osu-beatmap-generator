import os
import unittest

from beatmap.beatmap import Beatmap

TEST_BEATMAPS_DIR = "../tests/resources/beatmaps/"


class TestBeatmap(unittest.TestCase):
    def test_parse_no_breaks(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_no_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("audio.mp3", beatmap.audio_path)
        self.assertEqual("2060307", beatmap.id)
        self.assertAlmostEqual(2, beatmap.hp)
        self.assertAlmostEqual(3, beatmap.cs)
        self.assertAlmostEqual(2, beatmap.od)
        self.assertAlmostEqual(3, beatmap.ar)

    def test_parse_breaks(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("tokyo.mp3", beatmap.audio_path)
        self.assertEqual("801333", beatmap.id)
        self.assertAlmostEqual(1, beatmap.hp)
        self.assertAlmostEqual(2.5, beatmap.cs)
        self.assertAlmostEqual(1, beatmap.od)
        self.assertAlmostEqual(2, beatmap.ar)

    def test_not_on_divisor(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "not_on_divisor.osu")
        with self.assertRaises(Exception):
            Beatmap.from_osu_file(path)

    def test_parse_wrong_mode(self):
        pass

    def test_parse_invalid_beatmap(self):
        pass
