from beatmap import beatmap_generator

FFMPEG_DIR = "ffmpeg/"
BEATROOT_DIR = "beatroot/"

beatmap_generator.create_beatmapset("ffmpeg/test.mp3", [10], FFMPEG_DIR, BEATROOT_DIR)