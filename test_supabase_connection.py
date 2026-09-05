import os
import sys
from dotenv import load_dotenv

load_dotenv()

from db import get_connection, get_db_connection, get_supabase_client

print("1. Testing Supabase Client Initialization...")
client = get_supabase_client()
if client:
    print("   [OK] Supabase client initialized successfully")
else:
    print("   [ERROR] Supabase client failed to initialize")

print("\n2. Testing get_connection() and SELECT from assessment_types...")
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT id, name, disorder_type FROM assessment_types ORDER BY id")
rows = cur.fetchall()
print(f"   [OK] Fetched {len(rows)} assessment types:")
for r in rows:
    print(f"      - ID={r['id']}: {r['name']} ({r['disorder_type']})")
cur.close()
conn.close()

print("\n3. Testing SELECT from questions & answer_options...")
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT id, question_text, question_type FROM questions WHERE assessment_id = %s LIMIT 3", (1,))
questions = cur.fetchall()
print(f"   [OK] Fetched {len(questions)} sample questions for assessment 1:")
for q in questions:
    print(f"      - Q{q['id']}: {q['question_text'][:50]}... ({q['question_type']})")
cur.close()
conn.close()

print("\n4. Testing SELECT users...")
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT id, name, email, role FROM users LIMIT 5")
users = cur.fetchall()
print(f"   [OK] Fetched {len(users)} users:")
for u in users:
    print(f"      - User #{u['id']}: {u['name']} <{u['email']}> ({u['role']})")
cur.close()
conn.close()

print("\n5. Testing DB version query...")
conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT VERSION()")
v = cur.fetchone()
print(f"   [OK] Database Version response: {v}")
cur.close()
conn.close()

print("\n[SUCCESS] All core database checks passed!")
