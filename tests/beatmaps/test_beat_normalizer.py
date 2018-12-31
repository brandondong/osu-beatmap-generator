import unittest

import numpy as np

from beatmap import beat_normalizer

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
		beats = np.array([2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=beats)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
	
	def test_remove_bad_start_beat(self):
		# 60 bpm.
		beats = np.array([0, 2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3.1, 3.9, 5.1, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
		
	def test_remove_bad_end_beat(self):
		# 60 bpm.
		beats = np.array([2, 3.1, 3.9, 5, 6, 10]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
	
	def test_remove_bad_start_and_end_beat(self):
		# 60 bpm.
		beats = np.array([0, 2, 3.1, 3.9, 5, 6, 10]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3, 3.9, 5.1, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First and last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
		
	def test_remove_bad_until_start(self):
		# 60 bpm.
		beats = np.array([0, 0.1, 2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# First beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)
	
	def test_remove_bad_from_end(self):
		# 60 bpm.
		beats = np.array([2, 3.1, 3.9, 5, 6, 10, 12]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		onsets = np.array([2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		# Last beat should be omitted.
		timing_points, bpm, last_beat = beat_normalizer.get_timing_info(beats, onsets=onsets)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		self.assertEqual(last_beat, 6000)