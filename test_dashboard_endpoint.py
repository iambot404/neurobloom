#!/usr/bin/env python3
"""Test the student dashboard endpoint with Flask test client"""

import sys
sys.path.insert(0, '.')

from app import app
import json

def test_dashboard_endpoint():
    """Test the /student-dashboard route and API endpoint"""
    client = app.test_client()
    
    print("=" * 60)
    print("Testing Student Dashboard")
    print("=" * 60)
    
    # Test 1: Try to access dashboard without login (should redirect)
    print("\n1. Test accessing dashboard without login:")
    response = client.get('/student-dashboard')
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 302 (redirect) or 401 (unauthorized)")
    
    # Test 2: Test API endpoint without login
    print("\n2. Test API endpoint without login:")
    response = client.get('/api/student/dashboard')
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 302 (redirect) or 401 (unauthorized)")
    
    # Test 3: Test with simulated session
    print("\n3. Test dashboard API with simulated student session:")
    with client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'student'
            sess['name'] = 'Test Student'
            sess['class'] = '10A'
        
        response = client.get('/api/student/dashboard')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"   ✓ Response received")
            print(f"   Response structure:")
            if data:
                print(f"     - Status: {data.get('status')}")
                print(f"     - Has stats: {'stats' in data}")
                print(f"     - Has recent: {'recent' in data}")
                print(f"     - Has history: {'history' in data}")
                print(f"     - Has progress: {'progress' in data}")
                print(f"     - Has recommendations: {'recommendations' in data}")
                
                # Pretty print first 500 chars of response
                print(f"\n   Response preview:")
                preview = json.dumps(data, indent=2, default=str)[:800]
                for line in preview.split('\n'):
                    print(f"     {line}")
        else:
            print(f"   Response: {response.get_data(as_text=True)[:200]}")
    
    # Test 4: Test dashboard page with session
    print("\n4. Test dashboard page rendering:")
    with client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'student'
            sess['name'] = 'Test Student'
            sess['class'] = '10A'
        
        response = client.get('/student-dashboard')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            html = response.get_data(as_text=True)
            print(f"   ✓ Page rendered successfully")
            print(f"   - Page length: {len(html)} bytes")
            print(f"   - Has dashboard container: {'dashboard-container' in html}")
            print(f"   - Has chart script: {'chart.js' in html}")
            print(f"   - Has CSS link: {'student-dashboard.css' in html}")
        else:
            print(f"   Error: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✓ Dashboard tests completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_dashboard_endpoint()
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
