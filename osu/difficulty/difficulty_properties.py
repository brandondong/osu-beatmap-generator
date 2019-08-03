import json
import os

STAR_DIFFICULTIES_FILE_NAME = "difficulty.json"


class DifficultyProperties:
    @staticmethod
    def save_training_star_difficulties(id_to_diff_map, output_dir):
        with open(os.path.join(output_dir, STAR_DIFFICULTIES_FILE_NAME), "w") as file:
            json.dump(id_to_diff_map, file)
