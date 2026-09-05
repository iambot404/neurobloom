#!/usr/bin/env python
"""Check password for test user"""

from db import get_connection, DBError

try:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, password FROM users WHERE email='tejasnarute04@gmail.com' LIMIT 1")
    user = cursor.fetchone()
    if user:
        print('User found:')
        print(f'  ID: {user["id"]}')
        print(f'  Name: {user["name"]}')
        print(f'  Email: {user["email"]}')
        print(f'  Password: {user["password"]}')
    else:
        print('User not found')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'Error: {e}')
