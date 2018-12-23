import os

import numpy as np

TRAINING_METADATA_PATH = "../training_data/metadata/"

def load_metadata_dataset():
	"""Loads the metadata training dataset into a (n, 7) numpy array."""

	files = os.listdir(TRAINING_METADATA_PATH)
	num_files = len(files)

	# Data rows are in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
	dataset = np.zeros((num_files, 7))

	for idx, f in enumerate(files):
		filename = os.path.join(TRAINING_METADATA_PATH, f)
		with open(filename, encoding="utf-8", mode="r") as csv_file:
			contents = csv_file.read()
		data = contents.split(",")
		for prop_idx, prop in enumerate(data):
			dataset[idx, prop_idx] = float(prop)
	
	return dataset