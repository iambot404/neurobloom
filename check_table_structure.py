import sys
sys.path.insert(0, '.')
from app import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute('DESCRIBE student_assessments')
columns = cursor.fetchall()
print("student_assessments columns:")
for col in columns:
    print(f"  {col[0]}: {col[1]}")

cursor.close()
conn.close()
