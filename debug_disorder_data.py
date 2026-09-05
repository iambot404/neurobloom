from db import get_connection, DBError

conn = get_connection()
cursor = conn.cursor(dictionary=True)

# Get first student
cursor.execute("SELECT id, name FROM users WHERE role = 'student' LIMIT 1")
student = cursor.fetchone()

if student:
    student_id = student['id']
    print(f'Student: {student["name"]} (ID: {student_id})')
    
    # Get RECENT assessments (like the API does)
    print('\n=== RECENT (LIMIT 5) ===')
    cursor.execute('''
        SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
               sa.created_at as date, sa.status
        FROM student_assessments sa
        JOIN assessment_types at ON sa.assessment_id = at.id
        WHERE sa.student_id = %s
        ORDER BY sa.created_at DESC
        LIMIT 5
    ''', (student_id,))
    
    recent = cursor.fetchall()
    print(f'Recent Assessments: {len(recent)}')
    dyslexia_count = 0
    for a in recent:
        print(f'  - {a["disorder_type"]}: score={a["score"]}')
        if a["disorder_type"].lower() == 'dyslexia':
            dyslexia_count += 1
    print(f'Dyslexia in Recent: {dyslexia_count}')
    
    # Get ALL assessments (like history)
    print('\n=== ALL HISTORY ===')
    cursor.execute('''
        SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
               sa.created_at as date, sa.status
        FROM student_assessments sa
        JOIN assessment_types at ON sa.assessment_id = at.id
        WHERE sa.student_id = %s
        ORDER BY sa.created_at DESC
    ''', (student_id,))
    
    history = cursor.fetchall()
    print(f'All Assessments: {len(history)}')
    dyslexia_in_history = [h for h in history if h["disorder_type"].lower() == 'dyslexia']
    print(f'Dyslexia in History: {len(dyslexia_in_history)}')
    print('First 5 Dyslexia assessments:')
    for a in dyslexia_in_history[:5]:
        print(f'  - score={a["score"]}, status={a["status"]}')

else:
    print('No students found')

cursor.close()
conn.close()
