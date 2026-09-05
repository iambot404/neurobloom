"""
Test script to verify all frontend pages and API responses on live Flask application.
"""
import requests

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

print("==================================================")
print("     LIVE FLASK & FRONTEND ROUTE VERIFICATION    ")
print("==================================================")

# 1. Homepage
r = session.get(f"{BASE_URL}/")
assert r.status_code == 200, f"Homepage failed with {r.status_code}"
assert "NeuroBloom" in r.text or "neurobloom" in r.text.lower(), "Brand not in homepage"
print("[PASS] Homepage rendered successfully (HTTP 200)")

# 2. Database test endpoint
r = session.get(f"{BASE_URL}/db-test")
assert r.status_code == 200, f"db-test failed with {r.status_code}"
data = r.json()
assert data.get('status') == 'ok', f"Unexpected db-test response: {data}"
print(f"[PASS] /db-test endpoint responded: {data}")

# 3. Student Login Action
login_payload = {
    'student_email': 'test@neurobloom.com',
    'student_password': 'Test@123456'
}
r = session.post(f"{BASE_URL}/login/student", data=login_payload, allow_redirects=True)
assert r.status_code == 200, f"Student login failed with {r.status_code}"
print("[PASS] Student login successful and session established")

# 4. Student Dashboard Page
r = session.get(f"{BASE_URL}/student-dashboard")
assert r.status_code == 200, f"Student dashboard failed with {r.status_code}"
print("[PASS] Student dashboard page loaded (HTTP 200)")

# 5. Student Profile Page
r = session.get(f"{BASE_URL}/student-profile")
assert r.status_code == 200, f"Student profile failed with {r.status_code}"
print("[PASS] Student profile page loaded (HTTP 200)")

# 6. Student Stats API
r = session.get(f"{BASE_URL}/api/student-stats")
assert r.status_code == 200, f"Student stats API failed with {r.status_code}"
print(f"[PASS] Student stats API returned: {r.json().get('total_assessments')} assessments")

# 7. Available Assessments API
r = session.get(f"{BASE_URL}/api/assessments/available")
assert r.status_code == 200, f"Available assessments failed with {r.status_code}"
assessments = r.json().get('assessments', [])
print(f"[PASS] Available assessments returned {len(assessments)} tests")

# 8. Assessment Test Page
r = session.get(f"{BASE_URL}/assessment/1")
assert r.status_code == 200, f"Assessment 1 page failed with {r.status_code}"
print("[PASS] Assessment test page rendered successfully (HTTP 200)")

print("\n==================================================")
print("   ALL LIVE HTTP & FRONTEND ROUTES VERIFIED!     ")
print("==================================================")
