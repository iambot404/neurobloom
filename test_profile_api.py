import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Create a session
session = requests.Session()

# Test login first
login_data = {
    'email': 'tejasnarute04@gmail.com',
    'password': 'password123'
}

print("Step 1: Logging in as student...")
response = session.post('http://127.0.0.1:5000/login/student', data=login_data)
print(f"Login response status: {response.status_code}")
print(f"Login response: {response.text[:200]}")

# Now try to get the profile
print("\nStep 2: Fetching profile...")
profile_response = session.get('http://127.0.0.1:5000/api/student/profile')
print(f"Profile response status: {profile_response.status_code}")

if profile_response.status_code == 200:
    try:
        data = profile_response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Response content: {profile_response.text}")
else:
    print(f"Error: {profile_response.text}")
