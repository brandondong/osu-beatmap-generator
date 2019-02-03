import numpy as np

WHOLE_NUMBER_BPM_THRESHOLD = 0.05
EXPECTED_INTERVAL_DIFF_THRESHOLD = 10

# Timing offset to handle a beat tracker's consistent deviation.
BEAT_TRACKING_TIMING_OFFSET = 0.034

EDGE_FILTER_WINDOW_SIZE = 4

def get_timing_info(beats, onsets):
	"""Extracts beatmap timing info from beat tracking data.
	
	Returns a list of timing points, the beatmap bpm, and the offset of the last beat."""

	beats = beats - BEAT_TRACKING_TIMING_OFFSET
	onsets = onsets - BEAT_TRACKING_TIMING_OFFSET
	
	# Ignore starting and ending beats found to be likely happening during musical breaks.
	beats = _filter_edge_beats(beats, onsets)
	
	if _likely_single_bpm(beats):
		# Check if it matches a whole number bpm by first considering the time between the first and last beat.
		# Optimistically, the length between these beats would be high and would cancel out any noise.
		num_beats = beats.shape[0]
		total_time = beats[-1] - beats[0]
		bpm = (num_beats - 1) / total_time * 60
		round_bpm = round(bpm)
		if _within_whole_number_beat_threshold(bpm, round_bpm):
			# Calculate the expected number of seconds between each beat.
			expected_interval = 60 / round_bpm
			# Fit a line to the recorded beat times where the slope is the expected interval and the y-intercept is the starting beat.
			y0 = np.mean(beats) - expected_interval * (num_beats - 1) / 2
			expected_beats = np.arange(num_beats) * expected_interval + y0
			
			# Second check is to filter out syncopated false positives by comparing with the expected beats.
			avg_diff = np.mean(np.abs(expected_beats - beats))
			avg_diff_percent = avg_diff / expected_interval * 100
			if avg_diff_percent < EXPECTED_INTERVAL_DIFF_THRESHOLD:
				offset = _sec_to_rounded_milis(y0)
				timing_points = [(offset, expected_interval * 1000)]
				last_beat = _sec_to_rounded_milis(expected_beats[-1])
				return timing_points, round_bpm, last_beat
		
		# Check again for a whole number bpm but assuming we miscounted a beat. This happens regularly with syncopation.
		adjusted_bpm = num_beats / total_time * 60
		round_bpm = round(adjusted_bpm)
		if _within_whole_number_beat_threshold(adjusted_bpm, round_bpm):
			# Line fitting for the starting beat cannot rely on the beat positions anymore as they may have been uniformly shifted.
			# Just use the starting and ending beat to estimate the mean.
			expected_interval = 60 / round_bpm
			y0 = (beats[-1] + beats[0]) / 2 - expected_interval * num_beats / 2
			offset = _sec_to_rounded_milis(y0)
			timing_points = [(offset, expected_interval * 1000)]
			last_beat = _sec_to_rounded_milis(beats[-1])
			return timing_points, round_bpm, last_beat

		# Check if one and a half beats were misclassified to a single beat.
		# We can be pretty confident of this case if it matches a whole number bpm after adjustment and not before.
		bpm *= 1.5
		round_bpm = round(bpm)
		if _within_whole_number_beat_threshold(bpm, round_bpm):
			# Choose how to offset the new smaller beat interval. 
			pass

		# Perform the syncopation check again.
		adjusted_bpm *= 1.5
		round_bpm = round(adjusted_bpm)
		if _within_whole_number_beat_threshold(adjusted_bpm, round_bpm):
			pass

	# TODO debugging purposes. Remove later.
	print(bpm)
	diffs = np.diff(beats * 1000)
	expected = diffs - 409.0909
	cumsum = np.cumsum(expected)
	for i in range(num_beats - 1):
		print(cumsum[i])
		print(beats[i + 1])
		print()
	raise Exception("Not yet implemented")

def _likely_single_bpm(beats):
	return True
	
def _filter_edge_beats(beats, onsets):
	# Use a sliding window to filter out beats with few neighbouring onsets.
	start_index = _filtered_beats_start(beats, onsets)
	end_index = _filtered_beats_end(beats, onsets)
	if start_index >= end_index:
		# Removed too many beats. Likely too few onsets to work with.
		return beats
	return beats[start_index:end_index + 1]
	
def _filtered_beats_start(beats, onsets):
	num_beats = beats.shape[0]
	for start_index in range(num_beats - EDGE_FILTER_WINDOW_SIZE):
		start = beats[start_index]
		end_index = start_index + EDGE_FILTER_WINDOW_SIZE
		end = beats[end_index]
		num_between = _num_between(onsets, start, end, True, False)
		if num_between >= EDGE_FILTER_WINDOW_SIZE:
			return _beat_start_index_with_onset(beats, onsets, start_index)
	return 0

def _filtered_beats_end(beats, onsets):
	num_beats = beats.shape[0]
	for end_index in range(num_beats - 1, EDGE_FILTER_WINDOW_SIZE - 1, -1):
		start_index = end_index - EDGE_FILTER_WINDOW_SIZE
		start = beats[start_index]
		end = beats[end_index]
		num_between = _num_between(onsets, start, end, False, True)
		if num_between >= EDGE_FILTER_WINDOW_SIZE:
			return _beat_end_index_with_onset(beats, onsets, end_index)
	return beats.shape[0] - 1
	
def _num_between(a, start, end, inclusive_left, inclusive_right):
	left_side = "left" if inclusive_left else "right"
	right_side = "right" if inclusive_right else "left"
	start_index = np.searchsorted(a, start, side=left_side)
	end_index = np.searchsorted(a, end, side=right_side)
	return end_index - start_index
	
def _beat_start_index_with_onset(beats, onsets, left_index):
	num_beats = beats.shape[0]
	for start_index in range(left_index, num_beats - 1):
		start = beats[start_index]
		end = beats[start_index + 1]
		num_between = _num_between(onsets, start, end, True, False)
		if num_between >= 1:
			return start_index
	return left_index
	
def _beat_end_index_with_onset(beats, onsets, right_index):
	num_beats = beats.shape[0]
	for end_index in range(right_index, 0, -1):
		start = beats[end_index - 1]
		end = beats[end_index]
		num_between = _num_between(onsets, start, end, False, True)
		if num_between >= 1:
			return end_index
	return right_index

def _within_whole_number_beat_threshold(bpm, round_bpm):
	percentage_diff = abs(round_bpm - bpm) / bpm * 100
	return percentage_diff < WHOLE_NUMBER_BPM_THRESHOLD

def _sec_to_rounded_milis(milis):
	return int(round(milis * 1000))