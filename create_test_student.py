#!/usr/bin/env python
"""Create or update a test student account"""

from db import get_connection, DBError
from werkzeug.security import generate_password_hash

TEST_EMAIL = 'test@neurobloom.com'
TEST_PASSWORD = 'Test@123456'
TEST_NAME = 'Test Student'
TEST_CONTACT = '9999999999'
TEST_CLASS = '3'
TEST_FACULTY_ID = 21

try:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (TEST_EMAIL,))
    existing = cursor.fetchone()
    
    if existing:
        print(f'Updating existing user: {TEST_EMAIL}')
        hashed = generate_password_hash(TEST_PASSWORD)
        cursor.execute("""
            UPDATE users 
            SET password = %s, name = %s, contact = %s, class = %s, faculty_id = %s
            WHERE email = %s
        """, (hashed, TEST_NAME, TEST_CONTACT, TEST_CLASS, TEST_FACULTY_ID, TEST_EMAIL))
        conn.commit()
        print('✓ User updated successfully')
    else:
        print(f'Creating new user: {TEST_EMAIL}')
        hashed = generate_password_hash(TEST_PASSWORD)
        cursor.execute("""
            INSERT INTO users (name, email, password, contact, role, class, faculty_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (TEST_NAME, TEST_EMAIL, hashed, TEST_CONTACT, 'student', TEST_CLASS, TEST_FACULTY_ID))
        conn.commit()
        print('✓ User created successfully')
    
    cursor.close()
    conn.close()
    
    print(f'\nTest credentials:')
    print(f'  Email: {TEST_EMAIL}')
    print(f'  Password: {TEST_PASSWORD}')
    
except Exception as e:
    print(f'Error: {e}')
