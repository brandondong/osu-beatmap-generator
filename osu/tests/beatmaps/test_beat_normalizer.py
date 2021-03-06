import math
import os
import unittest

import numpy as np

from osu.beatmap import beat_normalizer

TEST_BEAT_DATA_DIR = "osu/tests/resources/beat_data/"


class TestBeatNormalizer(unittest.TestCase):
    def test_whole_number_bpm_unchanged(self):
        # 60 bpm.
        beats = np.array([2, 3, 4, 5]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        self._assert_single_bpm_details(
            beats, onsets=beats, offset=2000, interval=1000, last_beat=5000)

    def test_whole_number_bpm_changed(self):
        # 60 bpm with some small noise.
        beats = np.arange(2, 100) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        beats[1] += 0.1
        beats[2] -= 0.1
        self._assert_single_bpm_details(
            beats, onsets=beats, offset=2000, interval=1000, last_beat=99000)

    def test_remove_bad_start_beat(self):
        # 60 bpm.
        beats = np.array([0, 2, 3, 4, 5, 6]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        onsets = beats[1:]
        # First beat should be omitted.
        self._assert_single_bpm_details(
            beats, onsets, offset=2000, interval=1000, last_beat=6000)

    def test_remove_bad_end_beat(self):
        # 60 bpm.
        beats = np.array([2, 3, 4, 5, 6, 10]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        onsets = beats[:-1]
        # Last beat should be omitted.
        self._assert_single_bpm_details(
            beats, onsets, offset=2000, interval=1000, last_beat=6000)

    def test_remove_bad_start_and_end_beat(self):
        # 60 bpm.
        beats = np.array([0, 2, 3, 4, 5, 6, 10]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        onsets = beats[1:-1]
        # First and last beat should be omitted.
        self._assert_single_bpm_details(
            beats, onsets, offset=2000, interval=1000, last_beat=6000)

    def test_remove_bad_until_start(self):
        # 60 bpm.
        beats = np.array([0, 0.1, 2, 3, 4, 5, 6]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        onsets = beats[2:]
        # First two beat should be omitted.
        self._assert_single_bpm_details(
            beats, onsets, offset=2000, interval=1000, last_beat=6000)

    def test_remove_bad_from_end(self):
        # 60 bpm.
        beats = np.array([2, 3, 4, 5, 6, 10, 12]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        onsets = beats[:-2]
        # Last beat should be omitted.
        self._assert_single_bpm_details(
            beats, onsets, offset=2000, interval=1000, last_beat=6000)

    def test_syncopated_shifted(self):
        # 60 bpm but one fewer beat due to a misclassification with syncopation.
        beats = np.arange(201) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        beats[105:115] += 0.5
        beats[115:] += 1
        self.assertEqual(beats[-1], 201 +
                         beat_normalizer.BEAT_TRACKING_TIMING_OFFSET)
        self._assert_single_bpm_details(
            beats, onsets=beats, offset=0, interval=1000, last_beat=201000)

    def test_syncopated_shifted_odd(self):
        # 60 bpm but one fewer beat due to a misclassification with syncopation.
        beats = np.arange(10, 200) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        beats[105:115] += 0.5
        beats[115:] += 1
        self.assertEqual(beats[-1], 200 +
                         beat_normalizer.BEAT_TRACKING_TIMING_OFFSET)
        self._assert_single_bpm_details(
            beats, onsets=beats, offset=10000, interval=1000, last_beat=200000)

    def test_inner_beat(self):
        # 6 seconds per beat (10 bpm) but misclassified as 9 seconds per beat.
        beats = np.array([0, 9, 18, 27]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        # Onsets match exactly the true beat.
        onsets = np.array([0, 6, 12, 18, 24]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        self._assert_single_bpm_details(
            beats, onsets, offset=0, interval=6000, last_beat=24000)

    def test_inner_beat_offset(self):
        # 6 seconds per beat (10 bpm) but misclassified as 9 seconds per beat.
        beats = np.array([0, 9, 18, 27]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        # Onsets match exactly the true beat with offset.
        onsets = np.array([3, 9, 15, 21, 27]) + \
            beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
        self._assert_single_bpm_details(
            beats, onsets, offset=3000, interval=6000, last_beat=27000)

    def test_real_beat_data_single_bpm(self):
        sum = 0
        count = 0
        for file in os.listdir(TEST_BEAT_DATA_DIR):
            filename = os.path.join(TEST_BEAT_DATA_DIR, file)
            beats, onsets, expected_bpm, expected_offset = _read_beats_file(
                filename)
            expected_interval = 60000 / expected_bpm
            timing_points, bpm, _ = beat_normalizer.get_timing_info(
                beats, onsets)
            fail_msg = f"Failed for {file}."
            self.assertEqual(len(timing_points), 1, msg=fail_msg)
            self.assertEqual(bpm, expected_bpm, msg=fail_msg)
            interval = timing_points[0][1]
            self.assertAlmostEqual(interval, expected_interval, msg=fail_msg)

            # Calculate the offset differences.
            offset = timing_points[0][0]
            num_interval_diff = (expected_offset - offset) / interval
            o1 = offset + math.floor(num_interval_diff) * interval
            o2 = offset + math.ceil(num_interval_diff) * interval
            d1 = o1 - expected_offset
            d2 = o2 - expected_offset
            min_diff = d1 if abs(d1) < abs(d2) else d2
            if (abs(min_diff) < interval / 4):
                count += 1
                sum += min_diff

        # Having an average of 0 minimizes the squared differences in offset.
        self.assertEqual(round(sum / count), 0)

    def _assert_single_bpm_details(self, beats, onsets, *, offset, interval, last_beat):
        timing_points, bpm, actual_last_beat = beat_normalizer.get_timing_info(
            beats, onsets)
        self.assertEqual(len(timing_points), 1)
        timing_point = timing_points[0]
        self.assertEqual(timing_point[0], offset)
        self.assertEqual(timing_point[1], interval)
        self.assertEqual(bpm, round(60000 / interval))
        self.assertEqual(actual_last_beat, last_beat)


def _read_beats_file(filename):
    with open(filename, mode="r") as csv_file:
        beat_contents = csv_file.readline()
        onset_contents = csv_file.readline()
        expected_bpm_line = csv_file.readline()
        expected_bpm = float(expected_bpm_line)
        expected_offset_line = csv_file.readline()
        expected_offset = float(expected_offset_line)

    beats = _parse_to_np_array(beat_contents)
    onsets = _parse_to_np_array(onset_contents)
    return beats, onsets, expected_bpm, expected_offset


def _parse_to_np_array(s):
    data = s.split(",")
    a = np.empty(len(data))

    for idx, value in enumerate(data):
        a[idx] = float(value)
    return a
