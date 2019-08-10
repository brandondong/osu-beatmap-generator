import os

from osu.audio.audio_preprocessor import AudioPreprocessor
from osu.beatmap.beatmap import Beatmap
from osu.difficulty.difficulty_properties import DifficultyProperties
from osu.training.utils import is_osu_file, training_path

training_folder = training_path()
for beatmapset in os.listdir(training_folder):
    beatmapset_path = os.path.join(training_folder, beatmapset)
    files = os.listdir(beatmapset_path)
    # Check that this is not just a marker for a failed beatmapset during collection.
    if len(files) > 0:
        onsets = AudioPreprocessor.read_training_audio(beatmapset_path)
        difficulty_json = DifficultyProperties.read_training_star_difficulties(
            beatmapset_path)
        for file in files:
            if is_osu_file(file):
                osu_file = os.path.join(beatmapset_path, file)
                beatmap = Beatmap.from_osu_file(osu_file)
                timeseries_inputs, labels = beatmap.get_timeseries_training_data(
                    onsets)
