import os
import unittest

from osu.beatmap.beatmap import Beatmap

TEST_BEATMAPS_DIR = "osu/tests/resources/beatmaps/"


class TestBeatmap(unittest.TestCase):
    def test_parse_no_breaks(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_no_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("audio.mp3", beatmap.audio_path)
        self.assertEqual(2060307, beatmap.id)
        self.assertAlmostEqual(2, beatmap.hp)
        self.assertAlmostEqual(3, beatmap.cs)
        self.assertAlmostEqual(2, beatmap.od)
        self.assertAlmostEqual(3, beatmap.ar)

    def test_parse_breaks(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("tokyo.mp3", beatmap.audio_path)
        self.assertEqual(801333, beatmap.id)
        self.assertAlmostEqual(1, beatmap.hp)
        self.assertAlmostEqual(2.5, beatmap.cs)
        self.assertAlmostEqual(1, beatmap.od)
        self.assertAlmostEqual(2, beatmap.ar)

    def test_not_on_divisor(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "not_on_divisor.osu")
        with self.assertRaises(Exception):
            Beatmap.from_osu_file(path)

    def test_rounding_error(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "rounding_error.osu")
        Beatmap.from_osu_file(path)
        path = os.path.join(TEST_BEATMAPS_DIR, "rounding_error2.osu")
        Beatmap.from_osu_file(path)

    def test_parse_wrong_mode(self):
        path = os.path.join(TEST_BEATMAPS_DIR, "taiko.osu")
        with self.assertRaises(Exception):
            Beatmap.from_osu_file(path)

    def test_parse_wrong_divisor(self):
        # Missing beatmpa id.
        path = os.path.join(TEST_BEATMAPS_DIR, "old_format.osu")
        with self.assertRaises(Exception):
            Beatmap.from_osu_file(path)

    def test_late_starting_timing_point(self):
        path = os.path.join(TEST_BEATMAPS_DIR,
                            "late_starting_timing_point.osu")
        Beatmap.from_osu_file(path)
