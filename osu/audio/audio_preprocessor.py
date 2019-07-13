import os
import subprocess

FFMPEG_PATH = "audio/ffmpeg.exe"


class AudioPreprocessor:
    @staticmethod
    def save_training_audio(audio_path, output_dir):
        output_wav = os.path.join(output_dir, "audio.wav")
        subprocess.run(
            [FFMPEG_PATH, "-i", audio_path, output_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not os.path.exists(output_wav):
            raise Exception("MP3 -> WAV conversion failed.")
