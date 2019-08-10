import os

TRAINING_PATH = "osu/training_data"


def training_path(beatmapset_id=None):
    if beatmapset_id is None:
        return TRAINING_PATH
    return os.path.join(TRAINING_PATH, beatmapset_id)


def is_osu_file(file):
    _, ext = os.path.splitext(file)
    return ext.lower() == ".osu"
