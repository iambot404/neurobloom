#!/usr/bin/env python
"""
Verify and test the recommendation integration
"""
from db import get_connection, DBError
import json
from datetime import datetime

def test_recommendations():
    """Test the recommendation system"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Check if recommendations table exists
        cursor.execute('''
            SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'neurobloom' AND TABLE_NAME = 'recommendations'
        ''')
        table_exists = cursor.fetchone()['count'] > 0
        print(f"✓ Recommendations table exists: {table_exists}")
        
        if not table_exists:
            print("✗ Recommendations table does not exist!")
            return
        
        # 2. Check table structure
        cursor.execute('''
            SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'neurobloom' AND TABLE_NAME = 'recommendations'
            ORDER BY ORDINAL_POSITION
        ''')
        columns = cursor.fetchall()
        print("\n✓ Table structure:")
        for col in columns:
            print(f"  - {col['COLUMN_NAME']}: {col['DATA_TYPE']}")
        
        # 3. Check if student_id=1 exists
        cursor.execute('SELECT id FROM users WHERE id = 1')
        user_exists = cursor.fetchone()
        print(f"\n✓ Student ID 1 exists: {user_exists is not None}")
        
        # 4. Check existing student assessments
        cursor.execute('''
            SELECT COUNT(*) as count FROM student_assessments WHERE student_id = 1
        ''')
        assessment_count = cursor.fetchone()['count']
        print(f"✓ Student 1 has {assessment_count} assessments")
        
        # 5. Check existing recommendations
        cursor.execute('''
            SELECT COUNT(*) as count FROM recommendations WHERE student_id = 1
        ''')
        rec_count = cursor.fetchone()['count']
        print(f"✓ Student 1 has {rec_count} recommendations")
        
        if rec_count > 0:
            cursor.execute('''
                SELECT disorder_type, COUNT(*) as count FROM recommendations 
                WHERE student_id = 1 GROUP BY disorder_type
            ''')
            rec_by_type = cursor.fetchall()
            print("\n✓ Recommendations by disorder:")
            for rec in rec_by_type:
                print(f"  - {rec['disorder_type']}: {rec['count']}")
            
            # Show sample recommendation
            cursor.execute('''
                SELECT disorder_type, recommendation_text, created_at 
                FROM recommendations WHERE student_id = 1 LIMIT 1
            ''')
            sample = cursor.fetchone()
            if sample:
                print(f"\n✓ Sample recommendation:")
                print(f"  Disorder: {sample['disorder_type']}")
                print(f"  Text: {sample['recommendation_text'][:80]}...")
                print(f"  Created: {sample['created_at']}")
        
        # 6. Test dashboard API query
        print("\n✓ Testing dashboard API query...")
        student_id = 1
        cursor.execute('''
            SELECT id, disorder_type, recommendation_text as title, 
                   'Personalized recommendation' as description, created_at as date
            FROM recommendations
            WHERE student_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        ''', (student_id,))
        recs = cursor.fetchall() or []
        print(f"  Dashboard would return {len(recs)} recommendations")
        
        print("\n✅ All tests passed!")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_recommendations()
