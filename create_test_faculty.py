import sys
sys.path.insert(0, '.')
from app import get_connection, generate_password_hash

conn = get_connection()
cursor = conn.cursor()

# Insert or update test faculty account
email = "testfaculty@neurobloom.com"
name = "Test Faculty"
password = "Test@123456"
hashed_password = generate_password_hash(password)

# Delete if exists
cursor.execute('DELETE FROM users WHERE email = %s', (email,))

# Insert new
cursor.execute('''
    INSERT INTO users (name, email, password, role, class)
    VALUES (%s, %s, %s, %s, %s)
''', (name, email, hashed_password, 'faculty', 'Test Class'))

conn.commit()
cursor.close()
conn.close()

print(f"Created faculty account:")
print(f"  Email: {email}")
print(f"  Password: {password}")
print(f"  Name: {name}")
