"""
Medical Disease Diagnosis System - Model Training Script
=========================================================
Trains a Random Forest Classifier on the symptom-disease dataset.
Also trains a Decision Tree for comparison.
Saves the trained model, label encoder, and feature names.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import warnings
warnings.filterwarnings('ignore')


def load_and_preprocess_data(data_path):
    """Load the dataset and preprocess it."""
    print("=" * 60)
    print("  Medical Disease Diagnosis - Model Training")
    print("=" * 60)
    print(f"\n[1/5] Loading dataset from: {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"  → Dataset shape: {df.shape}")
    print(f"  → Number of diseases: {df['disease'].nunique()}")
    print(f"  → Number of symptoms: {df.shape[1] - 1}")
    print(f"  → Total samples: {df.shape[0]}")
    print(f"  → Diseases: {', '.join(sorted(df['disease'].unique()))}")
    
    # Separate features and labels
    X = df.drop('disease', axis=1)
    y = df['disease']
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    feature_names = list(X.columns)
    
    return X, y_encoded, label_encoder, feature_names, df


def train_random_forest(X_train, X_test, y_train, y_test, label_encoder):
    """Train a Random Forest Classifier."""
    print("\n[2/5] Training Random Forest Classifier...")
    
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # Predictions
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"  → Training accuracy: {rf_model.score(X_train, y_train) * 100:.2f}%")
    print(f"  → Testing accuracy: {accuracy * 100:.2f}%")
    
    # Cross-validation
    print("\n[3/5] Performing 5-fold Cross-Validation...")
    cv_scores = cross_val_score(rf_model, 
                                 np.vstack([X_train, X_test]), 
                                 np.concatenate([y_train, y_test]), 
                                 cv=5, scoring='accuracy')
    print(f"  → CV Scores: {[f'{s:.4f}' for s in cv_scores]}")
    print(f"  → Mean CV Accuracy: {cv_scores.mean() * 100:.2f}% (±{cv_scores.std() * 100:.2f}%)")
    
    # Classification report
    print("\n  Classification Report (Random Forest):")
    print("  " + "-" * 55)
    report = classification_report(y_test, y_pred, 
                                    target_names=label_encoder.classes_,
                                    zero_division=0)
    for line in report.split('\n'):
        print(f"  {line}")
    
    return rf_model


def train_decision_tree(X_train, X_test, y_train, y_test, label_encoder):
    """Train a Decision Tree Classifier for comparison."""
    print("\n[4/5] Training Decision Tree Classifier (comparison)...")
    
    dt_model = DecisionTreeClassifier(
        max_depth=None,
        min_samples_split=2,
        random_state=42
    )
    
    dt_model.fit(X_train, y_train)
    
    y_pred = dt_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"  → Training accuracy: {dt_model.score(X_train, y_train) * 100:.2f}%")
    print(f"  → Testing accuracy: {accuracy * 100:.2f}%")
    
    return dt_model


def save_model(model, label_encoder, feature_names, models_dir):
    """Save the trained model and related files."""
    print(f"\n[5/5] Saving model artifacts to: {models_dir}")
    
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'random_forest_model.pkl')
    encoder_path = os.path.join(models_dir, 'label_encoder.pkl')
    features_path = os.path.join(models_dir, 'feature_names.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump(label_encoder, encoder_path)
    joblib.dump(feature_names, features_path)
    
    print(f"  → Model saved: {model_path}")
    print(f"  → Label encoder saved: {encoder_path}")
    print(f"  → Feature names saved: {features_path}")
    
    # Print model file sizes
    for path in [model_path, encoder_path, features_path]:
        size = os.path.getsize(path)
        print(f"  → {os.path.basename(path)}: {size / 1024:.1f} KB")


def print_feature_importance(model, feature_names, top_n=20):
    """Print the top N most important features."""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print(f"\n  Top {top_n} Most Important Symptoms:")
    print("  " + "-" * 40)
    for i in range(min(top_n, len(feature_names))):
        name = feature_names[indices[i]].replace('_', ' ').title()
        print(f"  {i+1:3d}. {name:30s} {importances[indices[i]]:.4f}")


def main():
    """Main training pipeline."""
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'dataset.csv')
    models_dir = os.path.join(base_dir, 'models')
    
    # Load data
    X, y, label_encoder, feature_names, df = load_and_preprocess_data(data_path)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    print(f"\n  Train set: {X_train.shape[0]} samples")
    print(f"  Test set: {X_test.shape[0]} samples")
    
    # Train Random Forest
    rf_model = train_random_forest(X_train, X_test, y_train, y_test, label_encoder)
    
    # Train Decision Tree for comparison
    dt_model = train_decision_tree(X_train, X_test, y_train, y_test, label_encoder)
    
    # Feature importance
    print_feature_importance(rf_model, feature_names)
    
    # Save model
    save_model(rf_model, label_encoder, feature_names, models_dir)
    
    print("\n" + "=" * 60)
    print("  ✓ Training complete! Model is ready for deployment.")
    print("=" * 60)


if __name__ == '__main__':
    main()
