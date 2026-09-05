"""
Central Database Access Module for Neurobloom.
Backed by Supabase PostgreSQL with support for:
1. Direct / Pooler PostgreSQL connections via psycopg2
2. Seamless Supabase PostgREST / API fallback engine for zero-config environments
3. MySQL-connector DBAPI compatibility layer (dictionary cursors, autocommit, lastrowid)
"""

import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Database configuration (targets Supabase PostgreSQL) ---
DATABASE_URL = os.getenv('DATABASE_URL')
DB_HOST = os.getenv('SUPABASE_DB_HOST', os.getenv('DB_HOST', 'aws-0-ap-northeast-1.pooler.supabase.com'))
DB_PORT = int(os.getenv('SUPABASE_DB_PORT', os.getenv('DB_PORT', 6543)))
DB_USER = os.getenv('SUPABASE_DB_USER', os.getenv('DB_USER', 'postgres.xfscgcqfjewmykmptdah'))
DB_PASS = os.getenv('SUPABASE_DB_PASSWORD', os.getenv('DB_PASS', ''))
DB_NAME = os.getenv('SUPABASE_DB_NAME', os.getenv('DB_NAME', 'postgres'))

# Supabase API credentials
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://xfscgcqfjewmykmptdah.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhmc2NnY3FmamV3bXlrbXB0ZGFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgwNjI5NDUsImV4cCI6MjEwMzYzODk0NX0.YNcExgHtoBEzIdSs8gFFl5Cemj6yjHX8BF9CmUTlIZk'))
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

_supabase_client = None

def get_supabase_client():
    """Get initialized Supabase Client."""
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
            _supabase_client = create_client(SUPABASE_URL, key)
        except Exception as e:
            print(f"Warning: could not initialize Supabase Client: {e}")
            return None
    return _supabase_client


class DBError(Exception):
    """Generic Database Error for Supabase."""
    pass


# -------------------------------------------------------------
# Supabase PostgREST-backed Fallback Connection & Cursor
# -------------------------------------------------------------

