import requests
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def test_antigravity_ui_and_routes():
    print("=" * 70)
    print("TESTING DOCHUB GOOGLE ANTIGRAVITY PUBLIC-FIRST FLOW")
    print("=" * 70)

    sess = requests.Session()

    # 1. Public Landing Page
    print("\n[1] Testing GET / (Landing Page)...")
    r_home = sess.get(f"{BASE_URL}/")
    assert r_home.status_code == 200, f"Failed: {r_home.status_code}"
    assert "DocHub" in r_home.text
    assert "Understand how students learn." in r_home.text
    assert "antigravity.css" in r_home.text
    assert "hero_cinematic.mp4" in r_home.text
    assert "antigravity_platform_overview.png" in r_home.text
    print("    ✓ Landing page renders Antigravity design, video, and tokens!")

    # 2. Public Static Assets
    print("\n[2] Testing Static Assets from assest/...")
    for asset in [
        "static/videos/hero_cinematic.mp4",
        "static/imgs/antigravity_platform_overview.png",
        "static/imgs/antigravity_dyslexia.png",
        "static/imgs/antigravity_dysgraphia.png",
        "static/imgs/antigravity_dyscalculia.png"
    ]:
        r_asset = sess.get(f"{BASE_URL}/{asset}")
        assert r_asset.status_code == 200, f"Asset failed: {asset}, status: {r_asset.status_code}"
        print(f"    ✓ {asset}: HTTP 200 ({len(r_asset.content)} bytes)")

    # 3. Public-First Assessment Library
    print("\n[3] Testing GET /assessments as Guest...")
    r_assess = sess.get(f"{BASE_URL}/assessments")
    assert r_assess.status_code == 200
    assert "Public Screening Mode" in r_assess.text
    assert "Dyslexia Screening" in r_assess.text
    assert "Dysgraphia Evaluation" in r_assess.text
    assert "Dyscalculia Diagnostic" in r_assess.text
    print("    ✓ /assessments is accessible to guests without login blocks!")

    # 4. Public-First Interactive Tests
    print("\n[4] Testing Direct Assessment Access for Guests (ID 1, 2, 3)...")
    for aid in [1, 2, 3]:
        r_test = sess.get(f"{BASE_URL}/assessment/{aid}", allow_redirects=False)
        assert r_test.status_code == 200, f"Failed for assessment {aid}: status={r_test.status_code}"
        print(f"    ✓ /assessment/{aid}: HTTP 200 (Accessible directly by guest)")

    # 5. Public Results Pages
    print("\n[5] Testing Results Pages for Guests...")
    r_res1 = sess.get(f"{BASE_URL}/dyslexia-results/1", allow_redirects=False)
    assert r_res1.status_code == 200
    r_res2 = sess.get(f"{BASE_URL}/dyscalculia-results/2", allow_redirects=False)
    assert r_res2.status_code == 200
    r_res3 = sess.get(f"{BASE_URL}/dysgraphia-results/3", allow_redirects=False)
    assert r_res3.status_code == 200
    print("    ✓ All 3 results pages render HTTP 200 without login redirect or 401 crash!")

    # 6. Guest Submission API
    print("\n[6] Testing Guest POST /api/submit-assessment...")
    r_guest_sub = sess.post(f"{BASE_URL}/api/submit-assessment", json={
        'assessment_id': 2,
        'results': {
            'subitizing': {'correct': 4, 'total': 5, 'response_times': [600, 650, 700, 620, 680]}
        }
    })
    assert r_guest_sub.status_code == 200
    guest_data = r_guest_sub.json()
    assert guest_data.get('is_guest') == True
    print(f"    ✓ Guest submission evaluated: percentage_score={guest_data.get('percentage_score')}%")

    print("\n" + "=" * 70)
    print("ALL ANTIGRAVITY PUBLIC-FIRST VERIFICATIONS PASSED (100% SUCCESS)")
    print("=" * 70)

if __name__ == '__main__':
    test_antigravity_ui_and_routes()
