import sys

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import models_util

TRAINING_METADATA_PATH = "../training_data/metadata/"

NUM_CV_FOLDS = 5

output_column = 3
if len(sys.argv) == 2:
	output_column = int(sys.argv[1])

# Data rows are in the format of [difficulty_rating],[bpm],[total_length],[cs],[drain],[accuracy],[ar].
dataset = models_util.load_metadata_dataset()

# Randomize the dataset.
np.random.shuffle(dataset)

X_train = dataset[:,0].reshape((-1, 1))
y = dataset[:,output_column]

# Try a linear regression approach.
# From the graphs, it appears only the difficulty matters with a logarithmic relationship to all output features.
model = LinearRegression()

# Difficulties are all > 0.
scores = cross_val_score(model, np.log(X_train), y, cv=NUM_CV_FOLDS)
print(f"Cross validation score for linear regression: {scores.mean()}.")

# Try using a neural net still with only the difficulty input feature.
model = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(5,)))

scores = cross_val_score(model, X_train, y, cv=NUM_CV_FOLDS)
print(f"Cross validation score for neural network: {scores.mean()}.")

# Try with some subset of possible input features.
X_train = dataset[:,0:2]

# Linear regression.
model = LinearRegression()
transformed = np.stack((np.log(dataset[:,0]), dataset[:,1]), axis=-1)
scores = cross_val_score(model, transformed, y, cv=NUM_CV_FOLDS)
print(f"Cross validation score for second linear regression: {scores.mean()}.")

# Neural net.
model = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(6,)))

scores = cross_val_score(model, X_train, y, cv=NUM_CV_FOLDS)
print(f"Cross validation score for second neural network: {scores.mean()}.")