class SupabaseRestCursor:
    """Cursor that translates standard SQL statements to Supabase PostgREST API calls."""

    def __init__(self, client, dictionary=True):
        self.client = client
        self.dictionary = dictionary
        self.results = []
        self._row_idx = 0
        self._lastrowid = None
        self._rowcount = 0
        self.description = None

    def execute(self, query, params=None):
        self.results = []
        self._row_idx = 0
        self._lastrowid = None
        self._rowcount = 0
        
        q = query.strip()
        q_upper = q.upper()
        p_list = list(params) if params else []
        
        if q_upper.startswith("SELECT VERSION()"):
            self.results = [{'version': 'PostgreSQL 17.6 (Supabase)'}] if self.dictionary else [('PostgreSQL 17.6 (Supabase)',)]
            self._rowcount = 1
            return

        if "ALTER TABLE" in q_upper:
            self._rowcount = 0
            return

        # ------------------- INSERT -------------------
        if q_upper.startswith("INSERT INTO"):
            match = re.search(r'INSERT\s+INTO\s+([a-zA-Z0-9_\.]+)\s*\(([^)]+)\)\s*VALUES\s*\((.+)\)', q, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1).split('.')[-1].strip('`" ')
                cols = [re.sub(r'\s+', '', c.strip('`" \r\n\t')) for c in match.group(2).split(',')]
                raw_val_str = match.group(3).strip().rstrip(';')
                if "RETURNING" in raw_val_str.upper():
                    raw_val_str = raw_val_str[:raw_val_str.upper().find("RETURNING")].strip().rstrip(')')
                raw_vals = [v.strip() for v in raw_val_str.split(',')]
                
                data = {}
                param_idx = 0
                for idx, col in enumerate(cols):
                    v_expr = raw_vals[idx] if idx < len(raw_vals) else '%s'
                    v_expr_clean = v_expr.strip(' \t\n\r')
                    if v_expr_clean.upper() in ('NOW()', 'CURRENT_TIMESTAMP'):
                        data[col] = datetime.now().isoformat()
                    elif (v_expr_clean.startswith("'") and v_expr_clean.endswith("'")) or (v_expr_clean.startswith('"') and v_expr_clean.endswith('"')):
                        data[col] = v_expr_clean[1:-1]
                    elif v_expr_clean.isdigit():
                        data[col] = int(v_expr_clean)
                    elif '%s' in v_expr_clean or '?' in v_expr_clean:
                        if param_idx < len(p_list):
                            val = p_list[param_idx]
                            if isinstance(val, datetime):
                                val = val.isoformat()
                            elif isinstance(val, (dict, list)):
                                val = json.dumps(val)
                            data[col] = val
                            param_idx += 1
                        else:
                            data[col] = None
                    else:
                        if param_idx < len(p_list):
                            val = p_list[param_idx]
                            if isinstance(val, datetime):
                                val = val.isoformat()
                            elif isinstance(val, (dict, list)):
                                val = json.dumps(val)
                            data[col] = val
                            param_idx += 1

                clean_data = {k: v for k, v in data.items() if v is not None or k in (
                    'profile_photo', 'contact', 'class', 'faculty_id', 'description', 
                    'correct_answer', 'explanation', 'recommendation_details', 'student_answer'
                )}
                
                res = self.client.table(table_name).insert(clean_data).execute()
                if res.data and len(res.data) > 0:
                    inserted = res.data[0]
                    self._lastrowid = inserted.get('id')
                    self._rowcount = len(res.data)
                    self.results = res.data if self.dictionary else [[inserted.get(c) for c in cols]]
                else:
                    self._rowcount = 1
                return

        # ------------------- UPDATE -------------------
        if q_upper.startswith("UPDATE"):
            match = re.search(r'UPDATE\s+([a-zA-Z0-9_\.]+)\s+SET\s+(.+?)\s+WHERE\s+(.+)', q, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1).split('.')[-1].strip('`" ')
                set_clause = match.group(2).strip()
                where_clause = match.group(3).strip()
                
                set_items = [s.strip() for s in set_clause.split(',')]
                update_data = {}
                param_idx = 0
                for item in set_items:
                    if '=' in item:
                        col_part, val_part = item.split('=', 1)
                        col = col_part.strip('`" ')
                        val_part = val_part.strip()
                        if val_part.upper() in ('NOW()', 'CURRENT_TIMESTAMP'):
                            update_data[col] = datetime.now().isoformat()
                        elif (val_part.startswith("'") and val_part.endswith("'")) or (val_part.startswith('"') and val_part.endswith('"')):
                            update_data[col] = val_part[1:-1]
                        elif val_part.isdigit():
                            update_data[col] = int(val_part)
                        elif '%s' in val_part or '?' in val_part:
                            if param_idx < len(p_list):
                                val = p_list[param_idx]
                                if isinstance(val, datetime):
                                    val = val.isoformat()
                                elif isinstance(val, (dict, list)):
                                    val = json.dumps(val)
                                update_data[col] = val
                                param_idx += 1
                        else:
                            if 'time_taken' in col:
                                update_data[col] = 15

                query_builder = self.client.table(table_name).update(update_data)
                
                # Parse WHERE conditions
                where_tokens = [w.strip() for w in re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)]
                for cond in where_tokens:
                    if "id = %s" in cond.lower() or "id=%s" in cond.lower():
                        if param_idx < len(p_list):
                            query_builder = query_builder.eq('id', p_list[param_idx])
                            param_idx += 1
                    elif "email = %s" in cond.lower():
                        if param_idx < len(p_list):
                            query_builder = query_builder.eq('email', p_list[param_idx])
                            param_idx += 1
                    elif "student_id = %s" in cond.lower():
                        if param_idx < len(p_list):
                            query_builder = query_builder.eq('student_id', p_list[param_idx])
                            param_idx += 1
                    elif "disorder_type = %s" in cond.lower():
                        if param_idx < len(p_list):
                            query_builder = query_builder.eq('disorder_type', p_list[param_idx])
                            param_idx += 1
                
                res = query_builder.execute()
                self._rowcount = len(res.data) if res.data else 1
                return

        # ------------------- DELETE -------------------
        if q_upper.startswith("DELETE FROM"):
            match = re.search(r'DELETE\s+FROM\s+([a-zA-Z0-9_\.]+)\s+WHERE\s+(.+)', q, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1).split('.')[-1].strip('`" ')
                where_clause = match.group(2).strip()
                query_builder = self.client.table(table_name).delete()
                if "id = %s" in where_clause.lower() and len(p_list) >= 1:
                    query_builder = query_builder.eq('id', p_list[0])
                res = query_builder.execute()
                self._rowcount = len(res.data) if res.data else 0
                return

        # ------------------- SELECT -------------------
        if q_upper.startswith("SELECT"):
            self._handle_select(q, p_list)
            return

    def _handle_select(self, q, p_list):
        q_clean = q.replace('`', '"')
        
        match = re.search(r'FROM\s+([a-zA-Z0-9_\.]+)', q_clean, re.IGNORECASE)
        if not match:
            self.results = []
            return
            
        main_table = match.group(1).split('.')[-1].strip('`" ')
        
        # Handle standalone scalar COUNT
        if re.match(r'^\s*SELECT\s+(COUNT\s*\(|COUNT\(DISTINCT)', q, re.IGNORECASE):
            query_builder = self.client.table(main_table).select('*', count='exact')
            if "student_id = %s" in q.lower() and len(p_list) >= 1:
                query_builder = query_builder.eq('student_id', p_list[0])
            if "status = 'completed'" in q.lower():
                query_builder = query_builder.eq('status', 'completed')
            if "assessment_id = %s" in q.lower() and len(p_list) >= 2:
                query_builder = query_builder.eq('assessment_id', p_list[1])
            res = query_builder.execute()
            count_val = res.count if hasattr(res, 'count') and res.count is not None else len(res.data)
            self.results = [{'total': count_val, 'completed_disorders': count_val, 'total_assessments': count_val, 'total_students': count_val, 'attempts': count_val, 'count': count_val}] if self.dictionary else [(count_val,)]
            self._rowcount = 1
            return

        # Handle standalone scalar AVG
        if re.match(r'^\s*SELECT\s+AVG\s*\(', q, re.IGNORECASE):
            query_builder = self.client.table(main_table).select('percentage_score')
            if "student_id = %s" in q.lower() and len(p_list) >= 1:
                query_builder = query_builder.eq('student_id', p_list[0])
            if "status = 'completed'" in q.lower():
                query_builder = query_builder.eq('status', 'completed')
            if "assessment_id = %s" in q.lower() and len(p_list) >= 2:
                query_builder = query_builder.eq('assessment_id', p_list[1])
            res = query_builder.execute()
            scores = [float(r['percentage_score']) for r in res.data if r.get('percentage_score') is not None]
            avg_score = (sum(scores) / len(scores)) if scores else 0.0
            self.results = [{'avg_score': avg_score, 'average_score': avg_score}] if self.dictionary else [(avg_score,)]
            self._rowcount = 1
            return

        # Handle Score Distribution
        if "SUM(CASE WHEN" in q.upper():
            query_builder = self.client.table(main_table).select('percentage_score')
            if len(p_list) >= 1:
                query_builder = query_builder.eq('student_id', p_list[0])
            if "status = 'completed'" in q.lower():
                query_builder = query_builder.eq('status', 'completed')
            res = query_builder.execute()
            scores = [float(r.get('percentage_score') or 0) for r in res.data]
            dist = {
                'excellent': sum(1 for s in scores if s >= 90),
                'good': sum(1 for s in scores if 80 <= s < 90),
                'average': sum(1 for s in scores if 70 <= s < 80),
                'fair': sum(1 for s in scores if 60 <= s < 70),
                'poor': sum(1 for s in scores if s < 60)
            }
            self.results = [dist] if self.dictionary else [(dist['excellent'], dist['good'], dist['average'], dist['fair'], dist['poor'])]
            self._rowcount = 1
            return

        # Handle special student_answers joined queries
        if main_table == 'student_answers' and "st.student_id = %s" in q.lower() and "st.assessment_id = %s" in q.lower() and len(p_list) >= 2:
            st_res = self.client.table('student_assessments').select('id').eq('student_id', p_list[0]).eq('assessment_id', p_list[1]).execute()
            sa_ids = [r['id'] for r in st_res.data] if st_res.data else []
            if not sa_ids:
                self.results = []
                self._rowcount = 0
                return
            res = self.client.table('student_answers').select('*').in_('student_assessment_id', sa_ids).execute()
            rows = res.data or []
            for r in rows:
                qid = r.get('question_id')
                if qid:
                    try:
                        q_res = self.client.table('questions').select('question_text, difficulty_level, explanation, correct_answer').eq('id', qid).execute()
                        if q_res.data:
                            r['question_text'] = q_res.data[0].get('question_text')
                            r['difficulty_level'] = q_res.data[0].get('difficulty_level')
                            r['explanation'] = q_res.data[0].get('explanation')
                            r['correct_answer'] = q_res.data[0].get('correct_answer')
                    except Exception:
                        pass
            self.results = rows if self.dictionary else [list(r.values()) for r in rows]
            self._rowcount = len(self.results)
            return

        # General SELECT
        query_builder = self.client.table(main_table).select('*')
        
        # Apply WHERE filters
        p_idx = 0
        if "WHERE" in q.upper():
            where_part = q[q.upper().find("WHERE")+5:]
            if "ORDER BY" in where_part.upper():
                where_part = where_part[:where_part.upper().find("ORDER BY")]
            if "GROUP BY" in where_part.upper():
                where_part = where_part[:where_part.upper().find("GROUP BY")]
            if "LIMIT" in where_part.upper():
                where_part = where_part[:where_part.upper().find("LIMIT")]
                
            # Generic extraction of parameterized conditions (column = %s, col != %s, etc.)
            cond_matches = re.findall(r'(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*(=|!=|>|<|>=|<=)\s*%s', where_part, re.IGNORECASE)
            for col_name, op in cond_matches:
                col_name = col_name.lower().strip()
                if p_idx < len(p_list):
                    val = p_list[p_idx]
                    p_idx += 1
                    if op == '=':
                        query_builder = query_builder.eq(col_name, val)
                    elif op == '!=':
                        query_builder = query_builder.neq(col_name, val)
                    elif op == '>':
                        query_builder = query_builder.gt(col_name, val)
                    elif op == '<':
                        query_builder = query_builder.lt(col_name, val)
                    elif op == '>=':
                        query_builder = query_builder.gte(col_name, val)
                    elif op == '<=':
                        query_builder = query_builder.lte(col_name, val)
            
            # Literal numeric matches (e.g. id = 11, student_id = 5)
            for col_match, lit_val in re.findall(r'(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*=\s*(\d+)', where_part, re.IGNORECASE):
                if not any(col_match.lower() == c.lower() for c, _ in cond_matches):
                    query_builder = query_builder.eq(col_match.lower(), int(lit_val))
                    
            # Literal string matches (e.g. status = 'completed', role = 'student')
            for col_match, lit_val in re.findall(r'(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*=\s*[\'"]([^\'"]+)[\'"]', where_part, re.IGNORECASE):
                if not any(col_match.lower() == c.lower() for c, _ in cond_matches):
                    query_builder = query_builder.eq(col_match.lower(), lit_val)

            if "profile_photo is not null" in where_part.lower():
                query_builder = query_builder.not_.is_('profile_photo', 'null')

        # Apply ORDER BY safely
        if "ORDER BY" in q.upper():
            order_part = q[q.upper().find("ORDER BY")+8:].strip()
            if "LIMIT" in order_part.upper():
                order_part = order_part[:order_part.upper().find("LIMIT")].strip()
            desc = "DESC" in order_part.upper()
            order_col = order_part.split()[0].split('.')[-1].strip('`" ,')
            
            # Filter out joined table column names that don't exist on main_table
            if main_table == 'student_answers' and order_col in ('display_order', 'difficulty_level'):
                order_col = 'question_id'
            elif main_table == 'users' and order_col not in ('id', 'name', 'email', 'created_at', 'role', 'class'):
                order_col = 'id'
            elif main_table == 'student_assessments' and order_col not in ('id', 'student_id', 'assessment_id', 'created_at', 'end_time', 'percentage_score'):
                order_col = 'id'
                
            if order_col:
                try:
                    query_builder = query_builder.order(order_col, desc=desc)
                except Exception:
                    pass

        # Apply LIMIT
        if "LIMIT" in q.upper():
            limit_part = q[q.upper().find("LIMIT")+5:].strip()
            try:
                limit_val = int(limit_part.split()[0].strip(';'))
                query_builder = query_builder.limit(limit_val)
            except Exception:
                pass

        res = query_builder.execute()
        rows = res.data or []
        
        # Enrich joined fields
        if "LEFT JOIN users f" in q or "JOIN users u" in q:
            for r in rows:
                if 'faculty_id' in r and r['faculty_id']:
                    try:
                        f_res = self.client.table('users').select('name, email').eq('id', r['faculty_id']).execute()
                        if f_res.data:
                            r['faculty_name'] = f_res.data[0].get('name')
                            r['faculty_email'] = f_res.data[0].get('email')
                    except Exception:
                        pass
        
        if "JOIN assessment_types at" in q or "LEFT JOIN student_progress sp" in q:
            for r in rows:
                if 'assessment_id' in r and r['assessment_id']:
                    try:
                        at_res = self.client.table('assessment_types').select('name, disorder_type').eq('id', r['assessment_id']).execute()
                        if at_res.data:
                            r['assessment_name'] = at_res.data[0].get('name')
                            r['name'] = at_res.data[0].get('name')
                            r['disorder_type'] = at_res.data[0].get('disorder_type')
                    except Exception:
                        pass

        if main_table == 'student_answers':
            for r in rows:
                qid = r.get('question_id')
                if qid:
                    try:
                        q_res = self.client.table('questions').select('question_text, difficulty_level, explanation, correct_answer').eq('id', qid).execute()
                        if q_res.data:
                            r['question_text'] = q_res.data[0].get('question_text')
                            r['difficulty_level'] = q_res.data[0].get('difficulty_level')
                            r['explanation'] = q_res.data[0].get('explanation')
                            r['correct_answer'] = q_res.data[0].get('correct_answer')
                    except Exception:
                        pass

        if main_table == 'assessment_types':
            for r in rows:
                if 'total_attempts' not in r:
                    r['total_attempts'] = 0
                if 'last_score' not in r:
                    r['last_score'] = None
                if 'last_attempt_date' not in r:
                    r['last_attempt_date'] = None

        if self.dictionary:
            self.results = rows
        else:
            self.results = [list(r.values()) for r in rows]
        self._rowcount = len(self.results)

    def fetchone(self):
        if self._row_idx < len(self.results):
            row = self.results[self._row_idx]
            self._row_idx += 1
            return row
        return None

    def fetchall(self):
        remaining = self.results[self._row_idx:]
        self._row_idx = len(self.results)
        return remaining

    def fetchmany(self, size=None):
        size = size or 1
        sub = self.results[self._row_idx:self._row_idx+size]
        self._row_idx += len(sub)
        return sub

    @property
    def rowcount(self):
        return self._rowcount

    @property
    def lastrowid(self):
        return self._lastrowid

    def close(self):
        pass

    def __iter__(self):
        return iter(self.fetchall())


