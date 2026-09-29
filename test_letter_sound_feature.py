import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_assessment_page_render():
    print("[1] Testing /assessment/1 page render & microphone UI...")
    res = requests.get(f"{BASE_URL}/assessment/1")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.text

    # Verify critical microphone & live speech recognition features
    mic_features = [
        "lsm-mic-button",
        "lsm-mic-pulse",
        "lsm-equalizer",
        "lsmSpokenLetter",
        "lsmLiveTranscript",
        "detectSpokenLetter",
        "letterSoundMap",
        "stopSpeechRecognition",
        "Live Speech Detection",
        "Spoken Letter:",
        "ranMicBtn",
        "ranMicPulse",
        "ranEqualizer",
        "ranSpokenLetter",
        "ranLiveTranscript",
        "ran-summary-card",
        "ran-stats-grid",
        "viewFullResultsBtn"
    ]

    for feat in mic_features:
        assert feat in html, f"Missing expected feature in HTML: {feat}"
        print(f"  [OK] Found '{feat}' in dyslexia assessment template")

    print("[OK] Assessment 1 template successfully renders with microphone, live letter display, and rapid naming results scorecard!\n")

def test_api_analyze_and_submit():
    print("[2] Testing /api/analyze-dyslexia with letter_sound results...")
    test_results = {
        'phoneme_delete': {'correct': 5, 'total': 6, 'avg_rt': 1200},
        'letter_sound': {'correct': 6, 'total': 6, 'avg_rt': 950},
        'rhyme_recog': {'correct': 5, 'total': 5, 'avg_rt': 900},
        'word_scramble': {'correct': 5, 'total': 6, 'avg_rt': 1400},
        'lexical_decision': {'correct': 5, 'total': 5, 'avg_rt': 800},
        'rapid_naming': {'correct': 8, 'total': 8, 'avg_rt': 600}
    }

    res = requests.post(f"{BASE_URL}/api/analyze-dyslexia", json={'games': test_results})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    print("  API Response Risk:", data.get('risk'))
    assert 'risk' in data, "Missing 'risk' in analysis output"
    assert 'letter_sound' in data.get('details', {}).get('per_task', {}), "Missing letter_sound in details"
    print("  Letter-Sound task metrics:", data['details']['per_task']['letter_sound'])

    print("\n[3] Testing /api/submit-assessment with letter_sound results...")
    submit_res = requests.post(f"{BASE_URL}/api/submit-assessment", json={
        'assessment_id': 1,
        'student_id': 1,
        'results': test_results,
        'status': 'completed'
    })
    assert submit_res.status_code == 200, f"Submit failed: {submit_res.status_code}"
    submit_data = submit_res.json()
    assert submit_data.get('success') is True, f"Submission unsuccessful: {submit_data}"
    print(f"  [OK] Assessment submitted successfully! Student Assessment ID: {submit_data.get('student_assessment_id')}")

if __name__ == "__main__":
    test_assessment_page_render()
    test_api_analyze_and_submit()
    print("\n[SUCCESS] ALL LETTER-SOUND MATCHING & MICROPHONE TESTS PASSED!")
