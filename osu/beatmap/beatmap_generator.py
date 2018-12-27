import os
from subprocess import call
import time

import numpy as np

from models import metadata_predictor

FFMPEG_EXE_PATH = "ffmpeg/bin/ffmpeg.exe"
BEATROOT_JAR_PATH = "beatroot/beatroot.jar"

def create_beatmapset(audio_file, target_diffs):
	current_time = int(time.time())

	# Convert mp3 to a temporary wav file for audio processing.
	temp_wav_name = f"{current_time}.wav"
	call([FFMPEG_EXE_PATH, "-i", audio_file, temp_wav_name])
	print(f"Temporary wav file created: {temp_wav_name}.")
	
	# Track beats.
	print("Tracking beats...")
	beats_filename = f"{current_time}.csv"
	call(["java", "-cp", BEATROOT_JAR_PATH, "at.ofai.music.beatroot.BeatRoot", "-o", beats_filename, temp_wav_name])
	
	# Read the generated beat timing file.
	with open(beats_filename, mode="r") as csv_file:
		contents = csv_file.read()
	data = contents.split(",")
	beats = np.zeros(len(data))
	
	for idx, value in enumerate(data):
		beats[idx] = float(value)
	intervals = np.diff(beats * 1000)
	print(np.mean(intervals))
	print(intervals.min())
	print(intervals.max())
	print(60 * (len(data) - 1) / (beats[len(data) - 1] - beats[0]))
	
	# Create beatmaps for each target difficulty.
	for diff in target_diffs:
		print(metadata_predictor.predict_metadata(diff, 100))
	
	os.remove(temp_wav_name)
	os.remove(beats_filename)