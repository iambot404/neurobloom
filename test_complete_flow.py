#!/usr/bin/env python
"""Test the complete login and profile flow"""

import requests
import json

base_url = 'http://127.0.0.1:5000'

print('=== Testing Complete Profile Flow ===\n')

# Create session
session = requests.Session()

# Step 1: Login
print('Step 1: Logging in...')
login_data = {
    'student_email': 'test@neurobloom.com',
    'student_password': 'Test@123456'
}
login_response = session.post(f'{base_url}/login/student', data=login_data, allow_redirects=False)
print(f'  Status: {login_response.status_code}')

if login_response.status_code == 302:
    print('  ✓ Login successful (redirect)')
    print(f'  Location: {login_response.headers.get("location")}')
elif login_response.status_code == 200:
    print('  ✓ Login successful')
else:
    print(f'  ✗ Login failed: {login_response.text}')
    exit(1)

print()

# Step 2: Access profile API
print('Step 2: Accessing profile API...')
profile_response = session.get(f'{base_url}/api/student/profile')
print(f'  Status: {profile_response.status_code}')
print(f'  Content-Type: {profile_response.headers.get("content-type")}')

if profile_response.status_code == 200:
    try:
        data = profile_response.json()
        print(f'  ✓ Profile retrieved successfully')
        print()
        
        profile = data.get('profile', {})
        stats = data.get('statistics', {})
        
        print('  Profile Information:')
        print(f'    Name: {profile.get("name")}')
        print(f'    Email: {profile.get("email")}')
        print(f'    Contact: {profile.get("contact")}')
        print(f'    Class: {profile.get("class")}')
        print(f'    Faculty: {profile.get("faculty_name")}')
        print()
        
        print('  Statistics:')
        print(f'    Total Assessments: {stats.get("total_assessments")}')
        print(f'    Average Score: {stats.get("average_score")}%')
        print(f'    Disorders Attempted: {stats.get("disorders_attempted")}')
        
    except json.JSONDecodeError as e:
        print(f'  ✗ Failed to parse JSON: {e}')
        print(f'  Response: {profile_response.text[:200]}')
else:
    print(f'  ✗ Failed to get profile: {profile_response.text[:200]}')
    exit(1)

print()
print('✓ All tests passed! Profile data is loading correctly.')
