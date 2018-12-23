import os
import sys

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

TRAINING_METADATA_PATH = "../training_data/metadata/"

NUM_CROSS_VALIDATIONS = 20

output_column = 3
if len(sys.argv) == 2:
	output_column = int(sys.argv[1])

files = os.listdir(TRAINING_METADATA_PATH)
num_files = len(files)

# Data rows are in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
dataset = np.zeros((num_files, 7))

for idx, f in enumerate(files):
	filename = os.path.join(TRAINING_METADATA_PATH, f)
	with open(filename, encoding="utf-8", mode="r") as csv_file:
		contents = csv_file.read()
	data = contents.split(",")
	# Strip the ending new line added during the file write.
	data[-1].rstrip()
	for prop_idx, prop in enumerate(data):
		dataset[idx, prop_idx] = float(prop)

# Randomize the dataset.
np.random.shuffle(dataset)
		
# Try a linear regression approach.
# From the graphs, it appears only the difficulty matters with a logarithmic relationship to all output features.
model = LinearRegression()

X_train = dataset[:,0].reshape((-1, 1))
y = dataset[:,output_column]

# Difficulties are all > 0.
scores = cross_val_score(model, np.log(X_train), y, cv=NUM_CROSS_VALIDATIONS)
print(f"Cross validation score for linear regression: {scores.mean()}.")

# Try using a neural net still with only the difficulty input feature.
scaler = StandardScaler()
# Normalize the data.
# Cheating a bit by also using the validation data but should have little effect with more folds.
scaler.fit(X_train)

model = MLPRegressor(hidden_layer_sizes=(5,))
scores = cross_val_score(model, scaler.transform(X_train), y, cv=NUM_CROSS_VALIDATIONS)
print(f"Cross validation score for neural network: {scores.mean()}.")

# Try using a neural net with some subset of possible input features.
scaler = StandardScaler()
# Normalize the data.
X_train = dataset[:,0:2]
scaler.fit(X_train)

model = MLPRegressor(hidden_layer_sizes=(6,))
scores = cross_val_score(model, scaler.transform(X_train), y, cv=NUM_CROSS_VALIDATIONS)
print(f"Cross validation score for second neural network: {scores.mean()}.")