"""
End-to-End Validation Suite for Supabase-backed Neurobloom.
Tests:
1. Database connectivity & DB version endpoint
2. User registration (Student and Faculty)
3. Authentication & Session logic
4. Assessment APIs (/api/assessments/available, /api/assessment/<id>)
5. Assessment submission & score calculation
6. ML Predictions & Recommendations generation
7. Student dashboard & stats endpoints
8. Faculty dashboard & student filtering endpoints
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from db import get_connection, get_db_connection, get_supabase_client
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, insert_user, authenticate_user

client = app.test_client()

def run_all_tests():
    passed = 0
    failed = 0

    print("==========================================================")
    print("      NEUROBLOOM FULL BACKEND SUPABASE TEST SUITE         ")
    print("==========================================================\n")

    # TEST 1: DB Connectivity & db-test endpoint
    print("--- [TEST 1] DB Connectivity & /db-test endpoint ---")
    try:
        response = client.get('/db-test')
        data = response.get_json()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data.get('status') == 'ok', f"Expected status ok, got {data}"
        print(f"  [PASS] /db-test succeeded: {data}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] /db-test failed: {e}")
        failed += 1

    # TEST 2: Schema Integrity across all 11 tables
    print("\n--- [TEST 2] Schema Verification (11 tables) ---")
    tables = [
        'users', 'assessment_types', 'questions', 'answer_options',
        'student_assessments', 'student_answers', 'student_progress',
        'assessment_results', 'recommendations', 'ml_predictions', 'faculty_notes'
    ]
    all_tables_ok = True
    for tbl in tables:
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {tbl} LIMIT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            print(f"  [PASS] Table '{tbl}' verified in Supabase")
        except Exception as e:
            print(f"  [FAIL] Table '{tbl}' error: {e}")
            all_tables_ok = False
    if all_tables_ok:
        passed += 1
    else:
        failed += 1

    # TEST 3: User Registration & Authentication Flow
    print("\n--- [TEST 3] User Registration & Password Hashing Flow ---")
    test_id = uuid.uuid4().hex[:6]
    student_email = f"test_student_{test_id}@example.com"
    faculty_email = f"test_faculty_{test_id}@example.com"
    raw_password = "SecurePassword@123"

    try:
        # Register student
        hashed = generate_password_hash(raw_password)
        ok, err = insert_user(f"Test Student {test_id}", student_email, hashed, "1234567890", role='student')
        assert ok, f"Student insert failed: {err}"
        print(f"  [PASS] Student registered: {student_email}")

        # Register faculty
        ok, err = insert_user(f"Test Faculty {test_id}", faculty_email, hashed, "0987654321", role='faculty')
        assert ok, f"Faculty insert failed: {err}"
        print(f"  [PASS] Faculty registered: {faculty_email}")

        # Authenticate student
        auth_ok, student_row = authenticate_user(student_email, raw_password, expected_role='student')
        assert auth_ok, f"Student authentication failed: {student_row}"
        assert student_row['email'] == student_email, "Email mismatch in auth result"
        print(f"  [PASS] Student authenticated: ID={student_row.get('id')}")

        # Authenticate with wrong password
        wrong_auth, _ = authenticate_user(student_email, "WrongPassword", expected_role='student')
        assert not wrong_auth, "Authentication should fail with wrong password"
        print("  [PASS] Invalid password rejected correctly")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Auth flow failed: {e}")
        failed += 1

    # TEST 4: Assessment Data Retrieval
    print("\n--- [TEST 4] Assessment Data Retrieval ---")
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = student_row['id']
            sess['role'] = 'student'
            sess['name'] = student_row['name']

        # Available assessments endpoint
        resp = client.get('/api/assessments/available')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.get_json()
        assert 'assessments' in data or isinstance(data, list) or len(data) > 0, "No assessments returned"
        print(f"  [PASS] Available assessments endpoint returned data")

        # Specific assessment details (Assessment 1 - Dyslexia)
        resp = client.get('/api/assessment/1')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        a_data = resp.get_json()
        a_id = a_data.get('id') or a_data.get('assessment', {}).get('id')
        assert a_id == 1, f"Assessment ID mismatch: {a_data}"
        questions = a_data.get('questions', [])
        assert len(questions) > 0, "No questions returned for assessment 1"
        print(f"  [PASS] Assessment 1 loaded with {len(questions)} questions")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Assessment retrieval failed: {e}")
        failed += 1

    # TEST 5: Assessment Session & Submission Lifecycle
    print("\n--- [TEST 5] Assessment Lifecycle (Start & Submit) ---")
    try:
        # Create session with logged in student
        with client.session_transaction() as sess:
            sess['user_id'] = student_row['id']
            sess['role'] = 'student'
            sess['name'] = student_row['name']

        # Start assessment 1
        resp = client.post('/api/student-assessment/start', json={'assessment_id': 1})
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.get_json()}"
        sa_id = resp.get_json().get('student_assessment_id')
        assert sa_id, "No student_assessment_id returned"
        print(f"  [PASS] Started assessment session ID: {sa_id}")

        # Submit answers
        submit_payload = {
            'student_assessment_id': sa_id,
            'assessment_id': 1,
            'answers': {
                '1': '6',      # Question 1: '6' is correct
                '2': 'receive',# Question 2: 'receive' is correct
                '3': 'true',   # Question 3: 'true' is correct
                '4': 'slow'    # Question 4: 'slow' is correct
            },
            'time_spent': 120
        }
        resp = client.post('/api/student-assessment/submit', json=submit_payload)
        assert resp.status_code == 200, f"Submit failed: {resp.get_json()}"
        sub_res = resp.get_json()
        print(f"  [PASS] Assessment submitted successfully: score={sub_res.get('percentage_score')}%")

        # Check results
        resp = client.get(f'/api/student-assessment/{sa_id}/results')
        assert resp.status_code == 200, f"Results fetch failed: {resp.get_json()}"
        res_data = resp.get_json()
        res_id = res_data.get('id') or res_data.get('assessment', {}).get('id')
        assert res_id == sa_id, f"Result ID mismatch: {res_data}"
        status_val = res_data.get('status') or res_data.get('assessment', {}).get('status')
        print(f"  [PASS] Results retrieved: status={status_val}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Assessment lifecycle failed: {e}")
        failed += 1

    # TEST 6: ML Prediction & Recommendations
    print("\n--- [TEST 6] ML Risk Analysis & Recommendations ---")
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = student_row['id']
            sess['role'] = 'student'

        # Analyze dyslexia
        analysis_payload = {
            'student_id': student_row['id'],
            'assessment_id': 1,
            'responses': {
                'phoneme_delete': {'correct': 5, 'total': 6, 'avg_rt': 1200},
                'letter_sound': {'correct': 8, 'total': 9, 'avg_rt': 900},
                'rapid_naming': {'correct': 45, 'total': 48, 'avg_rt': 1500}
            }
        }
        resp = client.post('/api/analyze-dyslexia', json=analysis_payload)
        assert resp.status_code == 200, f"Analysis failed: {resp.get_json()}"
        pred_data = resp.get_json()
        print(f"  [PASS] Dyslexia ML analysis succeeded: risk_level={pred_data.get('risk_level')}")

        # Submit integrated assessment results
        save_payload = {
            'student_id': student_row['id'],
            'assessment_id': 1,
            'results': analysis_payload['responses'],
            'risk_level': pred_data.get('risk_level', 'low')
        }
        resp = client.post('/api/submit-assessment', json=save_payload)
        assert resp.status_code == 200, f"Save results failed: {resp.get_json()}"
        print(f"  [PASS] Assessment results & recommendations stored successfully")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] ML Prediction failed: {e}")
        failed += 1

    # TEST 7: Student Dashboard & Stats Endpoints
    print("\n--- [TEST 7] Student Dashboard APIs ---")
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = student_row['id']
            sess['role'] = 'student'

        resp = client.get('/api/student-stats')
        assert resp.status_code == 200, f"Student stats failed: {resp.get_json()}"
        stats = resp.get_json()
        print(f"  [PASS] Student stats retrieved: total_assessments={stats.get('total_assessments')}")

        resp = client.get('/api/student-info')
        assert resp.status_code == 200, f"Student info failed: {resp.get_json()}"
        info = resp.get_json()
        print(f"  [PASS] Student info retrieved: {info.get('name')}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Student dashboard APIs failed: {e}")
        failed += 1

    # TEST 8: Faculty APIs
    print("\n--- [TEST 8] Faculty APIs & Student Views ---")
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = 21  # Krishn Kumar (faculty)
            sess['role'] = 'faculty'
            sess['name'] = 'Krishn Kumar'

        resp = client.get('/api/faculty/dashboard')
        assert resp.status_code == 200, f"Faculty dashboard failed: {resp.get_json()}"
        f_data = resp.get_json()
        print(f"  [PASS] Faculty dashboard data retrieved: stats={f_data.get('stats')}")

        resp = client.get('/api/faculty/students')
        assert resp.status_code == 200, f"Faculty students failed: {resp.get_json()}"
        st_list = resp.get_json()
        print(f"  [PASS] Faculty student list retrieved: count={len(st_list.get('students', []))}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Faculty APIs failed: {e}")
        failed += 1

    print("\n==========================================================")
    print(f"             TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("==========================================================")
    return failed == 0

if __name__ == '__main__':
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
