import os
import unittest

from osu.beatmap.beatmap import Beatmap
from osu.beatmap.hit_object import HitObjectType

TEST_BEATMAPS_DIR = "osu/tests/resources/beatmaps/"


class TestBeatmap(unittest.TestCase):
    def test_parse_no_breaks(self):
        # Take a Hint [Nelliel's Easy].
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_no_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("audio.mp3", beatmap.audio_path)
        self.assertEqual(2060307, beatmap.id)
        self.assertAlmostEqual(2, beatmap.hp)
        self.assertAlmostEqual(3, beatmap.cs)
        self.assertAlmostEqual(2, beatmap.od)
        self.assertAlmostEqual(3, beatmap.ar)

        training_labels = beatmap.get_training_labels()
        self.assertEqual(1, len(training_labels))
        labels = training_labels[0]
        self.assert_expected_labels(
            [
                (HitObjectType.SLIDER, 8),
                (HitObjectType.SILENCE, 4),
                (HitObjectType.HIT_CIRCLE, 1),
                (HitObjectType.SILENCE, 3),
                (HitObjectType.SLIDER, 8),
                (HitObjectType.SILENCE, 4),
                (HitObjectType.HIT_CIRCLE, 1),
                (HitObjectType.SILENCE, 3),
                (HitObjectType.SLIDER, 8),
                (HitObjectType.SILENCE, 4),
                (HitObjectType.HIT_CIRCLE, 1),
                (HitObjectType.SILENCE, 3),
                (HitObjectType.SLIDER, 8),
                (HitObjectType.SILENCE, 8),
                (HitObjectType.SLIDER, 4),
                (HitObjectType.SILENCE, 4)
            ], labels)
        self.assert_expected_labels(
            [
                (HitObjectType.HIT_CIRCLE, 1),
                (HitObjectType.SILENCE, 4)
            ], labels, from_ending=True)
        self.assertEqual(573, len(labels))

    def test_parse_breaks(self):
        # Tokyo [Nhawak's Beginner].
        path = os.path.join(TEST_BEATMAPS_DIR, "valid_breaks.osu")
        beatmap = Beatmap.from_osu_file(path)
        self.assertEqual("tokyo.mp3", beatmap.audio_path)
        self.assertEqual(801333, beatmap.id)
        self.assertAlmostEqual(1, beatmap.hp)
        self.assertAlmostEqual(2.5, beatmap.cs)
        self.assertAlmostEqual(1, beatmap.od)
        self.assertAlmostEqual(2, beatmap.ar)
        training_labels = beatmap.get_training_labels()
        self.assertEqual(2, len(training_labels))
        labels = training_labels[0]
        self.assert_expected_labels(
            [
                (HitObjectType.SLIDER, 32),
                (HitObjectType.SILENCE, 16)
            ], labels)
        self.assert_expected_labels(
            [
                (HitObjectType.SPINNER, 32),
                (HitObjectType.SILENCE, 7),
                (HitObjectType.HIT_CIRCLE, 1)
            ], labels, from_ending=True)
        labels = training_labels[1]
        self.assert_expected_labels(
            [
                (HitObjectType.SLIDER, 32),
                (HitObjectType.SILENCE, 16)
            ], labels)
        self.assert_expected_labels(
            [
                (HitObjectType.SPINNER, 32),
                (HitObjectType.SILENCE, 7),
                (HitObjectType.HIT_CIRCLE, 1)
            ], labels, from_ending=True)
        self.assertTrue(len(training_labels[0]) > len(training_labels[1]))

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

    def assert_expected_labels(self, tuples, actual, from_ending=False):
        index = -1 if from_ending else 0
        for hit_object_type, num in tuples:
            for i in range(num):
                self.assertEqual(
                    hit_object_type.value, actual[index], f"Incorrect label at divisor {index}")
                if from_ending:
                    index -= 1
                else:
                    index += 1
