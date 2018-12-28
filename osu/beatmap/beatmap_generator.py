import os
import shutil
from subprocess import call
import time

import numpy as np

from .beat_normalizer import get_timing_info
from models import metadata_predictor

FFMPEG_EXE_PATH = "ffmpeg/bin/ffmpeg.exe"
BEATROOT_JAR_PATH = "beatroot/beatroot.jar"

MP3_NAME = "audio.mp3"
CREATOR = "Skynet"

def create_beatmapset(audio_file, target_diffs, dest_dir, title, artist):
	# Use current time to generate unique file names for temporary files.
	current_time = str(int(time.time()))

	# Convert mp3 to a temporary wav file for audio processing.
	temp_wav_name = f"{current_time}.wav"
	call([FFMPEG_EXE_PATH, "-i", audio_file, temp_wav_name])
	print(f"Temporary wav file created: {temp_wav_name}.")
	
	# Track beats.
	print("Tracking beats...")
	beats_filename = f"{current_time}.csv"
	call(["java", "-cp", BEATROOT_JAR_PATH, "at.ofai.music.beatroot.BeatRoot", "-o", beats_filename, temp_wav_name])
	
	# Read the generated beat timing file.
	beats = _read_and_delete_beats_file(beats_filename)
	
	timing_points = get_timing_info(beats)
	print(f"Number of timing points: {len(timing_points)}.")
	
	# Temporary directory to zip for osz file.
	temp_dir = current_time
	os.makedirs(temp_dir)
	shutil.copyfile(audio_file, os.path.join(temp_dir, MP3_NAME))
	
	# Create beatmaps for each target difficulty.
	for diff in target_diffs:
		_create_beatmap(diff, temp_dir, timing_points, title, artist)
	
	audio_file_basename = os.path.basename(audio_file)[:-4]
	osz_base_filename = os.path.join(dest_dir, audio_file_basename)
	shutil.make_archive(osz_base_filename, "zip", temp_dir)
	os.rename(f"{osz_base_filename}.zip", f"{osz_base_filename}.osz")
	
	os.remove(temp_wav_name)
	shutil.rmtree(temp_dir)
	
def _create_beatmap(diff, dir, timing_points, title, artist):
	filename = os.path.join(dir, f"{artist} - {title} ({CREATOR}) [{diff}].osu")
	with open(filename, encoding="utf-8", mode="w") as file:
		s = f"""osu file format v14

[General]
AudioFilename: {MP3_NAME}
AudioLeadIn: 0
PreviewTime: 0
Countdown: 0
SampleSet: Soft
StackLeniency: 0.7
Mode: 0
LetterboxInBreaks: 0
WidescreenStoryboard: 1

[Editor]
DistanceSpacing: 1.5
BeatDivisor: 4
GridSize: 4
TimelineZoom: 2

[Metadata]
Title:{title}
TitleUnicode:{title}
Artist:{artist}
ArtistUnicode:{artist}
Creator:{CREATOR}
Version:{diff}
Source:
Tags:
BeatmapID:0
BeatmapSetID:-1

[Difficulty]
HPDrainRate:5
CircleSize:4
OverallDifficulty:9.3
ApproachRate:9.2
SliderMultiplier:1.7
SliderTickRate:1

[Events]
//Background and Video events
//Break Periods
//Storyboard Layer 0 (Background)
//Storyboard Layer 1 (Fail)
//Storyboard Layer 2 (Pass)
//Storyboard Layer 3 (Foreground)
//Storyboard Sound Samples

[TimingPoints]
"""
		file.write(s)
		for tp in timing_points:
			file.write(f"{tp[0]},{tp[1]},4,2,22,40,1,0\n")
	
def _read_and_delete_beats_file(beats_filename):
	with open(beats_filename, mode="r") as csv_file:
		contents = csv_file.read()
	data = contents.split(",")
	beats = np.zeros(len(data))
	
	for idx, value in enumerate(data):
		beats[idx] = float(value)
		
	os.remove(beats_filename)
	return beats