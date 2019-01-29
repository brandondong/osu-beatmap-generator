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

def create_beatmapset(audio_file, dst_file, target_diffs, title, artist):
	# Use current time to generate unique file names for temporary files.
	current_time = str(int(time.time()))

	# Convert mp3 to a temporary wav file for audio processing.
	temp_wav_name = f"{current_time}.wav"
	call([FFMPEG_EXE_PATH, "-i", audio_file, temp_wav_name])
	print(f"Temporary wav file created: {temp_wav_name}.")
	
	# Track beats.
	print("Tracking beats...")
	beats_filename = f"{current_time}.csv"
	call(["java", "-cp", BEATROOT_JAR_PATH, "at.ofai.music.beatroot.BeatRoot", "-x", beats_filename, temp_wav_name])
	
	# Read the generated beat timing file.
	beats, onsets = _read_and_delete_beats_file(beats_filename)
	
	timing_points, map_bpm, last_beat = get_timing_info(beats, onsets)
	num_timing_points = len(timing_points)
	if num_timing_points == 1:
		print(f"Single timing point created. Offset: {timing_points[0][0]}.")
	else:
		print("Possible poor results due to beat tracking encountering difficulties. For best performance, use single bpm songs with distinctive percussive onsets and a lack of heavy syncopation." )
	print(f"Calculated beatmap bpm: {map_bpm}.")
	
	# Temporary directory to zip for osz file.
	temp_dir = current_time
	os.makedirs(temp_dir)
	shutil.copyfile(audio_file, os.path.join(temp_dir, MP3_NAME))
	
	# Create beatmaps for each target difficulty.
	for diff in target_diffs:
		_create_beatmap(diff, temp_dir, timing_points, map_bpm, title, artist)
	
	shutil.make_archive(temp_dir, "zip", temp_dir)
	shutil.move(f"{temp_dir}.zip", dst_file)
	
	os.remove(temp_wav_name)
	shutil.rmtree(temp_dir)
	
def _create_beatmap(diff, dir, timing_points, map_bpm, title, artist):
	title_ascii = _remove_non_ascii(title)
	artist_ascii = _remove_non_ascii(artist)
	filename = os.path.join(dir, f"{artist_ascii} - {title_ascii} ({CREATOR}) [{diff}].osu")
	cs, drain, accuracy, ar = metadata_predictor.predict_metadata(diff, map_bpm)
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
Title:{title_ascii}
TitleUnicode:{title}
Artist:{artist_ascii}
ArtistUnicode:{artist}
Creator:{CREATOR}
Version:{diff}
Source:
Tags:
BeatmapID:0
BeatmapSetID:-1

[Difficulty]
HPDrainRate:{drain}
CircleSize:{cs}
OverallDifficulty:{accuracy}
ApproachRate:{ar}
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
	
def _read_and_delete_beats_file(filename):
	with open(filename, mode="r") as csv_file:
		beat_contents = csv_file.readline()
		onset_contents = csv_file.readline()
	
	beats = _parse_to_np_array(beat_contents)
	onsets = _parse_to_np_array(onset_contents)
		
	os.remove(filename)
	return beats, onsets
	
def _parse_to_np_array(s):
	data = s.split(",")
	a = np.zeros(len(data))
	
	for idx, value in enumerate(data):
		a[idx] = float(value)
	return a

def _remove_non_ascii(s):
	return s.encode("ascii", errors="ignore").decode()