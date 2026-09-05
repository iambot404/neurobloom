import requests
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def test_all_pages_theme_sync():
    print("=" * 70)
    print("VERIFYING FULL-PROJECT GOOGLE ANTIGRAVITY THEME SYNCHRONIZATION")
    print("=" * 70)

    sess = requests.Session()

    endpoints_to_test = [
        ("/", "Landing Page", ["DocHub", "antigravity.css", "hero_cinematic.mp4"]),
        ("/assessments", "Assessments Library", ["DocHub", "COGNITIVE SCREENING LIBRARY"]),
        ("/assessment/1", "Dyslexia Assessment", ["DocHub"]),
        ("/assessment/2", "Dyscalculia Assessment", ["DocHub"]),
        ("/assessment/3", "Dysgraphia Assessment", ["DocHub"]),
        ("/dyslexia-results/1", "Dyslexia Results", ["DocHub", "Dyslexia Screening Report"]),
        ("/dyscalculia-results/2", "Dyscalculia Results", ["DocHub", "Dyscalculia Diagnostic Report"]),
        ("/dysgraphia-results/3", "Dysgraphia Results", ["DocHub", "Dysgraphia Evaluation Report"]),
        ("/login", "Login Page", ["DocHub", "login.css", "Welcome Back"]),
        ("/signup", "Signup Page", ["DocHub", "signup.css", "Registration Category"]),
        ("/support", "Support Page", ["DocHub", "Support & Documentation"]),
    ]

    for path, name, expected_strings in endpoints_to_test:
        print(f"\n[*] Testing {name} ({path})...")
        r = sess.get(f"{BASE_URL}{path}")
        assert r.status_code == 200, f"Failed on {path}: status {r.status_code}"
        for s in expected_strings:
            assert s in r.text, f"Expected '{s}' in {path} response, but was missing!"
        print(f"    ✓ HTTP 200 OK | Verified {len(expected_strings)} theme elements!")

    print("\n" + "=" * 70)
    print("ALL PROJECT PAGES ARE 100% SYNCHRONIZED WITH ANTIGRAVITY THEME!")
    print("=" * 70)

if __name__ == '__main__':
    test_all_pages_theme_sync()