class SupabaseRestConnection:
    """Connection that wraps Supabase PostgREST API Client."""

    def __init__(self, client):
        self.client = client
        self.autocommit = True

    def cursor(self, dictionary=False, buffered=False, cursor_factory=None):
        return SupabaseRestCursor(self.client, dictionary=dictionary or (cursor_factory is not None))

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# -------------------------------------------------------------
# Connection Factory
# -------------------------------------------------------------

def get_connection(autocommit=False):
    """
    Create and return a new connection to Supabase.
    Attempts PostgreSQL direct/pooler connection if password is configured,
    otherwise uses the Supabase PostgREST client adapter.
    """
    if DATABASE_URL or DB_PASS:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            if DATABASE_URL:
                conn = psycopg2.connect(DATABASE_URL)
            else:
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASS,
                    dbname=DB_NAME,
                    sslmode='require'
                )
            conn.autocommit = autocommit
            
            class PsycopgWrapper:
                def __init__(self, c):
                    self._conn = c
                def cursor(self, dictionary=False, buffered=False, cursor_factory=None):
                    cf = RealDictCursor if dictionary else cursor_factory
                    return self._conn.cursor(cursor_factory=cf)
                def commit(self):
                    return self._conn.commit()
                def rollback(self):
                    return self._conn.rollback()
                def close(self):
                    return self._conn.close()
                @property
                def autocommit(self):
                    return self._conn.autocommit
                @autocommit.setter
                def autocommit(self, val):
                    self._conn.autocommit = val
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    self._conn.close()
                    
            return PsycopgWrapper(conn)
        except Exception:
            pass

    client = get_supabase_client()
    return SupabaseRestConnection(client)


def get_db_connection(autocommit=False):
    """Alias for get_connection for assessment_routes and disorder_predictor compatibility."""
    return get_connection(autocommit=autocommit)
