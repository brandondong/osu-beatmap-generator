import os
from subprocess import call
import time

FFMPEG_EXE_PATH = "../ffmpeg/bin/ffmpeg.exe"
BEATROOT_PATH = "../beat_tracking/beatroot.jar"

def create_beatmapset(audio_file, target_diffs):
	current_time = int(time.time())

	# Convert mp3 to a temporary wav file for audio processing.
	temp_wav_name = f"{current_time}.wav"
	call([FFMPEG_EXE_PATH, "-i", audio_file, temp_wav_name])
	print(f"Temporary wav file created: {temp_wav_name}.")
	
	# Track beats.
	print("Tracking beats...")
	beats_filename = f"{current_time}.csv"
	call(["java", "-cp", BEATROOT_PATH, "at.ofai.music.beatroot.BeatRoot", "-o", beats_filename, temp_wav_name])
	
	# Read the generated beat timing file.
	with open(beats_filename, mode="r") as csv_file:
		contents = csv_file.read()
	data = contents.split(",")
	print(data)
	
	os.remove(temp_wav_name)
	os.remove(beats_filename)