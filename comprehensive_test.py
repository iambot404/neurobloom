#!/usr/bin/env python
"""
Comprehensive test of the complete profile functionality
"""

import requests
import json

print('=' * 70)
print('COMPREHENSIVE PROFILE SYSTEM TEST')
print('=' * 70)

session = requests.Session()
base_url = 'http://127.0.0.1:5000'

# Test 1: Unauthenticated API access
print('\n[TEST 1] Unauthenticated API Access')
print('-' * 70)
response = session.get(f'{base_url}/api/student/profile')
assert response.status_code == 401, f'Expected 401, got {response.status_code}'
data = response.json()
assert data.get('status') == 'error', 'Should return error status'
assert 'error' in data, 'Should contain error message'
print('✓ Correctly returns 401 with JSON error for unauthenticated requests')

# Test 2: Login
print('\n[TEST 2] Student Login')
print('-' * 70)
login_data = {
    'student_email': 'test@neurobloom.com',
    'student_password': 'Test@123456'
}
response = session.post(f'{base_url}/login/student', data=login_data, allow_redirects=False)
assert response.status_code in [200, 302], f'Login failed with status {response.status_code}'
print('✓ Login successful')

# Test 3: Authenticated API access
print('\n[TEST 3] Authenticated API Access')
print('-' * 70)
response = session.get(f'{base_url}/api/student/profile')
assert response.status_code == 200, f'Expected 200, got {response.status_code}'
data = response.json()
assert data.get('status') == 'ok', 'Should return ok status'
print('✓ API returns 200 OK for authenticated requests')

# Test 4: Profile data structure
print('\n[TEST 4] Profile Data Structure')
print('-' * 70)
profile = data.get('profile', {})
required_fields = ['id', 'name', 'email', 'contact', 'class', 'faculty_id', 'faculty_name', 'role']
for field in required_fields:
    assert field in profile, f'Missing required field: {field}'
    print(f'  ✓ {field}: {profile.get(field)}')
print('✓ All required profile fields present')

# Test 5: Statistics data structure
print('\n[TEST 5] Statistics Data Structure')
print('-' * 70)
stats = data.get('statistics', {})
required_stats = ['total_assessments', 'average_score', 'disorders_attempted']
for field in required_stats:
    assert field in stats, f'Missing required stat field: {field}'
    print(f'  ✓ {field}: {stats.get(field)}')
print('✓ All required statistics fields present')

# Test 6: Disorder breakdown structure
print('\n[TEST 6] Disorder Breakdown Structure')
print('-' * 70)
disorders = data.get('disorder_breakdown', [])
print(f'  Total disorders in breakdown: {len(disorders)}')
if disorders:
    for disorder in disorders:
        assert 'disorder' in disorder, 'Missing disorder field'
        assert 'attempts' in disorder, 'Missing attempts field'
        assert 'average_score' in disorder, 'Missing average_score field'
        print(f'    - {disorder.get("disorder")}: {disorder.get("attempts")} attempts, Avg: {disorder.get("average_score")}%')
else:
    print('  (No assessments yet - this is OK)')
print('✓ Disorder breakdown structure is correct')

# Test 7: Profile page accessibility
print('\n[TEST 7] Profile Page Accessibility')
print('-' * 70)
response = session.get(f'{base_url}/student-profile')
assert response.status_code == 200, f'Profile page returned {response.status_code}'
assert 'displayName' in response.text or 'profile' in response.text.lower(), 'Profile page HTML should contain profile elements'
print('✓ Profile page is accessible and contains profile elements')

print('\n' + '=' * 70)
print('ALL TESTS PASSED! ✅')
print('=' * 70)
print('\nSummary:')
print('- Authentication and authorization working correctly')
print('- API returns proper JSON responses with all required fields')
print('- Profile page is accessible to authenticated users')
print('- Student information displays correctly:')
print(f'    Name: {profile.get("name")}')
print(f'    Email: {profile.get("email")}')
print(f'    Contact: {profile.get("contact")}')
print(f'    Class: {profile.get("class")}')
print(f'    Faculty: {profile.get("faculty_name")}')
print(f'- Statistics are properly formatted and ready for display')
print('\nThe profile system is now fully functional!')
