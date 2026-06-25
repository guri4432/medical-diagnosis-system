import os
import json
import pytest
from app import app, db, load_model, load_knowledge

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Initialize DB in memory
    with app.app_context():
        db.create_all()
        # Load the models and knowledge base required for the API
        load_model()
        load_knowledge()
        
    with app.test_client() as client:
        yield client
        
    # Cleanup
    with app.app_context():
        db.drop_all()

def test_index_page(client):
    """Test that the main page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'MediScan AI' in response.data

def test_get_symptoms(client):
    """Test the symptoms API endpoint."""
    response = client.get('/api/symptoms')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'symptoms' in data
    assert 'total' in data
    assert data['total'] > 0

def test_predict_no_symptoms(client):
    """Test prediction endpoint with empty data."""
    response = client.post('/api/predict', json={})
    assert response.status_code == 400
    assert b'No symptoms provided' in response.data

def test_predict_invalid_symptoms(client):
    """Test prediction endpoint with an invalid symptom."""
    response = client.post('/api/predict', json={'symptoms': ['not_a_real_symptom']})
    assert response.status_code == 400
    assert b'No valid symptoms found' in response.data

def test_predict_low_confidence(client):
    """Test prediction endpoint expecting a low confidence response."""
    # A single vague symptom like 'fatigue' should result in low confidence.
    response = client.post('/api/predict', json={'symptoms': ['fatigue']})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['low_confidence'] is True
    assert 'message' in data

from unittest.mock import patch

def test_predict_high_confidence(client):
    """Test prediction endpoint expecting a confident response."""
    # We mock the model.predict_proba to guarantee a high confidence score
    with patch('app.model.predict_proba') as mock_proba:
        with patch('app.model.predict') as mock_predict:
            # Setup mock to return >80% confidence for class 0
            import numpy as np
            mock_predict.return_value = np.array([0])
            
            # Create a probability array where class 0 has 0.95 (95%)
            probs = np.zeros((1, 41))
            probs[0, 0] = 0.95
            mock_proba.return_value = probs
            
            response = client.post('/api/predict', json={'symptoms': ['chills']})
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['low_confidence'] is False
            assert 'predicted_disease' in data
            assert 'confidence' in data
            assert data['confidence'] >= 80.0

def test_history_workflow(client):
    """Test getting and deleting history."""
    # 1. Make a prediction to generate history
    session_id = 'test-session-123'
    client.post('/api/predict', json={'symptoms': ['chills', 'vomiting'], 'session_id': session_id})
    
    # 2. Get history
    response = client.get(f'/api/history?session_id={session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['history']) == 1
    
    # 3. Delete history
    delete_response = client.delete('/api/history', json={'session_id': session_id})
    assert delete_response.status_code == 200
    
    # 4. Verify deletion
    verify_response = client.get(f'/api/history?session_id={session_id}')
    verify_data = json.loads(verify_response.data)
    assert len(verify_data['history']) == 0
