import math

import numpy as np

# Timing offset to handle a beat tracker's consistent deviation.
BEAT_TRACKING_TIMING_OFFSET = 0.034

# Window size used for filtering out start and end beats.
EDGE_FILTER_WINDOW_SIZE = 4

# Allowable average normalized distance from the mean among interval lengths to be considered a single bpm.
SINGLE_BPM_THRESHOLD = 0.05

# The fraction of closest onsets to use when fitting a beat sequence.
CLOSEST_ONSETS_FIT_FRACTION = 0.45

# The fraction of closest onsets to use when evaluating a beat sequence.
CLOSEST_ONSETS_EVALUATION_FRACTION = 0.9

def get_timing_info(beats, onsets):
	"""Extracts beatmap timing info from beat tracking data.
	
	Returns a list of timing points, the beatmap bpm, and the offset of the last beat."""

	beats = beats - BEAT_TRACKING_TIMING_OFFSET
	onsets = onsets - BEAT_TRACKING_TIMING_OFFSET
	
	# Ignore starting and ending beats found to be devoid of onsets as we do not want those sections to be mapped.
	beats = _filter_edge_beats(beats, onsets)
	intervals = np.diff(beats)
	
	if not _likely_single_bpm(beats, intervals):
		return _handle_multi_bpm(beats, intervals)
	
	# Single bpm case. Calculate the overall bpm from the detected beats.
	num_intervals = intervals.size
	total_time = beats[-1] - beats[0]
	bpm = num_intervals / total_time * 60

	# The true bpm is assumed to be a whole number. Consider bpm's corresponding to the ceiling and floor.
	candidate_bpms = []
	candidate_bpms.append(math.ceil(bpm))
	candidate_bpms.append(math.floor(bpm))
	# And bpm's corresponding to the ceiling and floor if every one and a half beats were misclassified as a single beat which can happen in practice.
	multiplied_bpm = bpm * 1.5
	candidate_bpms.append(math.ceil(multiplied_bpm))
	candidate_bpms.append(math.floor(multiplied_bpm))

	# Find the best sequence.
	best_score = math.inf
	best_sequence = None
	best_bpm = None
	for candidate_bpm in candidate_bpms:
		sequence = _generate_beats(candidate_bpm, beats)
		# Shift the beats to fit well with the observed onsets.
		closest_onsets = _closest_onsets(sequence, onsets)
		sequence = _fit_beats_to_closest_onsets(sequence, closest_onsets)
		# Calculate a score.
		score = _score_beats_to_onsets(sequence, closest_onsets)
		if score < best_score:
			best_score = score
			best_sequence = sequence
			best_bpm = candidate_bpm
	
	first_beat = _sec_to_rounded_milis(best_sequence[0])
	last_beat = _sec_to_rounded_milis(best_sequence[-1])
	interval_ms = 60000 / best_bpm
	timing_points = [(first_beat, interval_ms)]
	return timing_points, best_bpm, last_beat

def _likely_single_bpm(beats, intervals):
	# Calculate the average distance from the mean.
	avg = np.mean(intervals)
	avg_dist = np.mean(np.abs(intervals - avg))
	# And normalize that value.
	normalized_avg_dist = avg_dist / avg
	return normalized_avg_dist <= SINGLE_BPM_THRESHOLD

def _handle_multi_bpm(beats, intervals):
	# Create individual timing points for each beat interval.
	timing_points = []
	for i in range(beats.size - 1):
		offset = _sec_to_rounded_milis(beats[i])
		timing_points.append((offset, intervals[i] * 1000))
	last_beat = _sec_to_rounded_milis(beats[-1])
	return timing_points, 60 / np.median(intervals), last_beat

def _sec_to_rounded_milis(milis):
	return int(round(milis * 1000))
	
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

def _generate_beats(bpm, beats):
	# Generate a sequence that starts on the first detected beat and ends before the last.
	interval = 60 / bpm
	start = beats[0]
	end = beats[-1]
	num_intervals_within = int((end - start) / interval)
	return np.arange(num_intervals_within + 1) * interval + start

def _closest_onsets(beats, onsets):
	idx = np.searchsorted(onsets, beats, side="left")
	# The closest is at either idx or idx - 1.
	idx1 = np.clip(idx, None, onsets.size - 1)
	idx2 = np.clip(idx - 1, 0, None)
	diff1 = np.abs(onsets[idx1] - beats)
	diff2 = np.abs(onsets[idx2] - beats)
	needs_adjustment = diff2 < diff1
	return onsets[idx1 - needs_adjustment]

def _fit_beats_to_closest_onsets(beats, closest_onsets):
	# Shift the sequence to fit with the very nearest onsets. The hope is that for the correct bpm case, these onsets fall on true beats.
	num_to_fit = max(int(beats.size * CLOSEST_ONSETS_FIT_FRACTION), 1)
	diff = closest_onsets - beats
	dist = np.abs(diff)
	idx = np.argpartition(dist, num_to_fit - 1)[:num_to_fit]
	# Fit the beat sequence line by minimizing the squared distances.
	adjustment = np.mean(diff[idx])
	return beats + adjustment

def _score_beats_to_onsets(beats, closest_onsets):
	# Score by average distance to the nearest onsets normalized by interval length.
	num_to_eval = max(int(beats.size * CLOSEST_ONSETS_EVALUATION_FRACTION), 1)
	dist = np.abs(closest_onsets - beats)
	dist = np.partition(dist, num_to_eval - 1)[:num_to_eval]
	interval = beats[1] - beats[0]
	return np.mean(dist) / interval