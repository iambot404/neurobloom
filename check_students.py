from db import get_connection, DBError

try:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check students
    cursor.execute("SELECT id, name, email, contact, class, faculty_id FROM users WHERE role = 'student' LIMIT 5")
    students = cursor.fetchall()
    
    print("=== STUDENTS IN DATABASE ===")
    for s in students:
        print(f"ID: {s['id']}")
        print(f"  Name: {s['name']}")
        print(f"  Email: {s['email']}")
        print(f"  Contact: {s.get('contact')}")
        print(f"  Class: {s.get('class')}")
        print(f"  Faculty ID: {s.get('faculty_id')}")
        print()
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
