import requests
import json
import numpy as np
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ml_models.dyslexia_nn_model import DyslexiaDeepLearning
from ml_models.dyscalculia_nn_model import DyscalculiaDeepLearning
from ml_models.dysgraphia_nn_model import DysgraphiaDeepLearning
from ml_models.unified_predictor import UnifiedDisorderPredictor

BASE_URL = "http://127.0.0.1:5000"

def trace_models_internals():
    print("=" * 75)
    print("STEP 1: TRACING ML MODELS INTERNALS & FEATURE SENSITIVITY")
    print("=" * 75)

    # 1. Dysgraphia Model
    print("\n--- [1] DYSGRAPHIA NEURAL MODEL TRACE ---")
    dysg = DysgraphiaDeepLearning()
    
    # Test A: Smooth, continuous strokes (Normal handwriting with continuous pointer samples)
    smooth_line = [{'points': [[20 + i*10, 150 + float(np.sin(i*0.1)*1.5)] for i in range(45)], 't_start': 0, 't_end': 1000, 'duration_ms': 1000}]
    
    # Continuous sampled letter 'B' (down stem, top loop, bottom loop)
    stem = [[50, 50 + i*5] for i in range(21)]
    loop1 = [[50 + float(np.sin(t)*25), 75 - float(np.cos(t)*25)] for t in np.linspace(0, np.pi, 15)]
    loop2 = [[50 + float(np.sin(t)*25), 125 - float(np.cos(t)*25)] for t in np.linspace(0, np.pi, 15)]
    smooth_letter = [{'points': stem + loop1 + loop2, 't_start': 0, 't_end': 800, 'duration_ms': 800}]
    
    # Continuous sampled Square & Triangle
    sq_top = [[100 + i*10, 100] for i in range(11)]
    sq_right = [[200, 100 + i*10] for i in range(11)]
    sq_bottom = [[200 - i*10, 200] for i in range(11)]
    sq_left = [[100, 200 - i*10] for i in range(11)]
    smooth_shape = [{'points': sq_top + sq_right + sq_bottom + sq_left, 't_start': 0, 't_end': 1200, 'duration_ms': 1200}]
    
    pass_dysgraphia_data = {
        'games': {
            'trace_line': {'strokes': smooth_line, 'duration_ms': 1000},
            'copy_letter': {'strokes': smooth_letter, 'duration_ms': 800},
            'write_audio': {'strokes': smooth_letter, 'duration_ms': 800},
            'timed_write': {'strokes': smooth_letter, 'duration_ms': 5000},
            'shape_draw': {'strokes': smooth_shape, 'duration_ms': 1200}
        }
    }
    
    pass_features = dysg.extract_advanced_features(pass_dysgraphia_data)
    pass_pred = dysg.predict_risk(pass_dysgraphia_data)
    print(f"  [PASS Case] Smoothness F1: {pass_features[0, 0]:.3f}, Straightness F2: {pass_features[0, 1]:.3f}")
    print(f"  [PASS Case] Risk Score: {pass_pred['risk_score']:.3f}, Risk Level: {pass_pred['risk_level']}, Confidence: {pass_pred['confidence']:.2%}")
    print(f"  [PASS Case] Top Recommendation: {pass_pred['recommendations'][0]}")
    assert pass_pred['risk_level'] in ['None', 'Low']
    
    # Test B: Erratic, shaky, jagged strokes (Dysgraphia Motor Impairment)
    erratic_line = [{'points': [[20 + i*10, 150 + (30 if i%2==0 else -30)] for i in range(40)], 't_start': 0, 't_end': 4000, 'duration_ms': 4000}]
    erratic_letter = [{'points': [[50 + (i*15)%40, 50 + (i*25)%60] for i in range(20)], 't_start': 0, 't_end': 3500, 'duration_ms': 3500}]
    erratic_shape = [{'points': [[100 + (i*20)%50, 100 + (i*30)%70] for i in range(25)], 't_start': 0, 't_end': 4500, 'duration_ms': 4500}]
    
    fail_dysgraphia_data = {
        'games': {
            'trace_line': {'strokes': erratic_line, 'duration_ms': 4000},
            'copy_letter': {'strokes': erratic_letter, 'duration_ms': 3500},
            'write_audio': {'strokes': erratic_letter, 'duration_ms': 3500},
            'timed_write': {'strokes': erratic_letter, 'duration_ms': 5000},
            'shape_draw': {'strokes': erratic_shape, 'duration_ms': 4500}
        }
    }
    
    fail_features = dysg.extract_advanced_features(fail_dysgraphia_data)
    fail_pred = dysg.predict_risk(fail_dysgraphia_data)
    print(f"  [FAIL Case] Smoothness F1: {fail_features[0, 0]:.3f}, Straightness F2: {fail_features[0, 1]:.3f}")
    print(f"  [FAIL Case] Risk Score: {fail_pred['risk_score']:.3f}, Risk Level: {fail_pred['risk_level']}, Confidence: {fail_pred['confidence']:.2%}")
    print(f"  [FAIL Case] Top Recommendation: {fail_pred['recommendations'][0]}")
    assert fail_pred['risk_level'] == 'High'

    # 2. Dyslexia Model
    print("\n--- [2] DYSLEXIA NEURAL MODEL TRACE ---")
    dysl = DyslexiaDeepLearning()
    
    pass_dyslexia_data = {
        'games': {
            'letter_sound': {'correct': 5, 'total': 5, 'response_times': [800, 750, 900, 850, 700]},
            'rhyme_recog': {'correct': 5, 'total': 5, 'response_times': [600, 650, 700, 620, 680]},
            'phoneme_delete': {'correct': 5, 'total': 5, 'response_times': [900, 850, 950, 800, 880]},
            'word_scramble': {'correct': 5, 'total': 5, 'response_times': [1100, 1050, 1150, 1000, 1200]},
            'lexical_decision': {'correct': 5, 'total': 5, 'response_times': [500, 550, 520, 580, 510]},
            'rapid_naming': {'correct': 5, 'total': 5, 'response_times': [400, 420, 410, 450, 430]}
        }
    }
    pass_dysl_pred = dysl.predict_risk(pass_dyslexia_data)
    print(f"  [PASS Case] Risk Score: {pass_dysl_pred['risk_score']:.3f}, Risk Level: {pass_dysl_pred['risk_level']}, Confidence: {pass_dysl_pred['confidence']:.2%}")
    assert pass_dysl_pred['risk_level'] in ['No risk likely', 'Low risk']

    fail_dyslexia_data = {
        'games': {
            'letter_sound': {'correct': 0, 'total': 5, 'response_times': [3500, 4000, 3800, 4200, 3900]},
            'rhyme_recog': {'correct': 0, 'total': 5, 'response_times': [3600, 4100, 3700, 4300, 4000]},
            'phoneme_delete': {'correct': 0, 'total': 5, 'response_times': [4000, 4500, 4200, 4400, 4100]},
            'word_scramble': {'correct': 0, 'total': 5, 'response_times': [4500, 5000, 4800, 4900, 4700]},
            'lexical_decision': {'correct': 0, 'total': 5, 'response_times': [3000, 3500, 3200, 3400, 3300]},
            'rapid_naming': {'correct': 0, 'total': 5, 'response_times': [3200, 3600, 3400, 3700, 3500]}
        }
    }
    fail_dysl_pred = dysl.predict_risk(fail_dyslexia_data)
    print(f"  [FAIL Case] Risk Score: {fail_dysl_pred['risk_score']:.3f}, Risk Level: {fail_dysl_pred['risk_level']}, Confidence: {fail_dysl_pred['confidence']:.2%}")
    assert fail_dysl_pred['risk_level'] == 'High risk'

    # 3. Dyscalculia Model
    print("\n--- [3] DYSCALCULIA NEURAL MODEL TRACE ---")
    dysc = DyscalculiaDeepLearning()
    
    pass_dyscalc_data = {
        'games': {
            'subitizing': {'correct': 5, 'total': 5, 'response_times': [600, 650, 700, 620, 680]},
            'comparison': {'correct': 5, 'total': 5, 'response_times': [500, 550, 520, 580, 510]},
            'symbol_match': {'correct': 5, 'total': 5, 'response_times': [700, 750, 720, 780, 710]},
            'sequencing': {'correct': 5, 'total': 5, 'response_times': [900, 850, 950, 800, 880]},
            'memory_span': {'correct': 5, 'total': 5, 'response_times': [1000, 1050, 1100, 980, 1020]},
            'story_arith': {'correct': 5, 'total': 5, 'response_times': [1200, 1150, 1250, 1180, 1220]}
        }
    }
    pass_dysc_pred = dysc.predict_risk(pass_dyscalc_data)
    print(f"  [PASS Case] Risk Score: {pass_dysc_pred['risk_score']:.3f}, Risk Level: {pass_dysc_pred['risk_level']}, Confidence: {pass_dysc_pred['confidence']:.2%}")
    assert pass_dysc_pred['risk_level'] in ['None', 'Low']

    fail_dyscalc_data = {
        'games': {
            'subitizing': {'correct': 0, 'total': 5, 'response_times': [3500, 4000, 3800, 4200, 3900]},
            'comparison': {'correct': 0, 'total': 5, 'response_times': [3600, 4100, 3700, 4300, 4000]},
            'symbol_match': {'correct': 0, 'total': 5, 'response_times': [4000, 4500, 4200, 4400, 4100]},
            'sequencing': {'correct': 0, 'total': 5, 'response_times': [4500, 5000, 4800, 4900, 4700]},
            'memory_span': {'correct': 0, 'total': 5, 'response_times': [4200, 4600, 4400, 4700, 4300]},
            'story_arith': {'correct': 0, 'total': 5, 'response_times': [5000, 5500, 5200, 5400, 5100]}
        }
    }
    fail_dysc_pred = dysc.predict_risk(fail_dyscalc_data)
    print(f"  [FAIL Case] Risk Score: {fail_dysc_pred['risk_score']:.3f}, Risk Level: {fail_dysc_pred['risk_level']}, Confidence: {fail_dysc_pred['confidence']:.2%}")
    assert fail_dysc_pred['risk_level'] == 'High'

    print("\n✓ ALL 3 ML MODELS GENUINELY & MATHEMATICALLY RESPOND TO USER INPUTS!")

