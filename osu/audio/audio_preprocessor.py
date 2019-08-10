import os
import subprocess

import numpy as np

FFMPEG_PATH = "osu/audio/ffmpeg.exe"
BEATROOT_JAR_PATH = "osu/audio/beatroot.jar"
OUTPUT_FILE_NAME = "audio.csv"


class AudioPreprocessor:
    @staticmethod
    def save_training_audio(audio_path, output_dir):
        output_wav = os.path.join(output_dir, "audio.wav")
        subprocess.run(
            [FFMPEG_PATH, "-i", audio_path, output_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(output_wav):
            raise Exception("MP3 -> WAV conversion failed.")

        output_csv = os.path.join(output_dir, OUTPUT_FILE_NAME)
        subprocess.run(["java", "-cp", BEATROOT_JAR_PATH,
                        "at.ofai.music.beatroot.BeatRoot", "-O", "-o", output_csv, output_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(output_wav)
        if not os.path.exists(output_csv):
            raise Exception("Onset processing failed.")

    @staticmethod
    def read_training_audio(dir):
        onsets_file = os.path.join(dir, OUTPUT_FILE_NAME)
        with open(onsets_file, "r") as f:
            onsets = f.readline().split(",")
            # Get rid of the newline.
            onsets[-1] = onsets[-1][:-1]
            onsets = list(map(lambda o: float(o), onsets))
            return np.array(onsets)
