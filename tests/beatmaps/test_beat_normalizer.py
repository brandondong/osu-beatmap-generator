import os
import unittest

import numpy as np

from beatmap import beat_normalizer

TEST_BEAT_DATA_DIR = "../tests/resources/"
TEST_BEAT_DATA_SINGLE_BPM_DIR = TEST_BEAT_DATA_DIR + "single/"
TEST_BEAT_DATA_MULTI_BPM_DIR = TEST_BEAT_DATA_DIR + "multi/"

class TestBeatNormalizer(unittest.TestCase):
	def test_whole_number_bpm_unchanged(self):
		# 60 bpm.
		beats = np.array([2, 3, 4, 5]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 5000)
		
	def test_whole_number_bpm_changed(self):
		# 60 bpm.
		beats = np.arange(2, 100) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		beats[1] += 0.1
		beats[2] -= 0.1
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 99000)
	
	def test_remove_bad_start_beat(self):
		# 60 bpm.
		beats = np.array([0, 2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
		
	def test_remove_bad_end_beat(self):
		# 60 bpm.
		beats = np.array([2, 3, 4, 5, 6, 10]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
	
	def test_remove_bad_start_and_end_beat(self):
		# 60 bpm.
		beats = np.array([0, 2, 3, 4, 5, 6, 10]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First and last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
		
	def test_remove_bad_until_start(self):
		# 60 bpm.
		beats = np.array([0, 0.1, 2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
	
	def test_remove_bad_from_end(self):
		# 60 bpm.
		beats = np.array([2, 3, 4, 5, 6, 10, 12]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 4, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)

	def test_syncopated_shifted(self):
		# 60 bpm but one fewer beat due to a misclassification with syncopation.
		beats = np.arange(201) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		beats[5:15] += 0.5
		beats[15:] += 1
		self.assertEqual(beats[-1], 201 + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET)
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(0, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 201000)

	def test_syncopated_shifted_odd(self):
		# 60 bpm but one fewer beat due to a misclassification with syncopation.
		beats = np.arange(10, 200) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		beats[5:15] += 0.5
		beats[15:] += 1
		self.assertEqual(beats[-1], 200 + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET)
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(10000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 200000)

	def test_inner_beat(self):
		# 6 seconds per beat (10 bpm) but misclassified as 9 seconds per beat.
		beats = np.array([0, 9, 18, 27]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Onsets match exactly the true beat.
		onsets = np.array([0, 6, 12, 18, 24]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets)
		self.assertEqual(timing_points, [(0, 6000)])
		self.assertEqual(bpm, 10)
		self.assertEqual(last_beat, 24000)

	def test_inner_beat_offset(self):
		# 6 seconds per beat (10 bpm) but misclassified as 9 seconds per beat.
		beats = np.array([0, 9, 18, 27]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Onsets match exactly the true beat with offset.
		onsets = np.array([3, 9, 15, 21, 27]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets)
		self.assertEqual(timing_points, [(3000, 6000)])
		self.assertEqual(bpm, 10)
		self.assertEqual(last_beat, 27000)

	def test_inner_beat_syncopation(self):
		# 6 seconds per beat (10 bpm) but misclassified as 9 seconds per beat also with a missing beat.
		beats = np.array([0, 13, 27]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([3, 9, 15, 21, 27]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets)
		self.assertEqual(timing_points, [(3000, 6000)])
		self.assertEqual(bpm, 10)
		self.assertEqual(last_beat, 27000)

	def test_multi_bpm(self):
		beats = np.array([0, 1, 3, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(0, 1000), (1000, 2000), (3000, 3000)])
		self.assertEqual(bpm, 30)
		self.assertEqual(last_beat, 6000)

	def test_real_beat_data_single_bpm(self):
		for file in os.listdir(TEST_BEAT_DATA_SINGLE_BPM_DIR):
			filename = os.path.join(TEST_BEAT_DATA_SINGLE_BPM_DIR, file)
			beats, onsets, expected_bpm = _read_beats_file(filename)
			expected_interval = 60000 / expected_bpm
			timing_points, bpm, _ = beat_normalizer.get_timing_info(beats, onsets)
			fail_msg = f"Failed for {file}."
			self.assertEqual(len(timing_points), 1, msg=fail_msg)
			self.assertEqual(bpm, expected_bpm, msg=fail_msg)
			self.assertAlmostEqual(timing_points[0][1], expected_interval, msg=fail_msg)
	
	def test_real_beat_data_multi_bpm(self):
		for file in os.listdir(TEST_BEAT_DATA_MULTI_BPM_DIR):
			filename = os.path.join(TEST_BEAT_DATA_MULTI_BPM_DIR, file)
			beats, onsets, _ = _read_beats_file(filename)
			timing_points, _, _ = beat_normalizer.get_timing_info(beats, onsets)
			fail_msg = f"Failed for {file}."
			self.assertTrue(len(timing_points) >  1, msg=fail_msg)

def _read_beats_file(filename):
	with open(filename, mode="r") as csv_file:
		beat_contents = csv_file.readline()
		onset_contents = csv_file.readline()
		expected_bpm_line = csv_file.readline()
		expected_bpm = float(expected_bpm_line) if len(expected_bpm_line) > 0 else None
	
	beats = _parse_to_np_array(beat_contents)
	onsets = _parse_to_np_array(onset_contents)
	return beats, onsets, expected_bpm

def _parse_to_np_array(s):
	data = s.split(",")
	a = np.empty(len(data))
	
	for idx, value in enumerate(data):
		a[idx] = float(value)
	return a			
