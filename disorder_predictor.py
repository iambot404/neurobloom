"""
Machine Learning Model for Dyslexia, Dyscalculia, and Dysgraphia Prediction
Uses assessment responses to predict risk levels for each disorder
"""

import os
import joblib
import numpy as np
import pandas as pd
from db import get_db_connection, DBError
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime
import json

# Model versioning
MODEL_VERSION = "1.0.0"
MODELS_DIR = "ml_models"

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)


class DisorderPredictor:
    """ML predictor for learning disorders"""
    
    def __init__(self, disorder_type='dyslexia'):
        self.disorder_type = disorder_type
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.risk_thresholds = {
            'low': (0, 0.33),
            'medium': (0.33, 0.66),
            'high': (0.66, 1.0)
        }
    
    def get_risk_level(self, score):
        """Convert probability score to risk level"""
        for level, (low, high) in self.risk_thresholds.items():
            if low <= score < high:
                return level
        return 'high' if score >= 0.66 else 'low'
    
    def extract_features(self, student_answers_df):
        """Extract ML features from assessment responses"""
        features = []
        
        # Feature 1: Accuracy rate
        correct_count = (student_answers_df['is_correct'] == True).sum()
        total_count = len(student_answers_df)
        accuracy = correct_count / total_count if total_count > 0 else 0
        features.append(accuracy)
        
        # Feature 2: Speed (inverse of time spent - faster = higher value)
        avg_time = student_answers_df['time_spent_seconds'].mean()
        speed_score = 1 / (1 + avg_time / 100)  # Normalize to 0-1
        features.append(speed_score)
        
        # Feature 3: Error pattern (errors on easy questions indicate issues)
        easy_questions = student_answers_df[student_answers_df['difficulty_level'] == 'easy']
        if len(easy_questions) > 0:
            easy_error_rate = (easy_questions['is_correct'] == False).sum() / len(easy_questions)
        else:
            easy_error_rate = 0
        features.append(easy_error_rate)
        
        # Feature 4: Consistency (variation in performance)
        correct_array = student_answers_df['is_correct'].astype(int).values
        if len(correct_array) > 1:
            consistency = 1 - (np.std(correct_array) / np.mean(correct_array) if np.mean(correct_array) > 0 else 0)
        else:
            consistency = 0.5
        features.append(max(0, min(1, consistency)))  # Clamp to 0-1
        
        # Feature 5: Difficulty handling (hard vs easy performance ratio)
        hard_questions = student_answers_df[student_answers_df['difficulty_level'] == 'hard']
        medium_questions = student_answers_df[student_answers_df['difficulty_level'] == 'medium']
        
        hard_accuracy = (hard_questions['is_correct'] == True).sum() / len(hard_questions) if len(hard_questions) > 0 else 0
        medium_accuracy = (medium_questions['is_correct'] == True).sum() / len(medium_questions) if len(medium_questions) > 0 else 0
        easy_accuracy = (easy_questions['is_correct'] == True).sum() / len(easy_questions) if len(easy_questions) > 0 else 0
        
        difficulty_ratio = (easy_accuracy - hard_accuracy) / (easy_accuracy + 0.1)
        features.append(max(0, min(1, difficulty_ratio)))
        
        # Feature 6: Answer pattern (for multiple choice - random vs thoughtful)
        # Using time spent as proxy for thoughtfulness
        thoughtfulness = min(1, avg_time / 60)  # 60 seconds = max thoughtfulness
        features.append(thoughtfulness)
        
        return np.array(features).reshape(1, -1)
    
    def train(self, X_train, y_train):
        """Train the ML model"""
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_scaled, y_train)
        
        return self.model
    
    def predict(self, X):
        """Predict risk level"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        probability = self.model.predict_proba(X_scaled)[0][1]  # Probability of high risk
        risk_level = self.get_risk_level(probability)
        
        return {
            'prediction_score': round(probability, 4),
            'risk_level': risk_level,
            'confidence_score': round(max(self.model.predict_proba(X_scaled)[0]), 4)
        }
    
    def save_model(self):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        
        model_path = f"{MODELS_DIR}/{self.disorder_type}_model_{MODEL_VERSION}.pkl"
        scaler_path = f"{MODELS_DIR}/{self.disorder_type}_scaler_{MODEL_VERSION}.pkl"
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        print(f"✓ Model saved: {model_path}")
        return model_path
    
    def load_model(self):
        """Load trained model from disk"""
        model_path = f"{MODELS_DIR}/{self.disorder_type}_model_{MODEL_VERSION}.pkl"
        scaler_path = f"{MODELS_DIR}/{self.disorder_type}_scaler_{MODEL_VERSION}.pkl"
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print(f"✓ Model loaded: {model_path}")
            return True
        return False


def get_training_data(disorder_type):
    """
    Get training data from completed assessments.
    In production, you'd use historical data. For now, we create synthetic data.
    """
    # Create synthetic training data based on disorder characteristics
    n_samples = 200  # 200 training samples per disorder
    
    if disorder_type == 'dyslexia':
        # Dyslexic patterns: slower reading, more letter confusion, reversal errors
        X = np.array([
            np.random.beta(2, 5, n_samples),  # Lower accuracy
            np.random.beta(3, 7, n_samples),  # Slower speed
            np.random.beta(5, 3, n_samples),  # More easy errors
            np.random.beta(3, 4, n_samples),  # Less consistency
            np.random.beta(4, 2, n_samples),  # Difficulty handling issues
            np.random.beta(2, 4, n_samples)   # Less thoughtful
        ]).T
        # High dyslexia risk if features align with dyslexic patterns
        y = (X[:, 0] < 0.4) | (X[:, 2] > 0.5)  # Low accuracy OR high easy errors
        
    elif disorder_type == 'dyscalculia':
        # Dyscalculic patterns: poor number sense, calculation errors, time pressure
        X = np.array([
            np.random.beta(3, 4, n_samples),  # Moderate accuracy
            np.random.beta(3, 5, n_samples),  # Moderate speed
            np.random.beta(4, 3, n_samples),  # Fewer easy errors
            np.random.beta(2, 4, n_samples),  # Less consistency
            np.random.beta(2, 2, n_samples),  # High difficulty ratio
            np.random.beta(2, 5, n_samples)   # Less thoughtful
        ]).T
        # High dyscalculia risk if difficulty handling is poor
        y = (X[:, 4] > 0.5) | (X[:, 0] < 0.45)
        
    else:  # dysgraphia
        # Dysgraphic patterns: writing speed, spelling errors, inconsistency
        X = np.array([
            np.random.beta(2, 4, n_samples),  # Lower accuracy (spelling)
            np.random.beta(2, 6, n_samples),  # Slower speed (fine motor)
            np.random.beta(3, 5, n_samples),  # Easy errors present
            np.random.beta(2, 5, n_samples),  # Low consistency
            np.random.beta(3, 3, n_samples),  # Moderate difficulty
            np.random.beta(3, 6, n_samples)   # Less thoughtful
        ]).T
        # High dysgraphia risk if accuracy and speed are poor
        y = (X[:, 0] < 0.35) & (X[:, 1] < 0.4)
    
    # Add some non-risk cases
    y = y.astype(int)
    # Ensure reasonable balance (60-40 split for high-risk to low-risk)
    n_high = int(n_samples * 0.6)
    n_low = n_samples - n_high
    y[:n_high] = 1
    y[n_high:] = 0
    
    return X, y


def train_all_models():
    """Train and save models for all three disorders"""
    disorders = ['dyslexia', 'dyscalculia', 'dysgraphia']
    
    print("🤖 Training ML models for disorder prediction...\n")
    
    for disorder in disorders:
        print(f"📚 Training {disorder.upper()} model...")
        
        # Get training data
        X, y = get_training_data(disorder)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create and train predictor
        predictor = DisorderPredictor(disorder)
        predictor.train(X_train, y_train)
        
        # Evaluate
        train_score = predictor.model.score(predictor.scaler.transform(X_train), y_train)
        test_score = predictor.model.score(predictor.scaler.transform(X_test), y_test)
        
        print(f"  Train Accuracy: {train_score:.3f}")
        print(f"  Test Accuracy:  {test_score:.3f}")
        
        # Save model
        predictor.save_model()
        print(f"  ✓ {disorder} model trained and saved\n")
    
    print("✅ All models trained successfully!")


def predict_disorder_risk(student_id, assessment_id, disorder_type):
    """
    Predict disorder risk for a student based on their assessment responses
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get student's assessment responses
        sql = '''
        SELECT sa.is_correct, sa.time_spent_seconds, q.difficulty_level
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN student_assessments st ON sa.student_assessment_id = st.id
        WHERE st.student_id = %s AND st.assessment_id = %s
        '''
        cursor.execute(sql, (student_id, assessment_id))
        results = cursor.fetchall()
        
        if not results:
            print(f"No assessment data for student {student_id}")
            return None
        
        # Create DataFrame from results
        if results and isinstance(results[0], dict):
            raw_df = pd.DataFrame(results)
            for col in ['is_correct', 'time_spent_seconds', 'difficulty_level']:
                if col not in raw_df.columns:
                    raw_df[col] = 0 if col == 'time_spent_seconds' else ('easy' if col == 'difficulty_level' else False)
            df = raw_df[['is_correct', 'time_spent_seconds', 'difficulty_level']]
        elif results and isinstance(results[0], (list, tuple)):
            if len(results[0]) >= 8:
                df = pd.DataFrame([
                    {'is_correct': r[4], 'time_spent_seconds': r[7], 'difficulty_level': 'easy'}
                    for r in results
                ])
            elif len(results[0]) == 3:
                df = pd.DataFrame(results, columns=['is_correct', 'time_spent_seconds', 'difficulty_level'])
            else:
                df = pd.DataFrame([
                    {'is_correct': r[0] if len(r) > 0 else False, 'time_spent_seconds': r[1] if len(r) > 1 else 0, 'difficulty_level': 'easy'}
                    for r in results
                ])
        else:
            df = pd.DataFrame(columns=['is_correct', 'time_spent_seconds', 'difficulty_level'])
        
        # Load predictor
        predictor = DisorderPredictor(disorder_type)
        if not predictor.load_model():
            print(f"Warning: Model not found for {disorder_type}, using default prediction")
            # Return a basic calculation if model not available
            accuracy = (df['is_correct'] == True).sum() / len(df)
            prediction_score = 1 - accuracy
            risk_level = predictor.get_risk_level(prediction_score)
            return {
                'prediction_score': round(prediction_score, 4),
                'risk_level': risk_level,
                'confidence_score': 0.6
            }
        
        # Extract features and predict
        X = predictor.extract_features(df)
        prediction = predictor.predict(X)
        
        # Generate recommendations
        recommendations = generate_recommendations(disorder_type, prediction['risk_level'])
        prediction['recommendations'] = recommendations
        
        cursor.close()
        conn.close()
        
        return prediction
    
    except Exception as e:
        print(f"Error predicting risk: {e}")
        return None


