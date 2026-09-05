#!/usr/bin/env python
"""Test the profile API authentication fix"""

import requests
import json

session = requests.Session()

# Test 1: Try to access profile API without authentication
print('=== Test 1: Profile API without authentication ===')
response = session.get('http://127.0.0.1:5000/api/student/profile')
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type", "N/A")}')
if response.status_code == 401 and 'application/json' in response.headers.get('content-type', ''):
    print('✓ Correct: Returned 401 with JSON')
    try:
        data = response.json()
        print(f'  Message: {data.get("message")}')
    except:
        pass
else:
    print('✗ Wrong: Should return 401 with JSON')
    print(f'Response: {response.text[:200]}')
print()

# Test 2: Login with valid credentials
print('=== Test 2: Login with valid credentials ===')
login_data = {'student_email': 'tejasnarute04@gmail.com', 'student_password': 'password123'}
response = session.post('http://127.0.0.1:5000/login/student', data=login_data, allow_redirects=False)
print(f'Login Status: {response.status_code}')
if response.status_code in [200, 302]:
    print('✓ Login successful')
else:
    print(f'✗ Login failed: {response.text[:200]}')
print()

# Test 3: Try to access profile API after authentication
print('=== Test 3: Profile API after authentication ===')
response = session.get('http://127.0.0.1:5000/api/student/profile')
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type", "N/A")}')
if response.status_code == 200:
    print('✓ Correct: Returned 200')
    try:
        data = response.json()
        print(f'  Status: {data.get("status")}')
        if data.get('status') == 'ok':
            profile = data.get('profile', {})
            print(f'  ✓ Student Name: {profile.get("name")}')
            print(f'  ✓ Email: {profile.get("email")}')
            print(f'  ✓ Contact: {profile.get("contact")}')
            print(f'  ✓ Class: {profile.get("class")}')
            print('  SUCCESS: Profile data displaying correctly!')
    except Exception as e:
        print(f'✗ Error parsing JSON: {e}')
else:
    print(f'✗ Wrong status: {response.status_code}')
    print(f'Response: {response.text[:200]}')
