#!/usr/bin/env python
"""Test the SQL query directly"""

from db import get_connection, DBError

conn = get_connection()
cursor = conn.cursor(dictionary=True)

user_id = 2  # Test student

# Test the disorder breakdown query
print('Testing disorder breakdown query...')
try:
    cursor.execute('''
        SELECT 
            at.disorder_type,
            COUNT(*) as attempts,
            AVG(sa.percentage_score) as average_score,
            MAX(sa.percentage_score) as best_score,
            MIN(sa.percentage_score) as lowest_score
        FROM student_assessments sa
        JOIN assessment_types at ON sa.assessment_id = at.id
        WHERE sa.student_id = %s
        GROUP BY at.disorder_type
    ''', (user_id,))
    
    results = cursor.fetchall()
    print(f'Query succeeded. Results: {results}')
except Exception as e:
    print(f'Query failed: {e}')

cursor.close()
conn.close()
