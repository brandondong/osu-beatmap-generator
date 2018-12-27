import numpy as np

from .models_util import load_model, MetadataPredictor

# Load all the models from file.
CS_PREDICTOR = load_model(MetadataPredictor.CS)
DRAIN_PREDICTOR = load_model(MetadataPredictor.DRAIN)
ACCURACY_PREDICTOR = load_model(MetadataPredictor.ACCURACY)
AR_PREDICTOR = load_model(MetadataPredictor.AR)

MIN_VALUE = 0
MAX_VALUE = 10

def predict_metadata(difficulty, bpm):
	# Single input to predict.
	X = np.zeros((1, 2))
	X[0, 0] = difficulty
	X[0, 1] = bpm
	cs = CS_PREDICTOR.predict(X)[0]
	drain = DRAIN_PREDICTOR.predict(X)[0]
	accuracy = ACCURACY_PREDICTOR.predict(X)[0]
	ar = AR_PREDICTOR.predict(X)[0]
	return _clamp(cs), _clamp(drain), _clamp(accuracy), _clamp(ar)
	
def _clamp(value):
	return min(MAX_VALUE, max(MIN_VALUE, value))