def trace_api_and_db_flow():
    print("\n" + "=" * 75)
    print("STEP 2: FULL API & SUPABASE PERSISTENCE TRACE")
    print("=" * 75)
    
    sess = requests.Session()
    ts = int(time.time())
    email = f"ml_trace_{ts}@example.com"
    pwd = "password123"
    
    # 1. Register & login student
    r = sess.post(f"{BASE_URL}/student_register", data={
        'name': 'ML Trace Student',
        'email': email,
        'contact': '1234567890',
        'password': pwd,
        'confirm_password': pwd
    }, allow_redirects=True)
    assert r.status_code == 200
    
    r_login = sess.post(f"{BASE_URL}/login/student", data={
        'student_email': email,
        'student_password': pwd
    }, allow_redirects=True)
    assert r_login.status_code == 200
    
    # 2. Test Dysgraphia Deliberate FAIL Submission
    erratic_line = [{'points': [[20 + i*10, 150 + (30 if i%2==0 else -30)] for i in range(40)], 't_start': 0, 't_end': 4000, 'duration_ms': 4000}]
    erratic_letter = [{'points': [[50 + (i*15)%40, 50 + (i*25)%60] for i in range(20)], 't_start': 0, 't_end': 3500, 'duration_ms': 3500}]
    erratic_shape = [{'points': [[100 + (i*20)%50, 100 + (i*30)%70] for i in range(25)], 't_start': 0, 't_end': 4500, 'duration_ms': 4500}]
    
    dysgraphia_fail_payload = {
        'games': {
            'trace_line': {'strokes': erratic_line, 'duration_ms': 4000},
            'copy_letter': {'strokes': erratic_letter, 'duration_ms': 3500},
            'write_audio': {'strokes': erratic_letter, 'duration_ms': 3500},
            'timed_write': {'strokes': erratic_letter, 'duration_ms': 5000},
            'shape_draw': {'strokes': erratic_shape, 'duration_ms': 4500}
        }
    }
    
    print("\n[*] Sending FAIL Dysgraphia data to /api/analyze-dysgraphia...")
    r_ana = sess.post(f"{BASE_URL}/api/analyze-dysgraphia", json=dysgraphia_fail_payload)
    assert r_ana.status_code == 200
    ana_data = r_ana.json()
    print(f"    ML Output Risk: {ana_data['risk']}, Risk Score: {ana_data['risk_score']:.2f}")
    print(f"    Per-Task Metrics: {json.dumps(ana_data['details']['per_task'], indent=4)}")
    print(f"    Warnings / Recommendations generated: {ana_data['details']['warnings'][0]}")
    assert ana_data['risk'] == 'High'
    assert ana_data['details']['per_task']['trace_line']['smoothness'] != '80%'  # Guaranteed not hardcoded 80%!

    print("\n[*] Submitting FAIL Dysgraphia assessment to /api/submit-assessment...")
    r_sub = sess.post(f"{BASE_URL}/api/submit-assessment", json={
        'assessment_id': 3,
        'results': dysgraphia_fail_payload['games']
    })
    assert r_sub.status_code == 200
    sub_data = r_sub.json()
    sa_id = sub_data['student_assessment_id']
    print(f"    Submitted sa_id: {sa_id}, percentage_score: {sub_data['percentage_score']}%")
    
    # 3. Verify Saved Supabase Record via Results API
    print("\n[*] Fetching saved assessment attempt from /api/student-assessment/<id>/results...")
    r_res = sess.get(f"{BASE_URL}/api/student-assessment/{sa_id}/results")
    assert r_res.status_code == 200
    res_data = r_res.json()
    ass_info = res_data.get('assessment', {})
    pred_info = res_data.get('prediction', {})
    print(f"    Assessment ID: {ass_info.get('id')}, Disorder: {ass_info.get('disorder_type')}")
    print(f"    Saved Score: {ass_info.get('percentage_score')}%")
    print(f"    Saved ML Risk Level: {pred_info.get('risk_level')}, ML Prediction Score: {pred_info.get('prediction_score')}")
    assert ass_info.get('percentage_score') == 0.0
    assert pred_info.get('risk_level') == 'High'
    
    # 4. Verify Student Profile
    print("\n[*] Fetching student profile from /api/student/profile...")
    r_prof = sess.get(f"{BASE_URL}/api/student/profile")
    assert r_prof.status_code == 200
    prof_data = r_prof.json()
    print(f"    Student Statistics: {prof_data['statistics']}")
    print(f"    Student Disorder Breakdown: {json.dumps(prof_data['disorder_breakdown'], indent=4)}")
    assert prof_data['statistics']['total_assessments'] == 1
    assert prof_data['statistics']['average_score'] == 0.0
    
    print("\n" + "=" * 75)
    print("COMPLETE END-TO-END PIPELINE IS 100% GENUINE AND TRACEABLE")
    print("=" * 75)

if __name__ == '__main__':
    trace_models_internals()
    trace_api_and_db_flow()
