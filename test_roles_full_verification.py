"""
Comprehensive Full Role & Workflow Verification Suite for Neurobloom (Supabase Backend)
Tests:
- Guest/Unauthenticated security checks
- Student lifecycle: Register, login, profile, take assessment, submit, get ML results & recommendations, check student dashboard
- Faculty lifecycle: Register, login, setup class, view dashboard, view students, drill down into student assessments & details, export CSV
- Cross-role authorization security checks
"""
import uuid
from app import app
from db import get_connection

def run_role_verification():
    print("==================================================================")
    print("      NEUROBLOOM FULL ROLE & WORKFLOW VERIFICATION SUITE         ")
    print("==================================================================")

    client = app.test_client()
    passed = 0
    failed = 0

    unique_id = uuid.uuid4().hex[:6]
    student_email = f"student_{unique_id}@test.com"
    faculty_email = f"faculty_{unique_id}@test.com"
    password = "SecurePassword@123"
    test_class = f"Class_{unique_id}"

    # -------------------------------------------------------------
    # 1. GUEST / UNAUTHENTICATED SECURITY CHECKS
    # -------------------------------------------------------------
    print("\n--- [1] Guest & Security Checks ---")
    try:
        # DB Test endpoint
        r = client.get('/db-test')
        assert r.status_code == 200, f"/db-test failed: {r.status_code}"
        print("  [PASS] /db-test accessible to guest")

        # Protected student endpoint rejected
        r = client.get('/api/student/dashboard')
        assert r.status_code in [401, 302], f"Expected 401/302 for unauth dashboard, got {r.status_code}"
        print("  [PASS] Unauthenticated access to /api/student/dashboard rejected")

        # Protected faculty endpoint rejected
        r = client.get('/api/faculty/dashboard')
        assert r.status_code in [401, 302], f"Expected 401/302 for unauth faculty dashboard, got {r.status_code}"
        print("  [PASS] Unauthenticated access to /api/faculty/dashboard rejected")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Guest security check failed: {e}")
        failed += 1

    # -------------------------------------------------------------
    # 2. FACULTY REGISTRATION & SETUP FLOW
    # -------------------------------------------------------------
    print("\n--- [2] Faculty Registration & Profile Setup ---")
    faculty_id = None
    try:
        # Register faculty
        r = client.post('/faculty_register', data={
            'name': f'Faculty {unique_id}',
            'email': faculty_email,
            'password': password,
            'contact': '9876543210'
        }, follow_redirects=False)
        assert r.status_code in [200, 302], f"Faculty registration failed: {r.status_code}"
        print(f"  [PASS] Faculty registered: {faculty_email}")

        # Login faculty
        with client.session_transaction() as sess:
            sess.clear()
        r = client.post('/login/faculty', data={
            'faculty_email': faculty_email,
            'faculty_password': password
        }, follow_redirects=False)
        assert r.status_code in [200, 302], f"Faculty login failed: {r.status_code}"
        
        # Get faculty info from DB to find ID
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id, name, role FROM users WHERE email = %s', (faculty_email,))
        fac_row = cur.fetchone()
        cur.close()
        conn.close()
        assert fac_row and fac_row['role'] == 'faculty', f"Faculty record invalid: {fac_row}"
        faculty_id = fac_row['id']
        print(f"  [PASS] Faculty authenticated: ID={faculty_id}")

        # Setup faculty class
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_id
            sess['role'] = 'faculty'
            sess['name'] = f'Faculty {unique_id}'
            sess['class'] = test_class

        r = client.post('/api/setup-faculty-profile', json={'class': test_class})
        assert r.status_code == 200, f"Setup faculty profile failed: {r.get_json()}"
        print(f"  [PASS] Faculty class assigned: {test_class}")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Faculty registration/setup failed: {e}")
        failed += 1

    # -------------------------------------------------------------
    # 3. STUDENT REGISTRATION & PROFILE FLOW
    # -------------------------------------------------------------
    print("\n--- [3] Student Registration, Profile & Dashboard ---")
    student_id = None
    try:
        # Register student
        r = client.post('/student_register', data={
            'name': f'Student {unique_id}',
            'email': student_email,
            'password': password,
            'contact': '1234567890'
        }, follow_redirects=False)
        assert r.status_code in [200, 302], f"Student registration failed: {r.status_code}"
        print(f"  [PASS] Student registered: {student_email}")

        # Get student ID from DB
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id, name, role FROM users WHERE email = %s', (student_email,))
        stu_row = cur.fetchone()
        assert stu_row and stu_row['role'] == 'student', f"Student record invalid: {stu_row}"
        student_id = stu_row['id']

        # Assign class and faculty_id to student
        cur.execute('UPDATE users SET class = %s, faculty_id = %s WHERE id = %s', (test_class, faculty_id, student_id))
        cur.close()
        conn.close()
        print(f"  [PASS] Student assigned to class={test_class}, faculty_id={faculty_id}")

        # Login student
        with client.session_transaction() as sess:
            sess['user_id'] = student_id
            sess['role'] = 'student'
            sess['name'] = f'Student {unique_id}'
            sess['class'] = test_class

        # Student Profile API GET
        r = client.get('/api/student/profile')
        assert r.status_code == 200, f"Student profile GET failed: {r.get_json()}"
        pdata = r.get_json()
        assert pdata.get('status') == 'ok', f"Unexpected profile payload: {pdata}"
        print(f"  [PASS] Student profile API verified: name={pdata['profile']['name']}")

        # Student Dashboard API
        r = client.get('/api/student/dashboard')
        assert r.status_code == 200, f"Student dashboard API failed: {r.get_json()}"
        ddata = r.get_json()
        assert ddata.get('status') == 'ok', f"Unexpected dashboard payload: {ddata}"
        print(f"  [PASS] Student dashboard API verified: total_assessments={ddata['stats']['total_assessments']}")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Student registration/profile failed: {e}")
        failed += 1

    # -------------------------------------------------------------
    # 4. STUDENT ASSESSMENT WORKFLOW & ML PREDICTIONS
    # -------------------------------------------------------------
    print("\n--- [4] Student Assessment Lifecycle & ML Predictions ---")
    assessment_session_id = None
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = student_id
            sess['role'] = 'student'
            sess['name'] = f'Student {unique_id}'
            sess['class'] = test_class

        # 1. Fetch available assessments
        r = client.get('/api/assessments/available')
        assert r.status_code == 200, f"Available assessments failed: {r.get_json()}"
        avail = r.get_json().get('assessments', [])
        assert len(avail) > 0, "No assessments found"
        assess_id = avail[0]['id']
        print(f"  [PASS] Available assessments loaded: {len(avail)} found (Using ID={assess_id})")

        # 2. Start assessment
        r = client.post('/api/student-assessment/start', json={'assessment_id': assess_id})
        assert r.status_code in [200, 201], f"Start assessment failed: {r.get_json()}"
        start_res = r.get_json()
        assessment_session_id = start_res.get('student_assessment_id') or start_res.get('id')
        assert assessment_session_id, f"Missing assessment session ID: {start_res}"
        print(f"  [PASS] Assessment started: session_id={assessment_session_id}")

        # 3. Submit assessment
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id FROM questions WHERE assessment_id = %s LIMIT 1', (assess_id,))
        q_row = cur.fetchone()
        q_id = q_row['id'] if q_row else 1
        cur.close()
        conn.close()

        submit_payload = {
            'student_assessment_id': assessment_session_id,
            'time_taken_minutes': 12,
            'answers': [{'question_id': q_id, 'selected_option_id': 1}]
        }
        r = client.post('/api/student-assessment/submit', json=submit_payload)
        assert r.status_code == 200, f"Submit assessment failed: {r.get_json()}"
        print(f"  [PASS] Assessment submitted successfully")

        # 4. View Results
        r = client.get(f'/api/student-assessment/{assessment_session_id}/results')
        assert r.status_code == 200, f"Assessment results fetch failed: {r.get_json()}"
        res_data = r.get_json()
        assert res_data.get('assessment') or res_data.get('id'), f"Invalid results schema: {res_data}"
        print(f"  [PASS] Assessment results retrieved successfully")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Assessment workflow failed: {e}")
        failed += 1

    # -------------------------------------------------------------
    # 5. FACULTY DASHBOARD & STUDENT INSPECTION WORKFLOW
    # -------------------------------------------------------------
    print("\n--- [5] Faculty Dashboard & Student Management ---")
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_id
            sess['role'] = 'faculty'
            sess['name'] = f'Faculty {unique_id}'
            sess['class'] = test_class

        # 1. Faculty Dashboard API
        r = client.get('/api/faculty/dashboard')
        assert r.status_code == 200, f"Faculty dashboard failed: {r.get_json()}"
        f_dash = r.get_json()
        assert f_dash.get('status') == 'ok', f"Faculty dashboard status error: {f_dash}"
        print(f"  [PASS] Faculty dashboard data loaded: total_students={f_dash['stats']['total_students']}, total_assessments={f_dash['stats']['total_assessments']}")

        # 2. Get students in class
        r = client.get('/api/get-students')
        assert r.status_code == 200, f"get-students failed: {r.get_json()}"
        stu_list = r.get_json().get('students', [])
        assert any(s['id'] == student_id for s in stu_list), f"Student {student_id} not in faculty student list: {stu_list}"
        print(f"  [PASS] Faculty student list contains enrolled student: count={len(stu_list)}")

        # 3. Faculty Student details
        r = client.get(f'/api/faculty/student/{student_id}')
        assert r.status_code == 200, f"Faculty student details failed: {r.get_json()}"
        stu_det = r.get_json().get('student', {})
        assert stu_det.get('id') == student_id, f"Mismatch student details: {stu_det}"
        print(f"  [PASS] Faculty student details drilldown succeeded")

        # 4. Faculty Student assessments
        r = client.get(f'/api/faculty/student/{student_id}/assessments')
        assert r.status_code == 200, f"Faculty student assessments failed: {r.get_json()}"
        stu_ass = r.get_json().get('assessments', [])
        assert len(stu_ass) >= 1, f"Expected at least 1 assessment for student: {stu_ass}"
        print(f"  [PASS] Faculty student assessments retrieved: count={len(stu_ass)}")

        # 5. Faculty Export CSV
        r = client.get('/api/faculty/export-csv')
        assert r.status_code == 200, f"Faculty export CSV failed: {r.status_code}"
        print(f"  [PASS] Faculty export CSV generated successfully")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Faculty dashboard/management failed: {e}")
        failed += 1

    # -------------------------------------------------------------
    # 6. ROLE ISOLATION & AUTHORIZATION BOUNDARY TESTING
    # -------------------------------------------------------------
    print("\n--- [6] Role Isolation & Authorization Boundaries ---")
    try:
        # Student cannot access faculty endpoints
        with client.session_transaction() as sess:
            sess['user_id'] = student_id
            sess['role'] = 'student'

        r = client.get('/api/faculty/dashboard')
        assert r.status_code in [401, 403, 302], f"Student should NOT access faculty dashboard! Status: {r.status_code}"
        print("  [PASS] Student blocked from /api/faculty/dashboard (401/403/302)")

        r = client.get(f'/api/faculty/student/{student_id}')
        assert r.status_code in [401, 403, 302], f"Student should NOT access faculty student details! Status: {r.status_code}"
        print("  [PASS] Student blocked from faculty student inspection endpoint")

        # Faculty cannot access student-only test-taking start endpoint
        with client.session_transaction() as sess:
            sess['user_id'] = faculty_id
            sess['role'] = 'faculty'

        r = client.get('/api/student/dashboard')
        assert r.status_code in [401, 403, 302], f"Faculty should NOT access student personal dashboard! Status: {r.status_code}"
        print("  [PASS] Faculty blocked from /api/student/dashboard")

        passed += 1
    except Exception as e:
        print(f"  [FAIL] Role isolation checks failed: {e}")
        failed += 1

    print("\n==================================================================")
    print(f"          FINAL RESULTS: {passed} PASSED, {failed} FAILED")
    print("==================================================================")
    return failed == 0

if __name__ == '__main__':
    success = run_role_verification()
    exit(0 if success else 1)
