"""
Assessment API Endpoints for Neurobloom
Includes endpoints for loading, submitting, and analyzing assessments
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
import json
import os
import numpy as np
from db import get_db_connection, DBError
from disorder_predictor import predict_disorder_risk, save_prediction_to_db
from ml_models import get_predictor  # Import unified ML/DL predictor
from ml_models.dyslexia_nn_model import DyslexiaDeepLearning
from ml_models.dyscalculia_nn_model import DyscalculiaDeepLearning
from ml_models.dysgraphia_nn_model import DysgraphiaDeepLearning
from ml_models.unified_predictor import UnifiedDisorderPredictor

# Initialize global predictor
predictor = get_predictor()


def convert_row_to_dict(row):
    """Convert row objects to JSON-serializable dictionary"""
    if row is None:
        return None
    if isinstance(row, dict):
        return {k: str(v) if isinstance(v, datetime) else v for k, v in row.items()}
    return row


def login_required_api(f):
    """Decorator for API endpoints requiring student login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or session.get('role') != 'student':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


def generate_and_store_recommendations(conn, student_id, disorder_type, risk_level):
    """Generate recommendations based on risk level and store in database"""
    try:
        cursor = conn.cursor()
        
        # Get the appropriate model based on disorder type
        if disorder_type.lower() == 'dyslexia':
            model = DyslexiaDeepLearning()
        elif disorder_type.lower() == 'dyscalculia':
            model = DyscalculiaDeepLearning()
        elif disorder_type.lower() == 'dysgraphia':
            model = DysgraphiaDeepLearning()
        else:
            return
        
        # Generate recommendations using the model's method
        recommendations = model._generate_recommendations(risk_level)
        
        if not recommendations:
            return
        
        # Store each recommendation in the database
        timestamp = datetime.now()
        for idx, rec_text in enumerate(recommendations):
            cursor.execute('''
                INSERT INTO recommendations 
                (student_id, disorder_type, recommendation_text, recommendation_details, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (student_id, disorder_type, rec_text, f'Recommendation {idx+1}', timestamp))
        
        conn.commit()
        print(f"[DEBUG] Stored {len(recommendations)} recommendations for student {student_id} ({disorder_type})")
        cursor.close()
    except Exception as e:
        print(f"[ERROR] Error generating recommendations: {e}")
        try:
            cursor.close()
        except:
            pass


# Create Blueprint
assessment_bp = Blueprint('assessment', __name__, url_prefix='/api')


@assessment_bp.route('/assessment/<int:assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    """Get assessment details with all questions and options"""
    conn = None
    cursor = None
    try:
        print(f"[DEBUG] Fetching assessment ID: {assessment_id}")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get assessment details
        cursor.execute('''
            SELECT id, name, description, disorder_type, total_questions, time_limit_minutes
            FROM assessment_types
            WHERE id = %s
        ''', (assessment_id,))
        assessment = cursor.fetchone()
        
        if not assessment:
            print(f"[DEBUG] Assessment not found for ID: {assessment_id}")
            return jsonify({'error': 'Assessment not found'}), 404
        
        print(f"[DEBUG] Assessment found: {assessment['name']}")
        
        # Get all questions
        cursor.execute('''
            SELECT id, question_text, question_type, difficulty_level, display_order
            FROM questions
            WHERE assessment_id = %s
            ORDER BY display_order
        ''', (assessment_id,))
        questions = cursor.fetchall()
        print(f"[DEBUG] Found {len(questions) if questions else 0} questions")
        
        if not questions:
            questions = []
        
        # Get options for each question
        for question in questions:
            qid = question['id']
            cursor.execute('''
                SELECT id, option_text, option_value, is_correct, display_order
                FROM answer_options
                WHERE question_id = %s
                ORDER BY display_order
            ''', (qid,))
            options = cursor.fetchall()
            question['options'] = options if options else []
            
            # For visual questions, get visual options
            if question['question_type'] in ['image', 'visual_matching']:
                cursor.execute('''
                    SELECT id, image_path, label
                    FROM visual_options
                    WHERE question_id = %s
                    ORDER BY display_order
                ''', (qid,))
                visual_opts = cursor.fetchall()
                question['visual_options'] = visual_opts if visual_opts else []
            
            # For puzzle questions, get puzzle data
            if question['question_type'] == 'puzzle':
                cursor.execute('''
                    SELECT id, puzzle_type, puzzle_data, correct_answer
                    FROM puzzle_questions
                    WHERE question_id = %s
                    LIMIT 1
                ''', (qid,))
                puzzle = cursor.fetchone()
                if puzzle:
                    question['puzzle_data'] = puzzle
        
        print(f"[DEBUG] Returning assessment with {len(questions)} questions")
        return jsonify({
            'assessment': convert_row_to_dict(assessment),
            'questions': [convert_row_to_dict(q) for q in questions]
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Error fetching assessment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/student-assessment/start', methods=['POST'])
@login_required_api
def start_student_assessment():
    """Start a new assessment for the student"""
    conn = None
    cursor = None
    try:
        data = request.json
        assessment_id = data.get('assessment_id')
        student_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Check if there's already an in_progress assessment
        cursor.execute('''
            SELECT id FROM student_assessments 
            WHERE student_id = %s AND assessment_id = %s AND status = 'in_progress'
        ''', (student_id, assessment_id))
        existing = cursor.fetchone()
        
        if existing:
            # Return the existing in_progress assessment ID
            student_assessment_id = existing['id']
        else:
            # Create a new student assessment record only if one doesn't exist
            cursor.execute('''
                INSERT INTO student_assessments 
                (student_id, assessment_id, status, start_time)
                VALUES (%s, %s, 'in_progress', NOW())
            ''', (student_id, assessment_id))
            conn.commit()
            student_assessment_id = cursor.lastrowid
        
        return jsonify({'student_assessment_id': student_assessment_id}), 201
    
    except Exception as e:
        print(f"Error starting assessment: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/student-assessment/submit', methods=['POST'])
@login_required_api
def submit_student_assessment():
    """Submit completed assessment with answers"""
    conn = None
    cursor = None
    try:
        data = request.json or {}
        student_assessment_id = data.get('student_assessment_id')
        assessment_id = data.get('assessment_id')
        answers = data.get('answers', [])
        student_id = session.get('user_id')
        
        if not student_assessment_id:
            return jsonify({'error': 'Missing student_assessment_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        if not assessment_id:
            cursor.execute('SELECT assessment_id FROM student_assessments WHERE id = %s', (student_assessment_id,))
            sa_row = cursor.fetchone()
            if sa_row:
                assessment_id = sa_row.get('assessment_id') if isinstance(sa_row, dict) else sa_row[0]

        if not assessment_id:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Could not determine assessment_id'}), 400
        
        # Get assessment info
        cursor.execute('''
            SELECT disorder_type FROM assessment_types WHERE id = %s
        ''', (assessment_id,))
        assessment_info = cursor.fetchone()
        
        if not assessment_info:
            return jsonify({'error': f'Assessment {assessment_id} not found'}), 404
        
        disorder_type = assessment_info['disorder_type']
        
        # Normalize answers to list of dicts
        answers_list = []
        if isinstance(answers, dict):
            for q_k, a_v in answers.items():
                answers_list.append({
                    'question_id': int(q_k) if str(q_k).isdigit() else q_k,
                    'student_answer': a_v,
                    'time_spent_seconds': 0
                })
        elif isinstance(answers, list):
            answers_list = answers
        else:
            answers_list = []
        
        # Process each answer
        total_correct = 0
        total_points = 0
        
        for answer_data in answers_list:
            question_id = None
            try:
                question_id = answer_data.get('question_id')
                student_answer = answer_data.get('student_answer')
                time_spent = answer_data.get('time_spent_seconds', 0)
                
                if not question_id:
                    continue
                
                # Get correct answer for this question
                cursor.execute('''
                    SELECT id, question_type, correct_answer FROM questions WHERE id = %s
                ''', (question_id,))
                question = cursor.fetchone()
                
                if not question:
                    print(f"Question {question_id} not found")
                    continue
                
                # Determine if answer is correct
                is_correct = False
                points = 0
                
                if question['question_type'] in ['multiple_choice', 'true_false']:
                    # For choice questions, check if selected option ID is correct or option value matches
                    cursor.execute('''
                        SELECT is_correct, option_value FROM answer_options WHERE id = %s OR (question_id = %s AND option_value = %s)
                    ''', (student_answer if str(student_answer).isdigit() else -1, question_id, str(student_answer)))
                    option = cursor.fetchone()
                    is_correct = option['is_correct'] if option else False
                    points = 5 if is_correct else 0
                else:
                    # For short answer, do basic matching
                    student_text = str(student_answer).lower().strip()
                    correct_text = str(question['correct_answer']).lower().strip() if question['correct_answer'] else ''
                    is_correct = student_text == correct_text
                    points = 5 if is_correct else 0
                
                if is_correct:
                    total_correct += 1
                total_points += points
                
                # Save answer
                cursor.execute('''
                    INSERT INTO student_answers 
                    (student_assessment_id, question_id, student_answer, is_correct, points_earned, answered_at, time_spent_seconds)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                ''', (student_assessment_id, question_id, str(student_answer), is_correct, points, time_spent))
            
            except Exception as e:
                print(f"Error processing answer for question {question_id}: {e}")
                continue
        
        conn.commit()
        
        # Calculate score
        total_questions = len(answers_list)
        percentage_score = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Update student assessment
        cursor.execute('''
            UPDATE student_assessments
            SET status = 'completed', end_time = NOW(), 
                total_score = %s, percentage_score = %s,
                time_taken_minutes = 15
            WHERE id = %s
        ''', (total_points, percentage_score, student_assessment_id))
        
        conn.commit()
        
        # Generate ML prediction
        prediction = predict_disorder_risk(student_id, assessment_id, disorder_type)
        
        # Save prediction to database
        if prediction:
            save_prediction_to_db(student_id, assessment_id, disorder_type, prediction)
            
            # Generate and store recommendations based on risk level from prediction
            risk_level = prediction.get('risk_level', 'Medium') if isinstance(prediction, dict) else 'Medium'
            generate_and_store_recommendations(conn, student_id, disorder_type, risk_level)
        
        # Update student progress
        try:
            # Count total completed assessments for this disorder
            cursor.execute('''
                SELECT COUNT(*) as count FROM student_assessments
                WHERE student_id = %s AND assessment_id = (
                    SELECT id FROM assessment_types WHERE disorder_type = %s
                ) AND status = 'completed'
            ''', (student_id, disorder_type))
            count_result = cursor.fetchone()
            total_completed_for_disorder = count_result['count']
            
            # Get average score for this disorder from all completed assessments
            cursor.execute('''
                SELECT AVG(percentage_score) as avg_score FROM student_assessments
                WHERE student_id = %s AND assessment_id = (
                    SELECT id FROM assessment_types WHERE disorder_type = %s
                ) AND status = 'completed'
            ''', (student_id, disorder_type))
            avg_result = cursor.fetchone()
            avg_score_for_disorder = float(avg_result['avg_score']) if avg_result['avg_score'] else 0
            
            # Upsert: try to update, if no rows affected then insert
            cursor.execute('''
                UPDATE student_progress
                SET total_attempts = %s, average_score = %s, last_assessment_date = NOW()
                WHERE student_id = %s AND disorder_type = %s
            ''', (total_completed_for_disorder, avg_score_for_disorder, student_id, disorder_type))
            
            if cursor.rowcount == 0:
                # No record exists, insert new one
                cursor.execute('''
                    INSERT INTO student_progress 
                    (student_id, disorder_type, total_attempts, average_score, last_assessment_date)
                    VALUES (%s, %s, %s, %s, NOW())
                ''', (student_id, disorder_type, total_completed_for_disorder, avg_score_for_disorder))
            
            conn.commit()
            print(f"Progress updated for {disorder_type}: {total_completed_for_disorder} attempts, {avg_score_for_disorder:.2f}% avg")
        except Exception as e:
            print(f"Error updating progress: {e}")
            conn.rollback()
        
        return jsonify({
            'student_assessment_id': student_assessment_id,
            'total_score': total_points,
            'percentage_score': round(percentage_score, 2),
            'total_correct': total_correct,
            'total_questions': total_questions,
            'prediction': prediction
        }), 200
    
    except Exception as e:
        print(f"Error submitting assessment: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/student-assessment/<int:student_assessment_id>/results', methods=['GET'])
@login_required_api
def get_assessment_results(student_assessment_id):
    """Get results for a specific student assessment attempt"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get the student assessment record
        cursor.execute('''
            SELECT id, assessment_id, total_score, percentage_score, time_taken_minutes, 
                   start_time, end_time, status
            FROM student_assessments
            WHERE id = %s AND student_id = %s
        ''', (student_assessment_id, student_id))
        assessment = cursor.fetchone()
        
        if not assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        # Get answers and performance with timing information
        cursor.execute('''
            SELECT sa.question_id, sa.student_answer, sa.is_correct, sa.points_earned,
                   sa.time_spent_seconds, q.question_text, q.difficulty_level, q.explanation, 
                   at.disorder_type
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            JOIN assessment_types at ON q.assessment_id = at.id
            WHERE sa.student_assessment_id = %s
            ORDER BY q.display_order
        ''', (student_assessment_id,))
        answers = cursor.fetchall()
        
        # Get ML prediction using assessment_id from the student_assessments record
        cursor.execute('''
            SELECT prediction_score, risk_level, confidence_score, recommendations
            FROM ml_predictions
            WHERE student_id = %s AND assessment_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1
        ''', (student_id, assessment['assessment_id']))
        prediction = cursor.fetchone()
        
        if prediction and prediction.get('recommendations'):
            prediction['recommendations'] = json.loads(prediction['recommendations'])
        
        # Add disorder_type to assessment object
        disorder_type = None
        aid = assessment.get('assessment_id') if isinstance(assessment, dict) else 1
        try:
            cursor.execute("SELECT disorder_type FROM assessment_types WHERE id = %s", (aid,))
            at_row = cursor.fetchone()
            if at_row:
                dt = at_row.get('disorder_type') if isinstance(at_row, dict) else at_row[0]
                disorder_type = dt
        except Exception:
            pass
            
        if not disorder_type:
            disorder_type = 'dyslexia' if aid == 1 else ('dyscalculia' if aid == 2 else ('dysgraphia' if aid == 3 else 'general'))
            
        if isinstance(assessment, dict):
            assessment['disorder_type'] = disorder_type
        
        # Generate detailed analysis
        detailed_analysis = generate_detailed_analysis(answers, disorder_type)
        
        return jsonify({
            'assessment': assessment,
            'answers': answers,
            'prediction': prediction,
            'detailed_analysis': detailed_analysis
        }), 200
    
    except Exception as e:
        print(f"Error fetching results: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def generate_detailed_analysis(answers, disorder_type):
    """Generate detailed analysis by difficulty level and per-question metrics"""
    if not answers:
        return {'by_difficulty': {}, 'per_question': {}, 'overall': {}}
    
    # Initialize difficulty buckets
    difficulty_analysis = {
        'easy': {'correct': 0, 'total': 0, 'time_taken': 0},
        'medium': {'correct': 0, 'total': 0, 'time_taken': 0},
        'hard': {'correct': 0, 'total': 0, 'time_taken': 0}
    }
    
    # Initialize per-question tracking
    per_question = {}
    
    # Process answers
    total_time = 0
    for idx, answer in enumerate(answers):
        difficulty = answer.get('difficulty_level', 'medium').lower()
        if difficulty not in difficulty_analysis:
            difficulty = 'medium'
        
        difficulty_analysis[difficulty]['total'] += 1
        is_correct = answer.get('is_correct')
        if is_correct:
            difficulty_analysis[difficulty]['correct'] += 1
        
        time_spent = answer.get('time_spent_seconds', 0) or 0
        difficulty_analysis[difficulty]['time_taken'] += time_spent
        total_time += time_spent
        
        # Track per-question metrics
        question_text = answer.get('question_text', f'Question {idx+1}')[:50]  # First 50 chars
        per_question[f'q{idx+1}'] = {
            'text': question_text,
            'correct': 1 if is_correct else 0,
            'response_time_ms': round(time_spent * 1000, 0) if time_spent else 0,
            'difficulty': difficulty
        }
    
    # Calculate percentages and averages
    for level in difficulty_analysis:
        bucket = difficulty_analysis[level]
        if bucket['total'] > 0:
            bucket['accuracy'] = round((bucket['correct'] / bucket['total']) * 100, 1)
            bucket['avg_response_time_ms'] = round((bucket['time_taken'] / bucket['total']) * 1000, 0)
        else:
            bucket['accuracy'] = 0
            bucket['avg_response_time_ms'] = 0
    
    # Overall statistics
    total_correct = sum(bucket['correct'] for bucket in difficulty_analysis.values())
    total_questions = sum(bucket['total'] for bucket in difficulty_analysis.values())
    overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    avg_response_time = (total_time / total_questions * 1000) if total_questions > 0 else 0
    
    return {
        'by_difficulty': difficulty_analysis,
        'per_question': per_question,
        'overall': {
            'accuracy_percent': round(overall_accuracy, 1),
            'avg_response_time_ms': round(avg_response_time, 0),
            'total_questions': total_questions,
            'total_correct': total_correct
        }
    }


@assessment_bp.route('/assessments/available', methods=['GET'])
@login_required_api
def get_available_assessments():
    """Get list of all available assessments for student"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get all assessment types
        cursor.execute('''
            SELECT id, name, description, disorder_type, total_questions, time_limit_minutes
            FROM assessment_types
            ORDER BY disorder_type, name
        ''')
        assessments = cursor.fetchall() or []
        
        # Get all attempts for each assessment
        cursor.execute('''
            SELECT assessment_id, id, percentage_score, end_time, time_taken_minutes
            FROM student_assessments
            WHERE student_id = %s AND status = 'completed'
            ORDER BY assessment_id, end_time DESC
        ''', (student_id,))
        all_attempts = cursor.fetchall() or []
        
        # Group attempts by assessment_id
        attempts_by_assessment = {}
        for attempt in all_attempts:
            if isinstance(attempt, dict):
                aid = attempt.get('assessment_id')
            else:
                aid = attempt[0] if len(attempt) > 0 else None
            if aid:
                if aid not in attempts_by_assessment:
                    attempts_by_assessment[aid] = []
                attempts_by_assessment[aid].append(attempt)
        
        # Attach attempts and statistics to each assessment
        for assessment in assessments:
            if isinstance(assessment, dict):
                aid = assessment.get('id')
                user_attempts = attempts_by_assessment.get(aid, [])
                assessment['attempts'] = user_attempts
                assessment['total_attempts'] = len(user_attempts)
                if user_attempts:
                    latest = user_attempts[0]
                    assessment['last_score'] = float(latest.get('percentage_score') or 0) if isinstance(latest, dict) else (float(latest[2]) if len(latest) > 2 else None)
                    assessment['last_attempt_date'] = str(latest.get('end_time') or '') if isinstance(latest, dict) else ''
                else:
                    assessment['last_score'] = None
                    assessment['last_attempt_date'] = None
        
        return jsonify({'assessments': assessments}), 200
    
    except Exception as e:
        print(f"Error fetching assessments: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/student-assessment-history/<int:assessment_id>', methods=['GET'])
@login_required_api
def get_student_assessment_history(assessment_id):
    """Get student's previous attempts for a specific assessment"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get all completed attempts for this assessment by the student
        cursor.execute('''
            SELECT id, assessment_id, start_time, end_time, percentage_score, time_taken_minutes, status
            FROM student_assessments
            WHERE student_id = %s AND assessment_id = %s AND status = 'completed'
            ORDER BY end_time DESC
        ''', (student_id, assessment_id))
        attempts = cursor.fetchall()
        
        return jsonify({'attempts': attempts}), 200
    
    except Exception as e:
        print(f"Error fetching assessment history: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/student-progress', methods=['GET'])
@login_required_api
def get_student_progress():
    """Get overall progress across all disorders"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get progress for all disorders
        cursor.execute('''
            SELECT disorder_type, total_attempts, average_score, current_risk_level,
                   improvement_trend, total_study_time_minutes, last_assessment_date
            FROM student_progress
            WHERE student_id = %s
            ORDER BY disorder_type
        ''', (student_id,))
        progress_data = cursor.fetchall()
        
        return jsonify({'progress': progress_data}), 200
    
    except Exception as e:
        print(f"Error fetching progress: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/analyze-dyslexia', methods=['POST'])
def analyze_dyslexia():
    """Analyze dyslexia game results using Neural Network ML model"""
    try:
        data = request.get_json()
        games = data.get('games', {})
        student_id = data.get('student_id', session.get('user_id'))
        
        print(f"[DEBUG] Analyzing dyslexia results using Neural Network: {list(games.keys())}")
        
        # Use neural network predictor
        dyslexia_model = DyslexiaDeepLearning()
        
        # Extract advanced features from game data
        session_data = {'games': games}
        features = dyslexia_model.extract_advanced_features(session_data)
        
        # Make prediction
        result = dyslexia_model.predict_risk(session_data)
        
        # Extract answers from games for detailed analysis
        answers = []
        for game_name, game_data in games.items():
            if isinstance(game_data, dict) and 'questions' in game_data:
                for q_idx, question in enumerate(game_data['questions']):
                    answers.append({
                        'question_text': question.get('text', f'{game_name} - Question {q_idx + 1}'),
                        'user_answer': question.get('userAnswer', ''),
                        'correct_answer': question.get('correctAnswer', ''),
                        'is_correct': question.get('isCorrect', False),
                        'time_spent_seconds': question.get('timeSpent', 0) / 1000.0,  # Convert ms to seconds
                        'difficulty_level': question.get('difficulty', 'medium')
                    })
        
        # Generate detailed analysis with per-question metrics
        detailed_analysis = generate_detailed_analysis(answers, 'dyslexia')
        
        # Build clean per_task map for each game
        per_task = {}
        for g_name, g_data in games.items():
            if isinstance(g_data, dict):
                c = g_data.get('correct', 0)
                tot = g_data.get('total', 0) or 1
                acc = round((c / tot * 100), 1) if tot > 0 else 0
                avg_rt = g_data.get('avg_rt', 0)
                per_task[g_name] = {
                    'acc': f"{acc}%",
                    'accuracy': acc,
                    'avg_rt': avg_rt,
                    'correct': c,
                    'total': tot
                }
        
        # Prepare response with detailed neural analysis
        response = {
            'risk': result['risk_level'],
            'risk_score': result['risk_score'],
            'confidence': result['confidence'],
            'details': {
                'norm_score': result['risk_score'],
                'per_task': per_task,
                'per_task_metrics': per_task,
                'detailed_analysis': detailed_analysis,
                'by_difficulty': detailed_analysis.get('by_difficulty', {}),
                'per_question': detailed_analysis.get('per_question', {}),
                'overall': detailed_analysis.get('overall', {}),
                'neural_analysis': result.get('detailed_analysis', {}),
                'warnings': result.get('recommendations', []),
                'model_version': '2.0 - Neural Networks',
                'features_analyzed': len(features[0]) if (features is not None and len(features) > 0) else 20,
                'confidence_threshold': 0.65
            }
        }
        
        print(f"[DEBUG] Neural dyslexia analysis complete: risk={result['risk_level']}, confidence={result['confidence']:.2%}")
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"[ERROR] Dyslexia analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'risk': 'Unable to analyze'}), 500


@assessment_bp.route('/submit-assessment', methods=['POST'])
def submit_assessment():
    """Submit completed assessment results and update student assessments and progress"""
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}
        assessment_id = data.get('assessment_id') or 1
        student_id = session.get('user_id') or data.get('student_id')
        results = data.get('results', {})
        status = data.get('status', 'completed')
        
        # Calculate scores from games
        total_correct = 0
        total_questions = 0
        smoothness_sum = 0.0
        smoothness_count = 0
        for g_name, g_data in results.items():
            if isinstance(g_data, dict):
                if 'correct' in g_data and 'total' in g_data and g_data.get('total', 0) > 0:
                    total_correct += g_data.get('correct', 0)
                    total_questions += g_data.get('total', 0)
                elif 'questions' in g_data and isinstance(g_data['questions'], list) and len(g_data['questions']) > 0:
                    qs = g_data['questions']
                    total_correct += sum(1 for q in qs if q.get('isCorrect'))
                    total_questions += len(qs)
                elif 'accuracy' in g_data:
                    acc = float(g_data['accuracy'])
                    smoothness_sum += (acc if acc <= 1.0 else acc / 100.0)
                    smoothness_count += 1
                elif 'smoothness' in g_data:
                    smoothness_sum += float(g_data['smoothness'])
                    smoothness_count += 1
        
        if total_questions > 0:
            percentage_score = round((total_correct / total_questions * 100), 2)
        elif smoothness_count > 0:
            percentage_score = round((smoothness_sum / smoothness_count * 100), 2)
        else:
            percentage_score = 0.0

        # Guest evaluation: calculate prediction and return without requiring database login
        if not student_id:
            dt_clean = 'dyslexia' if assessment_id == 1 else ('dyscalculia' if assessment_id == 2 else 'dysgraphia')
            prediction = None
            try:
                predictor = UnifiedDisorderPredictor()
                if dt_clean == 'dyslexia':
                    prediction = predictor.predict_dyslexia({'games': results})
                elif dt_clean == 'dyscalculia':
                    prediction = predictor.predict_dyscalculia({'games': results})
                elif dt_clean == 'dysgraphia':
                    prediction = predictor.predict_dysgraphia({'games': results})
            except Exception as e:
                print(f"[ERROR] Guest prediction error: {e}")
            
            return jsonify({
                'success': True,
                'is_guest': True,
                'student_assessment_id': 'guest',
                'percentage_score': percentage_score,
                'prediction': prediction,
                'message': 'Assessment completed. Sign up or log in to save permanently to your account.'
            }), 200
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Store assessment completion in assessment_results
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results_json = json.dumps(results)
        
        cursor.execute('''
            INSERT INTO assessment_results (student_id, assessment_id, results, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (student_id, assessment_id, results_json, status, timestamp))
        conn.commit()
        
        # Calculate scores from games
        total_correct = 0
        total_questions = 0
        smoothness_sum = 0.0
        smoothness_count = 0
        for g_name, g_data in results.items():
            if isinstance(g_data, dict):
                if 'correct' in g_data and 'total' in g_data and g_data.get('total', 0) > 0:
                    total_correct += g_data.get('correct', 0)
                    total_questions += g_data.get('total', 0)
                elif 'questions' in g_data and isinstance(g_data['questions'], list) and len(g_data['questions']) > 0:
                    qs = g_data['questions']
                    total_correct += sum(1 for q in qs if q.get('isCorrect'))
                    total_questions += len(qs)
                elif 'accuracy' in g_data:
                    acc = float(g_data['accuracy'])
                    smoothness_sum += (acc if acc <= 1.0 else acc / 100.0)
                    smoothness_count += 1
                elif 'smoothness' in g_data:
                    smoothness_sum += float(g_data['smoothness'])
                    smoothness_count += 1
        
        if total_questions > 0:
            percentage_score = round((total_correct / total_questions * 100), 2)
        elif smoothness_count > 0:
            percentage_score = round((smoothness_sum / smoothness_count * 100), 2)
        else:
            percentage_score = 0.0
        
        # Get disorder_type from assessment_types
        cursor.execute('SELECT disorder_type FROM assessment_types WHERE id = %s', (assessment_id,))
        at_row = cursor.fetchone()
        disorder_type = at_row.get('disorder_type') if at_row else ('dyslexia' if assessment_id == 1 else ('dyscalculia' if assessment_id == 2 else 'dysgraphia'))
        
        # Create student_assessments record
        cursor.execute('''
            INSERT INTO student_assessments 
            (student_id, assessment_id, status, start_time, end_time, total_score, percentage_score, time_taken_minutes, created_at)
            VALUES (%s, %s, 'completed', NOW(), NOW(), %s, %s, 15, NOW())
        ''', (student_id, assessment_id, total_correct, percentage_score))
        conn.commit()
        sa_id = cursor.lastrowid
        
        # Generate ML prediction and recommendations using Neural Network
        prediction = None
        try:
            predictor = UnifiedDisorderPredictor()
            dt_clean = str(disorder_type or '').lower()
            if dt_clean == 'dyslexia':
                prediction = predictor.predict_dyslexia({'games': results})
            elif dt_clean == 'dyscalculia':
                prediction = predictor.predict_dyscalculia({'games': results})
            elif dt_clean == 'dysgraphia':
                prediction = predictor.predict_dysgraphia({'games': results})
            print(f"[DEBUG] Neural prediction generated for student {student_id}: {prediction.get('risk_level')}, score={prediction.get('risk_score')}")
        except Exception as e:
            print(f"[ERROR] Unified neural prediction failed: {e}")
            prediction = predict_disorder_risk(student_id, assessment_id, disorder_type)
            
        if prediction:
            saved_ok = save_prediction_to_db(student_id, assessment_id, disorder_type, prediction)
            print(f"[DEBUG] Saved prediction to DB: {saved_ok}")
            risk_level = prediction.get('risk_level', 'Medium') if isinstance(prediction, dict) else 'Medium'
            generate_and_store_recommendations(conn, student_id, disorder_type, risk_level)
            
        # Update student_progress record
        try:
            cursor.execute('''
                SELECT COUNT(*) as count, AVG(percentage_score) as avg_score, MAX(percentage_score) as best_score
                FROM student_assessments
                WHERE student_id = %s AND assessment_id = %s AND status = 'completed'
            ''', (student_id, assessment_id))
            stats_row = cursor.fetchone() or {}
            c_cnt = stats_row.get('count', 1) if isinstance(stats_row, dict) else (stats_row[0] if stats_row else 1)
            c_avg = float(stats_row.get('avg_score') or percentage_score) if isinstance(stats_row, dict) else float(stats_row[1] or percentage_score)
            c_best = float(stats_row.get('best_score') or percentage_score) if isinstance(stats_row, dict) else float(stats_row[2] or percentage_score)
            
            cursor.execute('''
                SELECT id FROM student_progress 
                WHERE student_id = %s AND assessment_id = %s
            ''', (student_id, assessment_id))
            prog_row = cursor.fetchone()
            
            if prog_row:
                cursor.execute('''
                    UPDATE student_progress
                    SET total_completed = %s, average_score = %s, highest_score = %s,
                        last_attempt_date = NOW(), updated_at = NOW()
                    WHERE student_id = %s AND assessment_id = %s
                ''', (c_cnt, c_avg, c_best, student_id, assessment_id))
            else:
                cursor.execute('''
                    INSERT INTO student_progress
                    (student_id, assessment_id, total_completed, average_score, highest_score, last_attempt_date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                ''', (student_id, assessment_id, c_cnt, c_avg, c_best))
            conn.commit()
        except Exception as prog_err:
            print(f"[WARNING] Could not update student_progress: {prog_err}")
        
        print(f"[DEBUG] Assessment submitted successfully: sa_id={sa_id}, percentage={percentage_score}%")
        return jsonify({
            'success': True,
            'message': 'Assessment results saved',
            'student_assessment_id': sa_id,
            'percentage_score': percentage_score
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Submit assessment error: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/dyslexia-results/<int:assessment_id>', methods=['GET'])
def get_dyslexia_results(assessment_id):
    """Get all dyslexia assessment attempts for current student"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        if not student_id:
            return jsonify({'attempts': [], 'is_guest': True}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all attempts for this assessment
        cursor.execute('''
            SELECT ar.id, ar.student_id, ar.assessment_id, ar.results, ar.status, ar.created_at
            FROM assessment_results ar
            WHERE ar.student_id = %s AND ar.assessment_id = %s
            ORDER BY ar.created_at DESC
        ''', (student_id, assessment_id))
        
        attempts = cursor.fetchall()
        
        if not attempts:
            return jsonify({'attempts': []}), 200
        
        # Parse JSON results and analyze risk for each attempt
        processed_attempts = []
        for attempt in attempts:
            results_data = json.loads(attempt['results']) if isinstance(attempt['results'], str) else attempt['results']
            
            # Calculate risk level using the same algorithm
            risk_level, details = analyze_dyslexia_results(results_data)
            
            processed_attempts.append({
                'id': attempt['id'],
                'student_id': attempt['student_id'],
                'assessment_id': attempt['assessment_id'],
                'results': results_data,
                'risk_level': risk_level,
                'details': details,
                'status': attempt['status'],
                'created_at': attempt['created_at'].isoformat() if hasattr(attempt['created_at'], 'isoformat') else str(attempt['created_at'])
            })
        
        return jsonify({'attempts': processed_attempts}), 200
    
    except Exception as e:
        print(f"[ERROR] Get dyslexia results error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/dyscalculia-results/<int:assessment_id>', methods=['GET'])
def get_dyscalculia_results(assessment_id):
    """Get all dyscalculia assessment attempts for current student"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        if not student_id:
            return jsonify({'attempts': [], 'is_guest': True}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all attempts for this assessment
        cursor.execute('''
            SELECT ar.id, ar.student_id, ar.assessment_id, ar.results, ar.status, ar.created_at
            FROM assessment_results ar
            WHERE ar.student_id = %s AND ar.assessment_id = %s
            ORDER BY ar.created_at DESC
        ''', (student_id, assessment_id))
        
        attempts = cursor.fetchall()
        
        if not attempts:
            return jsonify({'attempts': []}), 200
        
        # Parse JSON results and analyze risk for each attempt
        processed_attempts = []
        for attempt in attempts:
            results_data = json.loads(attempt['results']) if isinstance(attempt['results'], str) else attempt['results']
            
            # The results_data IS the games data (not wrapped in a 'games' key)
            # Call the analysis function
            risk_level, details = analyze_dyscalculia_results(results_data)
            
            processed_attempts.append({
                'id': attempt['id'],
                'student_id': attempt['student_id'],
                'assessment_id': attempt['assessment_id'],
                'results': results_data,
                'risk_level': risk_level,
                'details': details,
                'status': attempt['status'],
                'created_at': attempt['created_at'].isoformat() if hasattr(attempt['created_at'], 'isoformat') else str(attempt['created_at'])
            })
        
        return jsonify({'attempts': processed_attempts}), 200
    
    except Exception as e:
        print(f"[ERROR] Get dyscalculia results error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@assessment_bp.route('/dysgraphia-results/<int:assessment_id>', methods=['GET'])
def get_dysgraphia_results(assessment_id):
    """Get all dysgraphia assessment attempts for current student"""
    conn = None
    cursor = None
    try:
        student_id = session.get('user_id')
        if not student_id:
            return jsonify({'attempts': [], 'is_guest': True}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all attempts for this assessment
        cursor.execute('''
            SELECT ar.id, ar.student_id, ar.assessment_id, ar.results, ar.status, ar.created_at
            FROM assessment_results ar
            WHERE ar.student_id = %s AND ar.assessment_id = %s
            ORDER BY ar.created_at DESC
        ''', (student_id, assessment_id))
        
        attempts = cursor.fetchall()
        
        if not attempts:
            return jsonify({'attempts': []}), 200
        
        # Parse JSON results and analyze risk for each attempt
        processed_attempts = []
        for attempt in attempts:
            results_data = json.loads(attempt['results']) if isinstance(attempt['results'], str) else attempt['results']
            
            # The results_data IS the games data (not wrapped in a 'games' key)
            # Call the analysis function
            risk_level, details = analyze_dysgraphia_results(results_data)
            
            processed_attempts.append({
                'id': attempt['id'],
                'student_id': attempt['student_id'],
                'assessment_id': attempt['assessment_id'],
                'results': results_data,
                'risk_level': risk_level,
                'details': details,
                'status': attempt['status'],
                'created_at': attempt['created_at'].isoformat() if hasattr(attempt['created_at'], 'isoformat') else str(attempt['created_at'])
            })
        
        return jsonify({'attempts': processed_attempts}), 200
    
    except Exception as e:
        print(f"[ERROR] Get dysgraphia results error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def analyze_dyslexia_results(games):
    """Analyze dyslexia game results and return risk level with details"""
    def _safe(v, default=0.0):
        try:
            return float(v)
        except:
            return default
    
    # Scoring weights from model.py
    weight_map = {
        'phoneme_delete': 1.6,
        'letter_sound': 1.5,
        'rhyme_recog': 1.2,
        'word_scramble': 1.3,
        'lexical_decision': 1.2,
        'rapid_naming': 1.4
    }
    
    per_task = {}
    aggregate = 0.0
    weight_sum = 0.0
    warnings = []
    
    for g, w in weight_map.items():
        d = games.get(g, {})
        correct = _safe(d.get('correct', 0))
        total = max(1.0, _safe(d.get('total', 1)))
        acc = correct / total
        avg_rt = _safe(d.get('avg_rt', 1000))  # ms
        
        # Expected baselines
        expected_acc = 0.78
        expected_rt = 1200
        
        acc_score = (acc - expected_acc)
        rt_penalty = (avg_rt - expected_rt) / 2500.0
        comp = acc_score - rt_penalty
        
        per_task[g] = {
            'acc': round(acc, 3),
            'avg_rt': int(round(avg_rt)),
            'component': round(comp, 3)
        }
        
        aggregate += comp * w
        weight_sum += w
        
        # Flags
        if acc < 0.55:
            warnings.append(f'Low accuracy in {g} ({acc:.2f})')
        if avg_rt > 2500:
            warnings.append(f'Slow responses in {g} (avg {int(avg_rt)}ms)')
    
    norm = aggregate / max(1e-6, weight_sum)
    
    # Convert normalized score to risk
    if norm >= -0.04:
        risk = "No risk likely"
    elif norm >= -0.22:
        risk = "Low risk"
    elif norm >= -0.5:
        risk = "Medium risk"
    else:
        risk = "High risk"
    
    details = {
        'norm_score': round(norm, 3),
        'per_task': per_task,
        'warnings': warnings
    }
    
    return risk, details


def analyze_dyscalculia_results(games):
    """Analyze dyscalculia game results and return risk level with details"""
    def _safe(v, default=0.0):
        try:
            return float(v)
        except:
            return default
    
    # Scoring weights
    weight_map = {
        'subitizing': 1.5,
        'comparison': 1.2,
        'symbol_match': 1.4,
        'sequencing': 1.3,
        'memory_span': 1.1,
        'story_arith': 1.4
    }
    
    scores = {}
    aggregate = 0.0
    weight_sum = 0.0
    warnings = []
    
    for g, w in weight_map.items():
        gdata = games.get(g, {})
        correct = _safe(gdata.get('correct', 0))
        total = max(1.0, _safe(gdata.get('total', 1)))
        acc = correct / total
        rt = _safe(gdata.get('avg_rt', 1500))  # Default 1500ms
        
        expected_acc = 0.8
        expected_rt = 1500  # Expected response time: 1.5 seconds (balanced)
        
        acc_score = (acc - expected_acc)
        # Balanced penalty: 1500ms = no penalty, 3500ms = 0.5 penalty, 4000ms+ = high penalty
        rt_penalty = max(0, (rt - expected_rt) / 2500.0)  # Balanced divisor
        comp_score = acc_score - rt_penalty
        
        scores[g] = {
            'acc': round(acc, 3),
            'avg_rt': round(rt, 1),
            'component': round(comp_score, 3)
        }
        
        aggregate += comp_score * w
        weight_sum += w
        
        if acc < 0.5:
            warnings.append(f'Low accuracy in {g} ({acc:.2f})')
        if rt > 3500:  # Warning if response time exceeds 3.5 seconds
            warnings.append(f'Slow responses in {g} (avg {rt:.0f}ms)')
    
    norm = aggregate / max(1e-6, weight_sum)
    
    if norm >= -0.05:
        risk = "No risk likely"
    elif norm >= -0.25:
        risk = "Low risk"
    elif norm >= -0.6:
        risk = "Medium risk"
    else:
        risk = "High risk"
    
    details = {
        'norm_score': round(norm, 3),
        'per_task': scores,
        'warnings': warnings
    }
    
    return risk, details


def analyze_dysgraphia_results(games):
    """Analyze dysgraphia game results and return risk level with details"""
    def _safe(v, default=0.0):
        try:
            return float(v)
        except:
            return default
    
    def path_length(points):
        if len(points) < 2:
            return 0.0
        s = 0.0
        for i in range(1, len(points)):
            s += ((points[i][0]-points[i-1][0])**2 + (points[i][1]-points[i-1][1])**2)**0.5
        return s
    
    def analyze_task(task):
        strokes = task.get('strokes', [])
        all_pts = []
        for s in strokes:
            pts = s.get('points', [])
            for p in pts:
                all_pts.append(p)
        
        n_strokes = len(strokes)
        duration = _safe(task.get('duration_ms', 0))
        length = path_length(all_pts)
        lifts = max(0, n_strokes - 1)
        lifts_per_s = (lifts / (duration/1000.0)) if duration > 0 else lifts
        
        return {
            'n_strokes': n_strokes,
            'duration_ms': int(duration),
            'smoothness': 0.5,  # placeholder
            'avg_speed_px_s': (length / max(1, duration)) * 1000.0 if duration > 0 else 0.0,
            'path_length_px': round(length, 2),
            'lifts': lifts,
            'lifts_per_s': round(lifts_per_s, 3)
        }
    
    per_task = {}
    for name, data_task in games.items():
        per_task[name] = analyze_task(data_task)
    
    scores = {}
    for name, metrics in per_task.items():
        duration = _safe(metrics.get('duration_ms', 1000))
        lifts_per_s = _safe(metrics.get('lifts_per_s', 0))
        
        expected_duration = 2500.0
        expected_lifts = 0.8
        
        dur_score = 1.0 - min(1.0, (duration / expected_duration) - 1.0)
        lift_score = max(0.0, 1.0 - (lifts_per_s / max(0.1, expected_lifts)))
        comp = (0.5 * lift_score) + (0.5 * dur_score)
        task_score = (comp - 0.5) * 2.0
        scores[name] = round(task_score, 3)
    
    weight_map = {
        'trace_line': 1.2,
        'copy_letter': 1.5,
        'write_audio': 1.3,
        'timed_write': 1.2,
        'shape_draw': 1.0
    }
    
    aggregate = 0.0
    wsum = 0.0
    warnings = []
    
    for k, w in weight_map.items():
        s = scores.get(k, 0.0)
        aggregate += s * w
        wsum += w
        if s < -0.6:
            warnings.append(f'Significant difficulty on {k} (score {s:.2f})')
        elif s < -0.25:
            warnings.append(f'Some difficulty on {k} (score {s:.2f})')
    
    norm = aggregate / max(1e-9, wsum)
    
    if norm >= 0.0:
        risk = "No risk likely"
    elif norm >= -0.25:
        risk = "Low risk"
    elif norm >= -0.55:
        risk = "Medium risk"
    else:
        risk = "High risk"
    
    details = {
        'norm_score': round(norm, 3),
        'per_task_metrics': per_task,
        'task_scores': scores,
        'warnings': warnings
    }
    
    return risk, details




@assessment_bp.route('/analyze-dyscalculia', methods=['POST'])
def analyze_dyscalculia():
    """Analyze dyscalculia game results using Neural Network ML model"""
    try:
        data = request.get_json()
        games = data.get('games', {})
        student_id = data.get('student_id', session.get('user_id'))
        
        print(f"[DEBUG] Analyzing dyscalculia results using Neural Network: {list(games.keys())}")
        
        # Use neural network predictor
        dyscalculia_model = DyscalculiaDeepLearning()
        
        # Extract advanced features from game data
        session_data = {'games': games}
        features = dyscalculia_model.extract_advanced_features(session_data)
        
        # Make prediction
        result = dyscalculia_model.predict_risk(session_data)
        
        # Extract answers from games for detailed analysis
        answers = []
        for game_name, game_data in games.items():
            if isinstance(game_data, dict) and 'questions' in game_data:
                for q_idx, question in enumerate(game_data['questions']):
                    answers.append({
                        'question_text': question.get('text', f'{game_name} - Question {q_idx + 1}'),
                        'user_answer': question.get('userAnswer', ''),
                        'correct_answer': question.get('correctAnswer', ''),
                        'is_correct': question.get('isCorrect', False),
                        'time_spent_seconds': question.get('timeSpent', 0) / 1000.0,  # Convert ms to seconds
                        'difficulty_level': question.get('difficulty', 'medium')
                    })
        
        # Generate detailed analysis with per-question metrics
        detailed_analysis = generate_detailed_analysis(answers, 'dyscalculia')
        
        # Build clean per_task map for each game
        per_task = {}
        for g_name, g_data in games.items():
            if isinstance(g_data, dict):
                c = g_data.get('correct', 0)
                tot = g_data.get('total', 0) or 1
                acc = round((c / tot * 100), 1) if tot > 0 else 0
                avg_rt = g_data.get('avg_rt', 0)
                per_task[g_name] = {
                    'acc': f"{acc}%",
                    'accuracy': acc,
                    'avg_rt': avg_rt,
                    'correct': c,
                    'total': tot
                }

        # Prepare response with detailed neural analysis
        response = {
            'risk': result['risk_level'],
            'risk_score': result['risk_score'],
            'confidence': result['confidence'],
            'details': {
                'norm_score': result['risk_score'],
                'per_task': per_task,
                'per_task_metrics': per_task,
                'detailed_analysis': detailed_analysis,
                'by_difficulty': detailed_analysis.get('by_difficulty', {}),
                'per_question': detailed_analysis.get('per_question', {}),
                'overall': detailed_analysis.get('overall', {}),
                'neural_analysis': result.get('detailed_analysis', {}),
                'warnings': result.get('recommendations', []),
                'model_version': '2.0 - Neural Networks',
                'features_analyzed': len(features[0]) if (features is not None and len(features) > 0) else 20,
                'confidence_threshold': 0.65
            }
        }
        
        print(f"[DEBUG] Neural dyscalculia analysis complete: risk={result['risk_level']}, confidence={result['confidence']:.2%}")
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"[ERROR] Dyscalculia analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'risk': 'Unable to analyze'}), 500


@assessment_bp.route('/analyze-dysgraphia', methods=['POST'])
def analyze_dysgraphia():
    """Analyze dysgraphia game results using Neural Network ML model"""
    try:
        data = request.get_json()
        games = data.get('games', {})
        student_id = data.get('student_id', session.get('user_id'))
        
        print(f"[DEBUG] Analyzing dysgraphia results using Neural Network: {list(games.keys())}")
        
        # Use neural network predictor
        dysgraphia_model = DysgraphiaDeepLearning()
        
        # Extract advanced features from game data
        session_data = {'games': games}
        features = dysgraphia_model.extract_advanced_features(session_data)
        
        # Make prediction
        result = dysgraphia_model.predict_risk(session_data)
        
        # Extract answers from games for detailed analysis
        answers = []
        for game_name, game_data in games.items():
            if isinstance(game_data, dict) and 'questions' in game_data:
                for q_idx, question in enumerate(game_data['questions']):
                    answers.append({
                        'question_text': question.get('text', f'{game_name} - Question {q_idx + 1}'),
                        'user_answer': question.get('userAnswer', ''),
                        'correct_answer': question.get('correctAnswer', ''),
                        'is_correct': question.get('isCorrect', False),
                        'time_spent_seconds': question.get('timeSpent', 0) / 1000.0,  # Convert ms to seconds
                        'difficulty_level': question.get('difficulty', 'medium')
                    })
        
        # Generate detailed analysis with per-question metrics
        detailed_analysis = generate_detailed_analysis(answers, 'dysgraphia')
        
        # Build clean per_task map for each game/task from actual user strokes or performance
        per_task = {}
        for g_name, g_data in games.items():
            if isinstance(g_data, dict):
                dur = g_data.get('duration_ms', 5000)
                strokes = g_data.get('strokes', [])
                if 'smoothness' in g_data:
                    smooth = float(g_data['smoothness'])
                elif strokes:
                    smooth = dysgraphia_model._calculate_stroke_smoothness(strokes)
                elif 'questions' in g_data and len(g_data['questions']) > 0:
                    c = sum(1 for q in g_data['questions'] if q.get('isCorrect'))
                    smooth = c / len(g_data['questions'])
                else:
                    smooth = 0.0
                
                acc_val = int(round(smooth * 100))
                per_task[g_name] = {
                    'smoothness': f"{acc_val}%",
                    'acc': f"{acc_val}%",
                    'accuracy': acc_val,
                    'avg_rt': dur,
                    'duration_ms': dur
                }

        # Prepare response with detailed neural analysis
        response = {
            'risk': result['risk_level'],
            'risk_score': result['risk_score'],
            'confidence': result['confidence'],
            'details': {
                'norm_score': result['risk_score'],
                'per_task': per_task,
                'per_task_metrics': per_task,
                'detailed_analysis': detailed_analysis,
                'by_difficulty': detailed_analysis.get('by_difficulty', {}),
                'per_question': detailed_analysis.get('per_question', {}),
                'overall': detailed_analysis.get('overall', {}),
                'neural_analysis': result.get('detailed_analysis', {}),
                'warnings': result.get('recommendations', []),
                'model_version': '2.0 - Neural Networks',
                'features_analyzed': len(features[0]) if (features is not None and len(features) > 0) else 20,
                'confidence_threshold': 0.65
            }
        }
        
        print(f"[DEBUG] Neural dysgraphia analysis complete: risk={result['risk_level']}, confidence={result['confidence']:.2%}")
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"[ERROR] Dysgraphia analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'risk': 'Unable to analyze'}), 500


# Register blueprint in main app
def register_assessment_routes(app):
    """Register assessment blueprint to main Flask app"""
    app.register_blueprint(assessment_bp)