def generate_recommendations(disorder_type, risk_level):
    """Generate recommendations based on disorder type and risk level"""
    recommendations = {
        'dyslexia': {
            'low': [
                'Continue current reading practices',
                'Focus on comprehension exercises',
                'Regular reading practice with varied materials'
            ],
            'medium': [
                'Consider additional phonetic training',
                'Use multisensory reading approaches',
                'Implement text-to-speech tools for support'
            ],
            'high': [
                'Immediate specialist assessment recommended',
                'Implement structured literacy programs',
                'Consider speech and language therapy',
                'Use assistive technology (text-to-speech, dyslexic fonts)'
            ]
        },
        'dyscalculia': {
            'low': [
                'Continue math practice regularly',
                'Work on number sense activities',
                'Use manipulatives for advanced concepts'
            ],
            'medium': [
                'Implement specialized math teaching techniques',
                'Use visual and tactile learning aids',
                'Consider tutoring for specific operations'
            ],
            'high': [
                'Immediate specialist evaluation recommended',
                'Use structured numeracy intervention programs',
                'Implement concrete-representational-abstract approach',
                'Consider calculator use for complex operations'
            ]
        },
        'dysgraphia': {
            'low': [
                'Continue regular writing practice',
                'Develop handwriting consistency',
                'Practice fine motor exercises'
            ],
            'medium': [
                'Implement handwriting intervention programs',
                'Use occupational therapy exercises',
                'Allow typed assignments where appropriate'
            ],
            'high': [
                'Immediate OT assessment recommended',
                'Implement intensive handwriting therapy',
                'Allow typing/speech-to-text alternatives',
                'Practice fine motor skills development',
                'Consider specialty writing tools and grips'
            ]
        }
    }
    
    return recommendations.get(disorder_type, {}).get(risk_level, [])


