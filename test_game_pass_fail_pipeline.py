import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("=" * 70)
    print("STARTING END-TO-END GAME PIPELINE PASS & FAIL VERIFICATION")
    print("=" * 70)
    
    # Session for Student
    student_session = requests.Session()
    faculty_session = requests.Session()
    
    # 1. Register & Login Student
    student_email = f"student_game_test_{int(time.time())}@example.com"
    stu_reg = student_session.post(f"{BASE_URL}/student_register", data={
        "name": "Pipeline Student",
        "email": student_email,
        "password": "Password123!",
        "contact": "9876543210"
    })
    print(f"[*] Student registration: status={stu_reg.status_code}")
    
    stu_login = student_session.post(f"{BASE_URL}/login/student", data={
        "student_email": student_email,
        "student_password": "Password123!"
    })
    print(f"[*] Student login: status={stu_login.status_code}")
    assert stu_login.status_code == 200, f"Student login failed: {stu_login.text}"
    
    # Get student profile to verify login session
    prof_init = student_session.get(f"{BASE_URL}/api/student/profile")
    assert prof_init.status_code == 200, f"Failed to get student profile: {prof_init.text}"
    student_id = prof_init.json()['profile']['id']
    print(f"    Student ID: {student_id}")

    # Set student class to Class-Game-Test
    student_session.put(f"{BASE_URL}/api/student/profile", json={"class": "Class-Game-Test"})

    # 2. Register & Login Faculty
    faculty_email = f"faculty_game_test_{int(time.time())}@example.com"
    fac_reg = faculty_session.post(f"{BASE_URL}/faculty_register", data={
        "name": "Pipeline Faculty",
        "email": faculty_email,
        "password": "Password123!",
        "contact": "9876543211"
    })
    print(f"[*] Faculty registration: status={fac_reg.status_code}")
    
    fac_login = faculty_session.post(f"{BASE_URL}/login/faculty", data={
        "faculty_email": faculty_email,
        "faculty_password": "Password123!"
    })
    print(f"[*] Faculty login: status={fac_login.status_code}")
    assert fac_login.status_code == 200, f"Faculty login failed: {fac_login.text}"

    # Set faculty class to Class-Game-Test
    faculty_session.put(f"{BASE_URL}/api/faculty-info", json={"class": "Class-Game-Test"})

    # -------------------------------------------------------------
    # 3. DYSLEXIA ASSESSMENT (ID: 1) - PASS & FAIL FLOWS
    # -------------------------------------------------------------
    print("\n--- Testing Dyslexia (ID 1) ---")
    
    # Dyslexia PASS Flow (High accuracy)
    pass_dyslexia_games = {
        "phoneme_delete": {"correct": 5, "total": 5, "avg_rt": 800, "questions": [{"text": "q1", "userAnswer": "a", "correctAnswer": "a", "isCorrect": True, "timeSpent": 800, "difficulty": "easy"}]},
        "letter_sound": {"correct": 5, "total": 5, "avg_rt": 750, "questions": [{"text": "q2", "userAnswer": "b", "correctAnswer": "b", "isCorrect": True, "timeSpent": 750, "difficulty": "medium"}]},
        "rhyme_recog": {"correct": 5, "total": 5, "avg_rt": 900, "questions": [{"text": "q3", "userAnswer": "c", "correctAnswer": "c", "isCorrect": True, "timeSpent": 900, "difficulty": "medium"}]},
        "word_scramble": {"correct": 5, "total": 5, "avg_rt": 1100, "questions": [{"text": "q4", "userAnswer": "d", "correctAnswer": "d", "isCorrect": True, "timeSpent": 1100, "difficulty": "hard"}]},
        "lexical_decision": {"correct": 5, "total": 5, "avg_rt": 600, "questions": [{"text": "q5", "userAnswer": "e", "correctAnswer": "e", "isCorrect": True, "timeSpent": 600, "difficulty": "easy"}]},
        "rapid_naming": {"correct": 5, "total": 5, "avg_rt": 500, "questions": [{"text": "q6", "userAnswer": "f", "correctAnswer": "f", "isCorrect": True, "timeSpent": 500, "difficulty": "easy"}]}
    }
    
    r_an_pass = student_session.post(f"{BASE_URL}/api/analyze-dyslexia", json={"games": pass_dyslexia_games})
    print(f"[*] Dyslexia PASS analysis: status={r_an_pass.status_code}")
    assert r_an_pass.status_code == 200, f"Analysis failed: {r_an_pass.text}"
    an_pass_data = r_an_pass.json()
    print(f"    Risk: {an_pass_data.get('risk')}, details.per_task keys: {list(an_pass_data['details']['per_task'].keys())}")
    assert 'phoneme_delete' in an_pass_data['details']['per_task']
    assert an_pass_data['details']['per_task']['phoneme_delete']['acc'] == '100.0%'
    
    # Submit Dyslexia PASS
    r_sub_pass = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 1,
        "student_id": student_id,
        "results": pass_dyslexia_games,
        "status": "completed"
    })
    print(f"[*] Dyslexia PASS submit: status={r_sub_pass.status_code}, data={r_sub_pass.json()}")
    assert r_sub_pass.status_code == 200 and r_sub_pass.json().get('success') is True
    sa_id_pass = r_sub_pass.json().get('student_assessment_id')

    # Dyslexia FAIL Flow (Low accuracy)
    fail_dyslexia_games = {
        "phoneme_delete": {"correct": 0, "total": 5, "avg_rt": 4500, "questions": [{"text": "q1", "userAnswer": "wrong", "correctAnswer": "a", "isCorrect": False, "timeSpent": 4500, "difficulty": "hard"}]},
        "letter_sound": {"correct": 1, "total": 5, "avg_rt": 5000, "questions": [{"text": "q2", "userAnswer": "wrong", "correctAnswer": "b", "isCorrect": False, "timeSpent": 5000, "difficulty": "hard"}]},
        "rhyme_recog": {"correct": 0, "total": 5, "avg_rt": 4800, "questions": [{"text": "q3", "userAnswer": "wrong", "correctAnswer": "c", "isCorrect": False, "timeSpent": 4800, "difficulty": "medium"}]},
        "word_scramble": {"correct": 0, "total": 5, "avg_rt": 6000, "questions": [{"text": "q4", "userAnswer": "wrong", "correctAnswer": "d", "isCorrect": False, "timeSpent": 6000, "difficulty": "hard"}]},
        "lexical_decision": {"correct": 1, "total": 5, "avg_rt": 3500, "questions": [{"text": "q5", "userAnswer": "wrong", "correctAnswer": "e", "isCorrect": False, "timeSpent": 3500, "difficulty": "medium"}]},
        "rapid_naming": {"correct": 0, "total": 5, "avg_rt": 5500, "questions": [{"text": "q6", "userAnswer": "wrong", "correctAnswer": "f", "isCorrect": False, "timeSpent": 5500, "difficulty": "easy"}]}
    }
    r_an_fail = student_session.post(f"{BASE_URL}/api/analyze-dyslexia", json={"games": fail_dyslexia_games})
    print(f"[*] Dyslexia FAIL analysis: status={r_an_fail.status_code}")
    assert r_an_fail.status_code == 200
    an_fail_data = r_an_fail.json()
    print(f"    Risk: {an_fail_data.get('risk')}, warnings count: {len(an_fail_data['details']['warnings'])}")
    assert 'High' in an_fail_data.get('risk')
    
    # Submit Dyslexia FAIL
    r_sub_fail = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 1,
        "student_id": student_id,
        "results": fail_dyslexia_games,
        "status": "completed"
    })
    print(f"[*] Dyslexia FAIL submit: status={r_sub_fail.status_code}, data={r_sub_fail.json()}")
    assert r_sub_fail.status_code == 200
    sa_id_fail = r_sub_fail.json().get('student_assessment_id')

    # Verify Dyslexia Results endpoint
    r_dys_res = student_session.get(f"{BASE_URL}/api/dyslexia-results/1")
    print(f"[*] Dyslexia results API: status={r_dys_res.status_code}")
    assert r_dys_res.status_code == 200
    attempts = r_dys_res.json().get('attempts', [])
    print(f"    Total attempts returned: {len(attempts)}")
    assert len(attempts) >= 2

    # Verify Detailed Results endpoint for FAIL attempt
    r_det_fail = student_session.get(f"{BASE_URL}/api/student-assessment/{sa_id_fail}/results")
    print(f"[*] Detailed Results API for attempt {sa_id_fail}: status={r_det_fail.status_code}")
    assert r_det_fail.status_code == 200
    det_data = r_det_fail.json()
    print(f"    Disorder Type: {det_data['assessment'].get('disorder_type')}")
    assert det_data['assessment'].get('disorder_type') == 'dyslexia'

    # -------------------------------------------------------------
    # 4. DYSCALCULIA ASSESSMENT (ID: 2) - PASS & FAIL FLOWS
    # -------------------------------------------------------------
    print("\n--- Testing Dyscalculia (ID 2) ---")
    
    pass_dyscalc_games = {
        "subitizing": {"correct": 5, "total": 5, "avg_rt": 900, "questions": [{"text": "Count dots", "userAnswer": "4", "correctAnswer": "4", "isCorrect": True, "timeSpent": 900, "difficulty": "easy"}]},
        "comparison": {"correct": 5, "total": 5, "avg_rt": 800, "questions": [{"text": "Which is bigger", "userAnswer": "8", "correctAnswer": "8", "isCorrect": True, "timeSpent": 800, "difficulty": "easy"}]},
        "symbol_match": {"correct": 5, "total": 5, "avg_rt": 950, "questions": [{"text": "Match symbol", "userAnswer": "3", "correctAnswer": "3", "isCorrect": True, "timeSpent": 950, "difficulty": "medium"}]},
        "sequencing": {"correct": 5, "total": 5, "avg_rt": 1100, "questions": [{"text": "Sequence", "userAnswer": "5", "correctAnswer": "5", "isCorrect": True, "timeSpent": 1100, "difficulty": "medium"}]},
        "memory_span": {"correct": 5, "total": 5, "avg_rt": 1200, "questions": [{"text": "Memory", "userAnswer": "123", "correctAnswer": "123", "isCorrect": True, "timeSpent": 1200, "difficulty": "hard"}]},
        "story_arith": {"correct": 5, "total": 5, "avg_rt": 1500, "questions": [{"text": "Word problem", "userAnswer": "7", "correctAnswer": "7", "isCorrect": True, "timeSpent": 1500, "difficulty": "hard"}]}
    }
    r_an_calc_pass = student_session.post(f"{BASE_URL}/api/analyze-dyscalculia", json={"games": pass_dyscalc_games})
    print(f"[*] Dyscalculia PASS analysis: status={r_an_calc_pass.status_code}")
    assert r_an_calc_pass.status_code == 200
    calc_pass_data = r_an_calc_pass.json()
    print(f"    Risk: {calc_pass_data.get('risk')}, per_task: {list(calc_pass_data['details']['per_task'].keys())}")
    assert 'subitizing' in calc_pass_data['details']['per_task']
    assert calc_pass_data['details']['per_task']['subitizing']['acc'] == '100.0%'
    
    r_sub_calc_pass = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 2,
        "student_id": student_id,
        "results": pass_dyscalc_games,
        "status": "completed"
    })
    assert r_sub_calc_pass.status_code == 200
    
    # Dyscalculia FAIL Flow
    fail_dyscalc_games = {
        "subitizing": {"correct": 0, "total": 5, "avg_rt": 5500, "questions": [{"text": "Count dots", "userAnswer": "1", "correctAnswer": "4", "isCorrect": False, "timeSpent": 5500, "difficulty": "easy"}]},
        "comparison": {"correct": 1, "total": 5, "avg_rt": 4800, "questions": [{"text": "Which is bigger", "userAnswer": "2", "correctAnswer": "8", "isCorrect": False, "timeSpent": 4800, "difficulty": "easy"}]},
        "symbol_match": {"correct": 0, "total": 5, "avg_rt": 6000, "questions": [{"text": "Match symbol", "userAnswer": "9", "correctAnswer": "3", "isCorrect": False, "timeSpent": 6000, "difficulty": "medium"}]},
        "sequencing": {"correct": 0, "total": 5, "avg_rt": 5200, "questions": [{"text": "Sequence", "userAnswer": "0", "correctAnswer": "5", "isCorrect": False, "timeSpent": 5200, "difficulty": "medium"}]},
        "memory_span": {"correct": 0, "total": 5, "avg_rt": 7000, "questions": [{"text": "Memory", "userAnswer": "999", "correctAnswer": "123", "isCorrect": False, "timeSpent": 7000, "difficulty": "hard"}]},
        "story_arith": {"correct": 0, "total": 5, "avg_rt": 8000, "questions": [{"text": "Word problem", "userAnswer": "10", "correctAnswer": "7", "isCorrect": False, "timeSpent": 8000, "difficulty": "hard"}]}
    }
    r_an_calc_fail = student_session.post(f"{BASE_URL}/api/analyze-dyscalculia", json={"games": fail_dyscalc_games})
    print(f"[*] Dyscalculia FAIL analysis: status={r_an_calc_fail.status_code}")
    assert r_an_calc_fail.status_code == 200
    calc_fail_data = r_an_calc_fail.json()
    print(f"    Risk: {calc_fail_data.get('risk')}")
    assert 'High' in calc_fail_data.get('risk')
    
    r_sub_calc_fail = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 2,
        "student_id": student_id,
        "results": fail_dyscalc_games,
        "status": "completed"
    })
    assert r_sub_calc_fail.status_code == 200

    # -------------------------------------------------------------
    # 5. DYSGRAPHIA ASSESSMENT (ID: 3) - PASS & FAIL FLOWS
    # -------------------------------------------------------------
    print("\n--- Testing Dysgraphia (ID 3) ---")
    
    pass_dysgraph_games = {
        "trace_line": {"smoothness": 0.95, "duration_ms": 3200, "questions": [{"text": "Trace line", "userAnswer": "done", "correctAnswer": "done", "isCorrect": True, "timeSpent": 3200, "difficulty": "easy"}]},
        "copy_letter": {"smoothness": 0.92, "duration_ms": 4100, "questions": [{"text": "Copy letter A", "userAnswer": "done", "correctAnswer": "done", "isCorrect": True, "timeSpent": 4100, "difficulty": "medium"}]},
        "write_audio": {"smoothness": 0.90, "duration_ms": 3800, "questions": [{"text": "Write word CAT", "userAnswer": "done", "correctAnswer": "done", "isCorrect": True, "timeSpent": 3800, "difficulty": "medium"}]},
        "timed_write": {"smoothness": 0.88, "duration_ms": 5000, "questions": [{"text": "Fast sentence write", "userAnswer": "done", "correctAnswer": "done", "isCorrect": True, "timeSpent": 5000, "difficulty": "hard"}]},
        "shape_draw": {"smoothness": 0.94, "duration_ms": 3000, "questions": [{"text": "Draw triangle", "userAnswer": "done", "correctAnswer": "done", "isCorrect": True, "timeSpent": 3000, "difficulty": "easy"}]}
    }
    r_an_graph_pass = student_session.post(f"{BASE_URL}/api/analyze-dysgraphia", json={"games": pass_dysgraph_games})
    print(f"[*] Dysgraphia PASS analysis: status={r_an_graph_pass.status_code}")
    assert r_an_graph_pass.status_code == 200
    graph_pass_data = r_an_graph_pass.json()
    print(f"    Risk: {graph_pass_data.get('risk')}, per_task keys: {list(graph_pass_data['details']['per_task'].keys())}")
    assert 'trace_line' in graph_pass_data['details']['per_task']
    assert graph_pass_data['details']['per_task']['trace_line']['smoothness'] == '95%'
    
    r_sub_graph_pass = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 3,
        "student_id": student_id,
        "results": pass_dysgraph_games,
        "status": "completed"
    })
    assert r_sub_graph_pass.status_code == 200

    # Dysgraphia FAIL Flow
    fail_dysgraph_games = {
        "trace_line": {"smoothness": 0.15, "duration_ms": 9500, "questions": [{"text": "Trace line", "userAnswer": "err", "correctAnswer": "done", "isCorrect": False, "timeSpent": 9500, "difficulty": "easy"}]},
        "copy_letter": {"smoothness": 0.20, "duration_ms": 11000, "questions": [{"text": "Copy letter A", "userAnswer": "err", "correctAnswer": "done", "isCorrect": False, "timeSpent": 11000, "difficulty": "medium"}]},
        "write_audio": {"smoothness": 0.18, "duration_ms": 12000, "questions": [{"text": "Write word CAT", "userAnswer": "err", "correctAnswer": "done", "isCorrect": False, "timeSpent": 12000, "difficulty": "medium"}]},
        "timed_write": {"smoothness": 0.12, "duration_ms": 14000, "questions": [{"text": "Fast sentence write", "userAnswer": "err", "correctAnswer": "done", "isCorrect": False, "timeSpent": 14000, "difficulty": "hard"}]},
        "shape_draw": {"smoothness": 0.22, "duration_ms": 8500, "questions": [{"text": "Draw triangle", "userAnswer": "err", "correctAnswer": "done", "isCorrect": False, "timeSpent": 8500, "difficulty": "easy"}]}
    }
    r_an_graph_fail = student_session.post(f"{BASE_URL}/api/analyze-dysgraphia", json={"games": fail_dysgraph_games})
    print(f"[*] Dysgraphia FAIL analysis: status={r_an_graph_fail.status_code}")
    assert r_an_graph_fail.status_code == 200
    graph_fail_data = r_an_graph_fail.json()
    print(f"    Risk: {graph_fail_data.get('risk')}")
    assert 'High' in graph_fail_data.get('risk')
    
    r_sub_graph_fail = student_session.post(f"{BASE_URL}/api/submit-assessment", json={
        "assessment_id": 3,
        "student_id": student_id,
        "results": fail_dysgraph_games,
        "status": "completed"
    })
    assert r_sub_graph_fail.status_code == 200

    # -------------------------------------------------------------
    # 6. VERIFY STUDENT PROFILE & DISORDER BREAKDOWN
    # -------------------------------------------------------------
    print("\n--- Verifying Student Profile Breakdown ---")
    r_prof = student_session.get(f"{BASE_URL}/api/student/profile")
    print(f"[*] Student profile API: status={r_prof.status_code}")
    assert r_prof.status_code == 200
    prof_data = r_prof.json()
    print(f"    Total Assessments: {prof_data['statistics']['total_assessments']}")
    print(f"    Average Score: {prof_data['statistics']['average_score']:.1f}%")
    print(f"    Disorders Attempted: {prof_data['statistics']['disorders_attempted']}")
    assert prof_data['statistics']['total_assessments'] >= 6
    
    breakdown = prof_data.get('disorder_breakdown', [])
    print(f"    Disorder Breakdown Items: {json.dumps(breakdown, indent=2)}")
    assert len(breakdown) == 3
    
    for item in breakdown:
        assert item['attempts'] >= 2, f"Expected at least 2 attempts for {item['disorder']}"
        assert item['best_score'] > 0, f"Expected best_score > 0 for {item['disorder']}"

    # -------------------------------------------------------------
    # 7. VERIFY FACULTY DASHBOARD & STUDENTS TAB
    # -------------------------------------------------------------
    print("\n--- Verifying Faculty Dashboard & Students Tab ---")
    r_fac_info = faculty_session.get(f"{BASE_URL}/api/faculty-info")
    print(f"[*] Faculty info: status={r_fac_info.status_code}")
    assert r_fac_info.status_code == 200
    fac_info_data = r_fac_info.json()
    print(f"    Faculty Stats: {fac_info_data['statistics']}")
    assert fac_info_data['statistics']['total_students'] >= 1
    assert fac_info_data['statistics']['total_assessments'] >= 6
    assert fac_info_data['statistics']['completed_assessments'] >= 6
    
    r_fac_stu = faculty_session.get(f"{BASE_URL}/api/get-students")
    print(f"[*] Faculty get-students: status={r_fac_stu.status_code}")
    assert r_fac_stu.status_code == 200
    stu_list = r_fac_stu.json().get('students', [])
    print(f"    Students count: {len(stu_list)}")
    assert len(stu_list) >= 1
    stu_entry = next((s for s in stu_list if s['id'] == student_id), None)
    assert stu_entry is not None, f"Student {student_id} not found in faculty student list"
    print(f"    Found student in faculty class: {stu_entry}")
    assert stu_entry['assessments_completed'] >= 6
    assert stu_entry['average_score'] != '-'

    r_fac_dash = faculty_session.get(f"{BASE_URL}/api/faculty/dashboard")
    print(f"[*] Faculty dashboard API: status={r_fac_dash.status_code}")
    assert r_fac_dash.status_code == 200
    dash_data = r_fac_dash.json()
    print(f"    Faculty Dashboard Total Students: {dash_data.get('stats', {}).get('total_students')}")
    assert dash_data.get('stats', {}).get('total_students') is not None
    assert 'analytics' in dash_data
    assert 'students' in dash_data
    print(f"    Faculty Dashboard Students Count: {len(dash_data.get('students', []))}")
    print(f"    Faculty Dashboard Total Assessments: {dash_data.get('stats', {}).get('total_assessments')}")
    assert dash_data.get('stats', {}).get('total_assessments') >= 6

    print("\n" + "=" * 70)
    print("ALL PASS & FAIL PIPELINE AND DASHBOARD VERIFICATIONS PASSED (100% SUCCESS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
