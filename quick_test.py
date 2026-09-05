#!/usr/bin/env python
"""Quick test of the profile API after the fix"""

import requests

session = requests.Session()

# Login
print('Logging in...')
login_data = {
    'student_email': 'test@neurobloom.com',
    'student_password': 'Test@123456'
}
login_response = session.post('http://127.0.0.1:5000/login/student', data=login_data)
print(f'Login status: {login_response.status_code}')

# Get profile
print('\nFetching profile...')
profile_response = session.get('http://127.0.0.1:5000/api/student/profile')
print(f'Profile status: {profile_response.status_code}')

if profile_response.status_code == 200:
    data = profile_response.json()
    if data.get('status') == 'ok':
        profile = data.get('profile', {})
        print('\n✓ SUCCESS! Profile data retrieved:')
        print(f'  Name: {profile.get("name")}')
        print(f'  Email: {profile.get("email")}')
        print(f'  Contact: {profile.get("contact")}')
        print(f'  Class: {profile.get("class")}')
        print(f'  Faculty: {profile.get("faculty_name")}')
    else:
        print(f'✗ Error: {data.get("error")}')
else:
    print(f'✗ Status {profile_response.status_code}: {profile_response.text[:200]}')