def save_prediction_to_db(student_id, assessment_id, disorder_type, prediction):
    """Save prediction to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = '''
        INSERT INTO ml_predictions 
        (student_id, assessment_id, disorder_type, prediction_score, risk_level, 
         confidence_score, recommendations, model_version, predicted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
        prediction_score = VALUES(prediction_score),
        risk_level = VALUES(risk_level),
        confidence_score = VALUES(confidence_score),
        recommendations = VALUES(recommendations),
        predicted_at = NOW()
        '''
        
        pred_score = prediction.get('prediction_score', prediction.get('risk_score', 0.0))
        risk_lvl = prediction.get('risk_level', 'Medium')
        conf_score = prediction.get('confidence_score', prediction.get('confidence', 0.8))
        recs = prediction.get('recommendations', [])
        
        cursor.execute(sql, (
            student_id,
            assessment_id,
            disorder_type,
            float(pred_score),
            str(risk_lvl),
            float(conf_score),
            json.dumps(recs) if not isinstance(recs, str) else recs,
            MODEL_VERSION
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False


if __name__ == '__main__':
    # Train all models
    train_all_models()
    
    print("\n" + "="*50)
    print("Models ready for prediction!")
    print("Use predict_disorder_risk(student_id, assessment_id, disorder_type)")
    print("="*50)
