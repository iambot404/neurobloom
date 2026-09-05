#!/usr/bin/env python
"""Test the new login redirect to profile page"""

import requests

session = requests.Session()

print('Testing new login redirect...\n')

# Login
login_data = {
    'student_email': 'test@neurobloom.com',
    'student_password': 'Test@123456'
}

response = session.post(
    'http://127.0.0.1:5000/login/student', 
    data=login_data,
    allow_redirects=False  # Don't follow redirect so we can see where it goes
)

print(f'Login Status: {response.status_code}')
if response.status_code == 302:
    redirect_location = response.headers.get('Location')
    print(f'Redirect Location: {redirect_location}')
    
    if '/student-profile' in redirect_location:
        print('✓ Correctly redirects to /student-profile')
    elif '/student' in redirect_location:
        print('✗ Still redirects to old student page')
    else:
        print(f'? Redirects to: {redirect_location}')
else:
    print(f'Response: {response.text[:100]}')
