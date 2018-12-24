from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import models_util

dataset = models_util.load_metadata_dataset()
# Difficulty and BPM input features.
X_train = dataset[:,0:2]
y = dataset[:,6]

model = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(10,)))
model.fit(X_train, y)

models_util.save_model(model, models_util.MetadataPredictor.AR)
print("Trained model saved.")