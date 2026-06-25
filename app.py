"""
Medical Disease Diagnosis System - Flask Application
=====================================================
REST API backend that serves ML predictions and disease information.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import numpy as np
import joblib
import shap
from flask_sqlalchemy import SQLAlchemy

# ─── App Configuration ───────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')
KNOWLEDGE_DIR = os.path.join(BASE_DIR, 'knowledge')
DB_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)

# ─── Database Configuration ──────────────────────────────────────
# Use PostgreSQL if DATABASE_URL is set, else local SQLite
database_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(DB_DIR, 'diagnosis_history.db')}")
# Fix older Heroku postgres:// urls
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DiagnosisHistory(db.Model):
    __tablename__ = 'diagnosis_history'
    id = db.Column(db.Integer, primary_key=True)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    top_predictions = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)

# ─── Global Variables ────────────────────────────────────────────
model = None
label_encoder = None
feature_names = None
disease_knowledge = None
explainer = None


# ─── Database Setup ──────────────────────────────────────────────
def init_db():
    """Initialize the database with required tables."""
    with app.app_context():
        db.create_all()


# ─── Model Loading ───────────────────────────────────────────────
def load_model():
    """Load the trained ML model, explainer, and related files."""
    global model, label_encoder, feature_names, explainer
    
    try:
        model_path = os.path.join(MODELS_DIR, 'random_forest_model.pkl')
        encoder_path = os.path.join(MODELS_DIR, 'label_encoder.pkl')
        features_path = os.path.join(MODELS_DIR, 'feature_names.pkl')
        
        if not all(os.path.exists(p) for p in [model_path, encoder_path, features_path]):
            app.logger.warning("Model files not found. Please run train_model.py first.")
            return False
        
        model = joblib.load(model_path)
        label_encoder = joblib.load(encoder_path)
        feature_names = joblib.load(features_path)
        
        # Initialize SHAP Explainer
        explainer = shap.TreeExplainer(model)
        
        app.logger.info(f"Model loaded successfully ({len(feature_names)} features, {len(label_encoder.classes_)} diseases)")
        return True
    except Exception as e:
        app.logger.error(f"Error loading model: {e}")
        return False


def load_knowledge():
    """Load the disease knowledge base."""
    global disease_knowledge
    
    try:
        knowledge_path = os.path.join(KNOWLEDGE_DIR, 'diseases.json')
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            disease_knowledge = json.load(f)
        app.logger.info(f"Knowledge base loaded ({len(disease_knowledge)} diseases)")
        return True
    except Exception as e:
        app.logger.error(f"Error loading knowledge base: {e}")
        disease_knowledge = {}
        return False


# ─── Routes ──────────────────────────────────────────────────────
@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Return the list of all available symptoms."""
    if feature_names is None:
        return jsonify({'error': 'Model not loaded. Run train_model.py first.'}), 503
    
    # Format symptom names for display
    symptoms = []
    for name in feature_names:
        display_name = name.replace('_', ' ').title()
        symptoms.append({
            'id': name,
            'name': display_name
        })
    
    # Sort alphabetically
    symptoms.sort(key=lambda x: x['name'])
    
    return jsonify({
        'symptoms': symptoms,
        'total': len(symptoms)
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict disease based on selected symptoms."""
    if model is None or label_encoder is None or feature_names is None:
        return jsonify({'error': 'Model not loaded. Run train_model.py first.'}), 503
    
    data = request.get_json()
    if not data or 'symptoms' not in data:
        return jsonify({'error': 'No symptoms provided.'}), 400
    
    selected_symptoms = data['symptoms']
    if not selected_symptoms:
        return jsonify({'error': 'Please select at least one symptom.'}), 400
    
    # Create feature vector
    feature_vector = np.zeros(len(feature_names))
    valid_symptoms = []
    
    for symptom in selected_symptoms:
        if symptom in feature_names:
            idx = feature_names.index(symptom)
            feature_vector[idx] = 1
            valid_symptoms.append(symptom)
    
    if not valid_symptoms:
        return jsonify({'error': 'No valid symptoms found.'}), 400
    
    # Predict
    feature_vector_2d = feature_vector.reshape(1, -1)
    prediction = model.predict(feature_vector_2d)[0]
    probabilities = model.predict_proba(feature_vector_2d)[0]
    
    predicted_disease = label_encoder.classes_[prediction]
    confidence = round(float(probabilities[prediction]) * 100, 2)
    
    # Get top 5 predictions (needed for both high/low confidence history)
    top_indices = np.argsort(probabilities)[::-1][:5]
    top_predictions = []
    for idx in top_indices:
        prob = probabilities[idx]
        if prob > 0.01:
            top_predictions.append({
                'disease': label_encoder.classes_[idx],
                'probability': round(float(prob) * 100, 2)
            })

    # Save to history via SQLAlchemy
    session_id = data.get('session_id', str(uuid.uuid4()))
    try:
        history_entry = DiagnosisHistory(
            symptoms=json.dumps(valid_symptoms),
            predicted_disease="Uncertain" if confidence < 80.0 else predicted_disease,
            confidence=confidence,
            top_predictions=json.dumps(top_predictions),
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        db.session.add(history_entry)
        db.session.commit()
    except Exception as e:
        app.logger.warning(f"Could not save to history: {e}")
        db.session.rollback()

    # === 80% CONFIDENCE THRESHOLD ===
    if confidence < 80.0:
        return jsonify({
            'low_confidence': True,
            'message': 'Insufficient symptom data for a high-confidence diagnosis. Please provide more specific symptoms or consult a doctor.',
            'confidence': confidence,
            'top_predictions': [
                {'disease': label_encoder.classes_[i], 'probability': round(float(probabilities[i])*100, 2)}
                for i in np.argsort(probabilities)[::-1][:3] if probabilities[i] > 0.05
            ]
        })
    top_indices = np.argsort(probabilities)[::-1][:5]
    top_predictions = []
    
    for idx in top_indices:
        disease_name = label_encoder.classes_[idx]
        prob = probabilities[idx]
        if prob > 0.01:  # Only include if probability > 1%
            top_predictions.append({
                'disease': disease_name,
                'probability': round(float(prob) * 100, 2)
            })
            
    # === SHAP EXPLAINABILITY ===
    shap_explanations = []
    try:
        # Get SHAP values for the specific prediction class
        shap_values = explainer.shap_values(feature_vector_2d)
        
        # Handle different SHAP versions' return types
        if isinstance(shap_values, list):
            class_shap_values = shap_values[prediction][0]
        else:
            class_shap_values = shap_values[0, :, prediction] if len(shap_values.shape) == 3 else shap_values[0]
            
        # Get indices of positive features that contributed the most
        feature_contributions = []
        for i, val in enumerate(class_shap_values):
            if feature_vector[i] == 1 and val > 0: # Only look at present symptoms that contributed positively
                feature_contributions.append((feature_names[i], float(val)))
                
        # Sort by highest contribution
        feature_contributions.sort(key=lambda x: x[1], reverse=True)
        
        # Format for frontend
        total_shap = sum(abs(v) for _, v in feature_contributions)
        if total_shap > 0:
            for feat, val in feature_contributions[:3]:
                percentage = round((val / total_shap) * 100)
                shap_explanations.append({
                    'symptom': feat.replace('_', ' ').title(),
                    'contribution': percentage
                })
    except Exception as e:
        app.logger.error(f"SHAP explanation failed: {e}")
    
    # Get disease knowledge
    knowledge = disease_knowledge.get(predicted_disease, {})
    
    # Build response
    response = {
        'low_confidence': False,
        'predicted_disease': predicted_disease,
        'confidence': confidence,
        'top_predictions': top_predictions,
        'selected_symptoms': [s.replace('_', ' ').title() for s in valid_symptoms],
        'shap_explanations': shap_explanations,
        'knowledge': {
            'description': knowledge.get('description', 'No description available.'),
            'causes': knowledge.get('causes', []),
            'common_symptoms': knowledge.get('common_symptoms', []),
            'risk_factors': knowledge.get('risk_factors', []),
            'prevention': knowledge.get('prevention', []),
            'home_remedies': knowledge.get('home_remedies', []),
            'general_advice': knowledge.get('general_advice', []),
            'when_to_see_doctor': knowledge.get('when_to_see_doctor', []),
            'clinical_treatments': knowledge.get('clinical_treatments', [])
        }
    }
    
    return jsonify(response)


@app.route('/api/history', methods=['GET'])
def get_history():
    """Return diagnosis history for a session."""
    session_id = request.args.get('session_id', '')
    
    if not session_id:
        return jsonify({'history': []})
    
    try:
        records = DiagnosisHistory.query.filter_by(session_id=session_id).order_by(DiagnosisHistory.timestamp.desc()).limit(20).all()
        
        history = []
        for row in records:
            history.append({
                'id': row.id,
                'symptoms': json.loads(row.symptoms),
                'predicted_disease': row.predicted_disease,
                'confidence': row.confidence,
                'timestamp': row.timestamp
            })
        
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'history': [], 'error': str(e)})


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear diagnosis history for a session."""
    data = request.get_json()
    session_id = data.get('session_id', '') if data else ''
    
    if not session_id:
        return jsonify({'message': 'No session ID provided.'}), 400
    
    try:
        DiagnosisHistory.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        return jsonify({'message': 'History cleared successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─── Startup ─────────────────────────────────────────────────────
init_db()
model_loaded = load_model()
knowledge_loaded = load_knowledge()

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  Medical Disease Diagnosis System")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    
    if not model_loaded:
        print("[WARNING] WARNING: Model not loaded!")
        print("   Run: python train_model.py")
        print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
