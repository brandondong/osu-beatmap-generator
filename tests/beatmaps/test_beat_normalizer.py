import unittest

import numpy as np

from beatmap import beat_normalizer

class TestBeatNormalizer(unittest.TestCase):
	def test_whole_number_bpm_unchanged(self):
		# 60 bpm.
		beats = np.array([2, 3, 4, 5]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm = beat_normalizer.get_timing_info(beats)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)
		
	def test_whole_number_bpm_changed(self):
		# 60 bpm.
		beats = np.array([2, 3.1, 3.9, 5, 6]) + beat_normalizer.BEAT_TRACKING_TIMING_OFFSET
		timing_points, bpm = beat_normalizer.get_timing_info(beats)
		self.assertEqual(timing_points, [(2000, 1000)])
		self.assertEqual(bpm, 60)