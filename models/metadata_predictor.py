import numpy as np

import models_util

# Load all the models from file.
CS_PREDICTOR = models_util.load_model(models_util.MetadataPredictor.CS)

def predict_metadata(difficulty, bpm):
	# Single input to predict.
	X = np.zeros((1, 2))
	X[0, 0] = difficulty
	X[0, 1] = bpm
	cs = CS_PREDICTOR.predict(X)[0]
	return cs