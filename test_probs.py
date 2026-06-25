import joblib
import numpy as np
import os

model_path = 'models/random_forest_model.pkl'
features_path = 'models/feature_names.pkl'
encoder_path = 'models/label_encoder.pkl'

model = joblib.load(model_path)
feature_names = joblib.load(features_path)
label_encoder = joblib.load(encoder_path)

# Symptoms from user's screenshot
symptoms = ['chills', 'vomiting', 'high_fever', 'sweating', 'headache', 'muscle_pain']
# The user actually selected 'Fever' instead of 'High Fever' in UI, but the UI might map it to 'high_fever'.
# Let's see what features are actually valid.
print("Symptoms available with 'fever' in name:", [f for f in feature_names if 'fever' in f])

vector = np.zeros(len(feature_names))
for s in symptoms:
    if s in feature_names:
        idx = feature_names.index(s)
        vector[idx] = 1
    else:
        print(f"Warning: symptom {s} not found in feature names!")

vector_2d = vector.reshape(1, -1)
probs = model.predict_proba(vector_2d)[0]

top_indices = np.argsort(probs)[::-1][:5]
print("\nTop predictions:")
for idx in top_indices:
    print(f"{label_encoder.classes_[idx]}: {probs[idx]*100:.2f}%")
