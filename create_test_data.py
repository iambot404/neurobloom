#!/usr/bin/env python
"""
Create test data for dashboard
"""
from db import get_connection, DBError
from datetime import datetime, timedelta

def create_test_data():
    """Create test assessments for student_id=1"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First check if student_id=1 exists
        cursor.execute('SELECT id FROM users WHERE id = 1')
        if not cursor.fetchone():
            print("❌ Student with ID 1 doesn't exist. Creating test user...")
            cursor.execute('''
                INSERT INTO users (name, email, role, password_hash, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            ''', ('Test Student', 'student@test.com', 'student', 'hashed_password'))
            conn.commit()
            print("✅ Test user created")
        
        # Get assessment type IDs
        cursor.execute('SELECT id, disorder_type FROM assessment_types LIMIT 3')
        assessments = cursor.fetchall()
        
        if not assessments:
            print("❌ No assessment types found. Creating test assessment types...")
            disorders = ['dyslexia', 'dyscalculia', 'dysgraphia']
            for disorder in disorders:
                cursor.execute('''
                    INSERT INTO assessment_types 
                    (name, description, disorder_type, total_questions, time_limit_minutes, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                ''', (disorder.capitalize(), f'{disorder} assessment', disorder, 20, 30))
            conn.commit()
            print("✅ Test assessment types created")
            
            # Fetch them again
            cursor.execute('SELECT id, disorder_type FROM assessment_types LIMIT 3')
            assessments = cursor.fetchall()
        
        print(f"\n📝 Creating test assessments for student_id=1...")
        
        # Create test assessments
        for i, (assessment_id, disorder_type) in enumerate(assessments):
            base_date = datetime.now() - timedelta(days=10-i)
            scores = [65, 72, 80]
            
            cursor.execute('''
                INSERT INTO student_assessments
                (student_id, assessment_id, status, start_time, end_time, 
                 total_score, percentage_score, time_taken_minutes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                1, assessment_id, 'completed', 
                base_date - timedelta(minutes=30),
                base_date,
                scores[i] if i < len(scores) else 70,
                scores[i] if i < len(scores) else 70,
                30,
                base_date,
                base_date
            ))
            print(f"   ✓ Created assessment for {disorder_type} with score {scores[i] if i < len(scores) else 70}%")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ Test data created successfully!")
        print("   You can now test the dashboard with student_id=1")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_data()
