#!/usr/bin/env python
"""Test the API directly without authentication to see what it returns"""

import requests
import json

base_url = 'http://127.0.0.1:5000'

# Test the API endpoint
print('=== Testing /api/student/profile endpoint ===\n')

# Test 1: Without authentication
print('1. Without authentication:')
response = requests.get(f'{base_url}/api/student/profile')
print(f'   Status: {response.status_code}')
print(f'   Content-Type: {response.headers.get("content-type")}')
print(f'   Body: {response.text[:300]}\n')

# Test 2: With session (simulate login)
print('2. Simulating student login and accessing API...')
session = requests.Session()

# First login
login_data = {
    'student_email': 'tejasnarute04@gmail.com',
    'student_password': 'password123'
}
print(f'   Attempting login with email: {login_data["student_email"]}')
login_response = session.post(f'{base_url}/login/student', data=login_data)
print(f'   Login response status: {login_response.status_code}')

# Now try to access API
print('   Attempting to access /api/student/profile with session...')
profile_response = session.get(f'{base_url}/api/student/profile')
print(f'   Profile response status: {profile_response.status_code}')
print(f'   Content-Type: {profile_response.headers.get("content-type")}')
print(f'   Body preview: {profile_response.text[:500]}\n')

if profile_response.status_code == 200:
    try:
        data = profile_response.json()
        print('✓ Successfully parsed JSON response')
        print(f'   Status: {data.get("status")}')
        if 'profile' in data:
            print(f'   Student Name: {data["profile"].get("name")}')
            print(f'   Email: {data["profile"].get("email")}')
            print(f'   Class: {data["profile"].get("class")}')
            print(f'   Contact: {data["profile"].get("contact")}')
    except json.JSONDecodeError as e:
        print(f'✗ Failed to parse JSON: {e}')
        print(f'   Raw response: {profile_response.text[:500]}')
