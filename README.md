# Medical Disease Diagnosis System

A Flask-based web application that provides medical disease predictions using a machine learning model. It takes patient symptoms as input, uses a Random Forest model to predict the most likely disease, and provides detailed information about the condition.

## Features

- **Symptom-based Prediction:** Select from a comprehensive list of symptoms to get disease predictions.
- **Machine Learning Backend:** Uses a Random Forest Classifier trained on symptom-disease datasets.
- **Disease Knowledge Base:** Provides detailed information about predicted diseases, including descriptions, causes, risk factors, prevention, and home remedies.
- **Diagnosis History:** Keeps track of previous predictions in a session using an SQLite database.
- **RESTful API:** Clean API endpoints for frontend integration.

## Tech Stack

- **Backend:** Python, Flask
- **Machine Learning:** scikit-learn, pandas, numpy, joblib
- **Database:** SQLite3

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd medical-diagnosis-system
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Train the Model:**
   Before running the app, you need to train the machine learning model.
   ```bash
   python train_model.py
   ```
   This will generate the necessary `.pkl` files in the `models/` directory.

2. **Run the Application:**
   Start the Flask development server:
   ```bash
   python app.py
   ```

3. **Access the App:**
   Open your web browser and go to `http://localhost:5000`.

## API Endpoints

- `GET /api/symptoms`: Returns a list of all available symptoms.
- `POST /api/predict`: Accepts a JSON payload with an array of symptoms and returns the predicted disease and related information.
- `GET /api/history`: Returns the diagnosis history for a specific session ID.
- `DELETE /api/history`: Clears the diagnosis history for a specific session ID.

## Directory Structure

```
medical-diagnosis-system/
├── app.py                 # Main Flask application
├── train_model.py         # Script to train the ML model
├── requirements.txt       # Python dependencies
├── models/                # Directory for trained model files (.pkl)
├── data/                  # Directory for training datasets
├── database/              # Directory for SQLite database
├── knowledge/             # JSON files containing disease information
├── static/                # Static assets (CSS, JS, images)
└── templates/             # HTML templates
```

## License

This project is licensed under the MIT License.
