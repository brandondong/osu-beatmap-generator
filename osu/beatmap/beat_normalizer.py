import numpy as np

WHOLE_NUMBER_BPM_THRESHOLD = 0.05

EXPECTED_INTERVAL_DIFF_THRESHOLD = 10

def get_timing_info(beats):
	# Analyze each beat section separated by breaks.
	timing_points = []
	
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
			timing_points.append((int(round(y0 * 1000)), expected_interval * 1000))
		
	return timing_points