#!/usr/bin/env python3
"""Test the fixed dashboard API"""

from db import get_connection, DBError
import json

def test_dashboard_query():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Test the fixed query
        student_id = 1
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
                   sa.created_at as date
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            ORDER BY sa.created_at DESC
            LIMIT 5
        ''', (student_id,))
        
        recent = cursor.fetchall()
        print(f'[OK] Recent assessments query: Found {len(recent)} results')
        
        # Test stats query
        cursor.execute('''
            SELECT COUNT(*) as total_assessments, 
                   AVG(CAST(sa.percentage_score AS FLOAT)) as average_score
            FROM student_assessments sa
            WHERE sa.student_id = %s AND sa.status = 'completed'
        ''', (student_id,))
        
        stats = cursor.fetchone()
        print(f'[OK] Stats query: {stats}')
        
        # Test disorder-wise progress
        cursor.execute('''
            SELECT at.disorder_type,
                   COUNT(*) as attempts,
                   AVG(CAST(sa.percentage_score AS FLOAT)) as average_score
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            GROUP BY at.disorder_type
        ''', (student_id,))
        
        progress = cursor.fetchall()
        print(f'[OK] Disorder progress query: Found {len(progress)} disorders')
        
        cursor.close()
        conn.close()
        print('\n[OK] All database queries work correctly!')
        return True
        
    except Exception as e:
        print(f'[FAIL] Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_dashboard_query()
    exit(0 if success else 1)
