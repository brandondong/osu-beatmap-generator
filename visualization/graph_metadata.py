import os

import matplotlib.pyplot as plt
import numpy as np

TRAINING_METADATA_PATH = "../training_data/metadata/"

DIFFICULTY_LABEL = "Star Difficulty"
BPM_LABEL = "BPM"
LENGTH_LABEL = "Length"
CS_LABEL = "Cirlce Size"
DRAIN_LABEL = "HP Drain"
ACCURACY_LABEL = "Accuracy"
AR_LABEL = "Approach Rate"

files = os.listdir(TRAINING_METADATA_PATH)
num_files = len(files)

# Data rows are in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
labels = [DIFFICULTY_LABEL, BPM_LABEL, LENGTH_LABEL, CS_LABEL, DRAIN_LABEL, ACCURACY_LABEL, AR_LABEL]
filename_labels = []
for label in labels:
	filename_labels.append(label.lower().replace(" ", "_"))
# Keep track of each property in separate rows.
points = np.zeros((7, num_files))

for idx, f in enumerate(files):
	filename = os.path.join(TRAINING_METADATA_PATH, f)
	with open(filename, encoding="utf-8", mode="r") as csv_file:
		contents = csv_file.read()
	data = contents.split(",")
	# Strip the ending new line added during the file write.
	data[-1].rstrip()
	for prop_idx, prop in enumerate(data):
		points[prop_idx, idx] = float(prop)

mins = points.min(axis=-1)
maxes = points.max(axis=-1)

print("Minimum values:")
for idx, value in enumerate(mins):
	print(f"{labels[idx]}: {value}")
print()

print("Maximum values:")
for idx, value in enumerate(maxes):
	print(f"{labels[idx]}: {value}")
print()

# Plot graphs for each input output feature pair.
for i in range(3):
	for j in range(3, 7):
		plt.hexbin(points[i], points[j], gridsize=50, cmap="inferno")
		plt.axis([mins[i], maxes[i], mins[j], maxes[j]])
		x_label = labels[i]
		y_label = labels[j]
		plt.title(f"{y_label} vs {x_label}")
		plt.xlabel(x_label)
		plt.ylabel(y_label)
		
		x_file_label = filename_labels[i]
		y_file_label = filename_labels[j]
		image_name = f"{y_file_label}_vs_{x_file_label}.png"
		print(f"Saving graph to {image_name}.")
		plt.savefig(image_name)