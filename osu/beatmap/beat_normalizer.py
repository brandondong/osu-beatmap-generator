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
	timing_points = []
	last_beat = beats[-1] * 1000
	
	# Ignore starting and ending beats found to be likely happening during musical breaks.
	beats = _filter_edge_beats(beats, onsets)
	
	# Check if it matches a whole number bpm by first considering the time between the first and last beat.
	# Optimistically, the length between these beats would be high and would cancel out any noise.
	num_beats = beats.shape[0]
	total_time = beats[-1] - beats[0]
	bpm = (num_beats - 1) / total_time * 60
	round_bpm = round(bpm)
	percentage_diff = abs(round_bpm - bpm) / bpm * 100
	if percentage_diff < WHOLE_NUMBER_BPM_THRESHOLD:
		# Second check is to ensure the beats are fairly constant throughout.
		# Calculate the expected number of seconds between each beat.
		expected_interval = 60 / round_bpm
		# Fit a line to the recorded beat times where the slope is the expected interval and the y-intercept is the starting beat.
		y0 = np.mean(beats) - expected_interval * (num_beats - 1) / 2
		expected_beats = np.arange(num_beats) * expected_interval + y0
		
		avg_diff = np.mean(np.abs(expected_beats - beats))
		avg_diff_percent = avg_diff / expected_interval * 100
		if avg_diff_percent < EXPECTED_INTERVAL_DIFF_THRESHOLD:
			offset = int(round(y0 * 1000))
			timing_points.append((offset, expected_interval * 1000))
			last_beat = expected_beats[-1] * 1000
	
	return timing_points, _map_bpm(timing_points, beats), last_beat
	
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
	
def _map_bpm(timing_points, beats):
	# Map bpm appears to be the longest duration timing point where the last point is to the last object.
	max_length = 0
	max_index = -1
	for i, tp in enumerate(timing_points):
		if i == len(timing_points) - 1:
			# Last point.
			length = beats[-1] * 1000 - tp[0]
		else:
			length = timing_points[i + 1][0] - tp[0]
		if length >= max_length:
			max_length = length
			max_index = i
	
	interval = timing_points[max_index][1]
	return 1 / interval * 60000