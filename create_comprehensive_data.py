#!/usr/bin/env python
"""
Create comprehensive test data with assessments from past to today
"""
from db import get_connection, DBError
from datetime import datetime, timedelta
import random

def create_comprehensive_test_data():
    """Create multiple assessments for student_id=1 from past to today"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Creating comprehensive test data...")
        
        # Get assessment type IDs
        cursor.execute('SELECT id, disorder_type FROM assessment_types')
        assessments = cursor.fetchall()
        
        if not assessments:
            print("❌ No assessment types found.")
            return
        
        print(f"Found {len(assessments)} assessment types\n")
        
        # Create assessments from 30 days ago till today
        base_date = datetime.now()
        student_id = 1
        
        print("Creating assessments:")
        for day_offset in range(30, -1, -1):
            # Randomly select an assessment type
            assessment_id, disorder_type = random.choice(assessments)
            
            # Random score between 40-95
            score = random.randint(40, 95)
            
            # Random status: 60% completed, 40% in_progress
            status = 'completed' if random.random() > 0.4 else 'in_progress'
            
            # Date from past to today
            assessment_date = base_date - timedelta(days=day_offset)
            
            # Only add scores for completed assessments
            percentage_score = score if status == 'completed' else None
            
            # Time taken (only for completed)
            time_taken = random.randint(15, 45) if status == 'completed' else 0
            
            start_time = assessment_date - timedelta(minutes=time_taken if time_taken > 0 else 30)
            end_time = assessment_date
            
            cursor.execute('''
                INSERT INTO student_assessments
                (student_id, assessment_id, status, start_time, end_time, 
                 total_score, percentage_score, time_taken_minutes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                student_id, assessment_id, status, 
                start_time, end_time,
                score if status == 'completed' else None,
                percentage_score,
                time_taken,
                assessment_date,
                assessment_date
            ))
            
            status_text = f"{status.upper():<12}"
            print(f"  {assessment_date.strftime('%Y-%m-%d')}: {disorder_type:<12} - {status_text} - {score if status == 'completed' else '-'}%")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ Comprehensive test data created!")
        print("   31 assessments added (from 30 days ago till today)")
        print("   Dashboard will now show all these assessments dynamically")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_comprehensive_test_data()
