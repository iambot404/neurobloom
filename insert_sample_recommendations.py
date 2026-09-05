# Script to insert sample recommendations for student_id=1
from db import get_connection, DBError
from datetime import datetime

conn = get_connection()
cursor = conn.cursor()

recommendations = [
    (1, 'dyslexia', 'Use multisensory reading strategies', 'Encourage daily reading with tactile and visual aids.', datetime.now()),
    (1, 'dyscalculia', 'Practice math games', 'Engage in math puzzles and games to improve number sense.', datetime.now()),
    (1, 'dysgraphia', 'Handwriting exercises', 'Daily handwriting practice with guided tracing.', datetime.now()),
]

for student_id, disorder_type, text, details, created_at in recommendations:
    cursor.execute('''
        INSERT INTO recommendations (student_id, disorder_type, recommendation_text, recommendation_details, created_at)
        VALUES (%s, %s, %s, %s, %s)
    ''', (student_id, disorder_type, text, details, created_at))

conn.commit()
cursor.close()
conn.close()

print('Sample recommendations inserted for student_id=1.')
