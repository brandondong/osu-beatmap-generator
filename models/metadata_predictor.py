import numpy as np

import models_util

# Load all the models from file.
CS_PREDICTOR = models_util.load_model(models_util.MetadataPredictor.CS)
DRAIN_PREDICTOR = models_util.load_model(models_util.MetadataPredictor.DRAIN)
ACCURACY_PREDICTOR = models_util.load_model(models_util.MetadataPredictor.ACCURACY)
AR_PREDICTOR = models_util.load_model(models_util.MetadataPredictor.AR)

def predict_metadata(difficulty, bpm):
	# Single input to predict.
	X = np.zeros((1, 2))
	X[0, 0] = difficulty
	X[0, 1] = bpm
	cs = CS_PREDICTOR.predict(X)[0]
	drain = DRAIN_PREDICTOR.predict(X)[0]
	accuracy = ACCURACY_PREDICTOR.predict(X)[0]
	ar = AR_PREDICTOR.predict(X)[0]
	return cs, drain, accuracy, ar