import os

import matplotlib.pyplot as plt
import numpy as np

from models import models_util

DIFFICULTY_LABEL = "Star Difficulty"
BPM_LABEL = "BPM"
LENGTH_LABEL = "Length"
CS_LABEL = "Circle Size"
DRAIN_LABEL = "HP Drain"
ACCURACY_LABEL = "Accuracy"
AR_LABEL = "Approach Rate"

SAVE_FOLDER = "visualization/"

def print_property_values(labels, values):
	for idx, value in enumerate(values):
		print(f"{labels[idx]}: {value}")
	print()

# Data rows are in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
labels = [DIFFICULTY_LABEL, BPM_LABEL, LENGTH_LABEL, CS_LABEL, DRAIN_LABEL, ACCURACY_LABEL, AR_LABEL]
filename_labels = []
for label in labels:
	filename_labels.append(label.lower().replace(" ", "_"))
# Keep track of each property in separate rows.
points = np.transpose(models_util.load_metadata_dataset())

mins = points.min(axis=-1)
maxes = points.max(axis=-1)
means = np.mean(points, axis=-1)

print("Minimum values:")
print_property_values(labels, mins)

print("Maximum values:")
print_property_values(labels, maxes)

print("Mean values:")
print_property_values(labels, means)

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
		image_name = os.path.join(SAVE_FOLDER, f"{y_file_label}_vs_{x_file_label}.png")
		print(f"Saving graph to {image_name}.")
		plt.savefig(image_name)