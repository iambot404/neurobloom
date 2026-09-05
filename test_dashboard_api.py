#!/usr/bin/env python
"""
Test the student dashboard API endpoint
"""
from db import get_connection, DBError
import json
from decimal import Decimal

def test_dashboard_query():
    """Test if the SQL queries work correctly"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Test with student_id = 1
        student_id = 1
        
        # Helper function for risk level
        def get_risk_level(score):
            if score is None:
                return 'Medium'
            score = float(score)
            if score >= 75:
                return 'Low'
            elif score >= 50:
                return 'Medium'
            else:
                return 'High'
        
        # Test: Get recent assessments with disorder type from assessment_types
        print("\n1. Testing recent assessments query...")
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
                   sa.created_at as date
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            ORDER BY sa.created_at DESC
            LIMIT 5
        ''', (student_id,))
        recent = cursor.fetchall() or []
        print(f"   Found {len(recent)} recent assessments")
        for item in recent[:1]:
            print(f"   Sample: {json.dumps(dict(item), default=str, indent=2)}")
        
        # Test: Get quick stats
        print("\n2. Testing stats query...")
        cursor.execute('''
            SELECT COUNT(*) as total_assessments, 
                   AVG(CAST(sa.percentage_score AS FLOAT)) as average_score
            FROM student_assessments sa
            WHERE sa.student_id = %s AND sa.status = 'completed'
        ''', (student_id,))
        stats_result = cursor.fetchone()
        print(f"   Stats: {json.dumps(dict(stats_result), default=str, indent=2)}")
        
        # Test: Get disorder-wise progress
        print("\n3. Testing disorder progress query...")
        cursor.execute('''
            SELECT at.disorder_type,
                   COUNT(*) as attempts,
                   AVG(CAST(sa.percentage_score AS FLOAT)) as average_score
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            GROUP BY at.disorder_type
        ''', (student_id,))
        disorder_progress = cursor.fetchall() or []
        print(f"   Found {len(disorder_progress)} disorder types")
        for dp in disorder_progress[:1]:
            print(f"   Sample: {json.dumps(dict(dp), default=str, indent=2)}")
        
        # Test: Check if recommendations table exists
        print("\n4. Testing recommendations table...")
        cursor.execute('''
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'recommendations' LIMIT 1
        ''')
        has_recommendations = cursor.fetchone()
        print(f"   Recommendations table exists: {bool(has_recommendations)}")
        
        if has_recommendations:
            cursor.execute('''
                SELECT id, disorder_type, recommendation_text as title, 
                       recommendation_details as description, created_at as date
                FROM recommendations
                WHERE student_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            ''', (student_id,))
            recs = cursor.fetchall() or []
            print(f"   Found {len(recs)} recommendations")
            if recs:
                print(f"   Sample: {json.dumps(dict(recs[0]), default=str, indent=2)}")
        
        cursor.close()
        conn.close()
        print("\n✅ All queries executed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_dashboard_query()
