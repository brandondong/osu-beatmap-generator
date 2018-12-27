import os
from subprocess import call
import time

import numpy as np

FFMPEG_EXE_PATH = "bin/ffmpeg.exe"
BEATROOT_JAR_PATH = "beatroot.jar"

def create_beatmapset(audio_file, target_diffs, ffmpeg_dir, beatroot_dir):
	current_time = int(time.time())
	ffmpeg_path = os.path.join(ffmpeg_dir, FFMPEG_EXE_PATH)
	beatroot_path = os.path.join(beatroot_dir, BEATROOT_JAR_PATH)

	# Convert mp3 to a temporary wav file for audio processing.
	temp_wav_name = f"{current_time}.wav"
	call([ffmpeg_path, "-i", audio_file, temp_wav_name])
	print(f"Temporary wav file created: {temp_wav_name}.")
	
	# Track beats.
	print("Tracking beats...")
	beats_filename = f"{current_time}.csv"
	call(["java", "-cp", beatroot_path, "at.ofai.music.beatroot.BeatRoot", "-o", beats_filename, temp_wav_name])
	
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
	
	os.remove(temp_wav_name)
	os.remove(beats_filename)