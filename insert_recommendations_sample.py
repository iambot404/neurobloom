#!/usr/bin/env python
"""
Insert sample recommendations for testing
"""
from db import get_connection, DBError
from datetime import datetime

def insert_sample_recommendations():
    """Insert comprehensive sample recommendations"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        student_id = 1
        timestamp = datetime.now()
        
        # Sample recommendations for each disorder
        recommendations = [
            # Dyslexia recommendations
            (student_id, 'dyslexia', '✓ Continue evidence-based, structured literacy instruction', 'Maintain phonemic awareness and phonics practice', timestamp),
            (student_id, 'dyslexia', '✓ Regular reading fluency development with daily guided and independent reading', 'Use multisensory reading approaches in lessons', timestamp),
            (student_id, 'dyslexia', '⚠ Monitor reading comprehension and word recognition closely', 'Monthly progress monitoring assessments recommended', timestamp),
            (student_id, 'dyslexia', '✓ Foster enthusiasm for reading with age-appropriate books', 'HOME: Read together daily for 15-20 minutes', timestamp),
            
            # Dyscalculia recommendations
            (student_id, 'dyscalculia', '⚠ Implement structured number sense instruction', 'Focus on subitizing and number recognition activities', timestamp),
            (student_id, 'dyscalculia', '⚠ Use multisensory math approaches with manipulatives', 'Combine visual, auditory, and kinesthetic learning', timestamp),
            (student_id, 'dyscalculia', '✓ Practice math facts through games and interactive activities', 'Daily 10-15 minute sessions recommended', timestamp),
            (student_id, 'dyscalculia', '⚠ Provide extra time for math assignments and assessments (1.5x)', 'Use graph paper and visual aids for organization', timestamp),
            
            # Dysgraphia recommendations
            (student_id, 'dysgraphia', '✓ Daily handwriting practice with guided tracing exercises', 'Use pencil grips and ergonomic writing tools', timestamp),
            (student_id, 'dysgraphia', '⚠ Implement multisensory writing instruction with letter formation', 'Combine visual, tactile, and motor activities', timestamp),
            (student_id, 'dysgraphia', '✓ Allow use of assistive technology for written expression', 'Speech-to-text tools and digital devices when appropriate', timestamp),
            (student_id, 'dysgraphia', '⚠ Provide extra time for writing assignments and tests (1.5-2x)', 'Focus on content over mechanics initially', timestamp),
        ]
        
        for rec in recommendations:
            cursor.execute('''
                INSERT INTO recommendations 
                (student_id, disorder_type, recommendation_text, recommendation_details, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', rec)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Inserted {len(recommendations)} sample recommendations for student ID 1")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    insert_sample_recommendations()
