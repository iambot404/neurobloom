import sys
sys.path.insert(0, '.')
from app import get_connection

conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT id, name, email, role FROM users WHERE role = %s', ('faculty',))
rows = cursor.fetchall()
cursor.close()
conn.close()

print("Faculty users in database:")
for row in rows:
    print(f"  ID: {row['id']}, Name: {row['name']}, Email: {row['email']}")
