import sys
sys.path.insert(0, '.')
from app import app, get_connection

# Test the faculty info API directly
with app.app_context():
    # Simulate logged in user
    with app.test_client() as client:
        # Login first
        response = client.post('/login/faculty', data={
            'faculty_email': 'testfaculty@neurobloom.com',
            'faculty_password': 'Test@123456'
        }, follow_redirects=False)
        print(f"Login response: {response.status_code}")
        
        # Try to get faculty info
        response = client.get('/api/faculty-info')
        print(f"Faculty Info API response: {response.status_code}")
        print(f"Response data: {response.get_json() if response.status_code != 500 else response.data}")
        
        if response.status_code == 500:
            # Try to debug the error
            import traceback
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id, name, email, class FROM users WHERE email = %s', ('testfaculty@neurobloom.com',))
                user = cursor.fetchone()
                print(f"\nDirect user query result: {user}")
                
                if user:
                    class_name = user['class']
                    print(f"User class: {class_name}")
                    
                    # Test stats query
                    cursor.execute('''
                        SELECT COUNT(DISTINCT u.id) as total_students
                        FROM users u
                        WHERE u.class = %s AND u.role = 'student'
                    ''', (class_name,))
                    stats = cursor.fetchone()
                    print(f"Stats query result: {stats}")
                
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()
