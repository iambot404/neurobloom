from flask import Flask, render_template, jsonify, request, redirect, url_for, session, make_response
import os
from db import get_connection, get_db_connection, DBError
from assessment_routes import register_assessment_routes

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

# Register assessment routes
register_assessment_routes(app)


@app.route('/db-test')
def db_test():
    """Simple endpoint to test DB connectivity. Returns database version on success."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        v_str = version.get('version') if isinstance(version, dict) else str(version[0])
        return jsonify({'status': 'ok', 'database_version': v_str, 'provider': 'Supabase PostgreSQL'})
    except Exception as e:
        app.logger.exception('DB test failed')
        return jsonify({'status': 'error', 'error': str(e)}), 500



def insert_user(name, email, hashed_password, contact, role='student'):
    """Insert a user into the users table. Returns (True, None) on success or (False, error_msg) on failure."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO users (name, email, password, contact, role) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (name, email, hashed_password, contact, role))
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Exception as e:
        # detect duplicate email
        err = str(e)
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        if 'Duplicate' in err or 'UNIQUE' in err:
            return False, 'Email already registered'
        return False, err


from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session
from werkzeug.utils import secure_filename
import uuid


def login_required(role=None):
    """Decorator to require a logged-in user with an optional specific role.

    Usage: @login_required('student') or @login_required()
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = session.get('user_id')
            user_role = session.get('role')
            if not user_id:
                app.logger.info('Access denied: not logged in')
                # Check if this is an API request
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401
                return redirect(url_for('login'))
            if role and user_role != role:
                app.logger.info(f"Access denied: role mismatch (required={role}, actual={user_role})")
                # Check if this is an API request
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'error': 'Access denied'}), 403
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def ensure_profile_column():
    """Ensure that the users table has a profile_photo column. Attempt to add it if missing."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_photo VARCHAR(255) NULL;")
            conn.commit()
            app.logger.info('Added profile_photo column to users table')
        except Exception as inner_e:
            # Ignore if column exists or other harmless error
            app.logger.debug('ensure_profile_column check/skip: %s', inner_e)
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN class VARCHAR(100) NULL;")
            conn.commit()
            app.logger.info('Added class column to users table')
        except Exception as inner_e:
            app.logger.debug('ensure_class_column check/skip: %s', inner_e)
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN faculty_id INT NULL;")
            conn.commit()
            app.logger.info('Added faculty_id column to users table')
        except Exception as inner_e:
            app.logger.debug('ensure_faculty_id_column check/skip: %s', inner_e)
        
        cursor.close()
        conn.close()
    except Exception as e:
        app.logger.warning('Could not ensure columns: %s', e)


# Try to ensure column exists at startup (best-effort)
ensure_profile_column()


def cleanup_profile_photos_for_disallowed_roles():
    """Remove profile_photo files and DB values for users whose role is not student/faculty.

    This is a best-effort cleanup to ensure only students and faculty keep profile photos.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, profile_photo, role FROM users WHERE profile_photo IS NOT NULL")
        rows = cursor.fetchall()
        for r in rows:
            role = r.get('role')
            pp = r.get('profile_photo')
            if not pp:
                continue
            if role not in ('student', 'faculty'):
                # attempt delete file on disk
                try:
                    rel = pp.lstrip('/')
                    abs_path = os.path.join(os.path.dirname(__file__), *rel.split('/'))
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        app.logger.info('Removed profile photo file for user %s: %s', r.get('id'), abs_path)
                except Exception:
                    app.logger.exception('Failed to remove profile photo file: %s', pp)
                try:
                    upd = conn.cursor()
                    upd.execute('UPDATE users SET profile_photo = NULL WHERE id = %s', (r.get('id'),))
                    upd.close()
                except Exception:
                    app.logger.exception('Failed to clear profile_photo DB for user %s', r.get('id'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        app.logger.exception('cleanup_profile_photos_for_disallowed_roles failed')


# Best-effort cleanup at startup
cleanup_profile_photos_for_disallowed_roles()


@app.route('/faculty_register', methods=['POST'])
def faculty_register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    contact = request.form.get('contact', '').strip()

    if not (name and email and password):
        return "Name, email and password are required", 400

    hashed = generate_password_hash(password)
    ok, err = insert_user(name, email, hashed, contact, role='faculty')
    if not ok:
        return f"Registration failed: {err}", 400
    return redirect(url_for('login'))


@app.route('/student_register', methods=['POST'])
def student_register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    contact = request.form.get('contact', '').strip()

    if not (name and email and password):
        return "Name, email and password are required", 400

    hashed = generate_password_hash(password)
    ok, err = insert_user(name, email, hashed, contact, role='student')
    if not ok:
        return f"Registration failed: {err}", 400
    return redirect(url_for('login'))


def authenticate_user(email, password, expected_role=None):
    """Authenticate a user by email and password. Optionally check role.
    Returns (True, user_row_dict) on success, (False, error_msg) on failure.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, email, password, contact, role, profile_photo FROM users WHERE email = %s', (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return False, 'User not found'
        if expected_role and row.get('role') != expected_role:
            return False, 'Role mismatch'
        # stored hash in row['password']
        if not check_password_hash(row.get('password', ''), password):
            return False, 'Invalid password'
        return True, row
    except Exception as e:
        return False, str(e)


@app.route('/login/student', methods=['POST'])
def login_student():
    email = request.form.get('student_email', '').strip()
    password = request.form.get('student_password', '')
    ok, result = authenticate_user(email, password, expected_role='student')
    if not ok:
        return f"Login failed: {result}", 401
    # on success set session and redirect to student page
    from flask import session
    session['user_id'] = result['id']
    session['role'] = result['role']
    session['name'] = result['name']
    # profile photo (if present)
    if result.get('profile_photo'):
        session['profile_photo'] = result.get('profile_photo')
    return redirect(url_for('student_profile'))


@app.route('/login/faculty', methods=['POST'])
def login_faculty():
    email = request.form.get('faculty_email', '').strip()
    password = request.form.get('faculty_password', '')
    ok, result = authenticate_user(email, password, expected_role='faculty')
    if not ok:
        return f"Login failed: {result}", 401
    from flask import session
    session['user_id'] = result['id']
    session['role'] = result['role']
    session['name'] = result['name']
    if result.get('profile_photo'):
        session['profile_photo'] = result.get('profile_photo')
    return redirect(url_for('faculty_page'))


@app.route('/student')
@login_required('student')
def student_page():
    # ensure session has latest profile_photo so page shows uploaded image after refresh
    user_id = session.get('user_id')
    if user_id and not session.get('profile_photo'):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT profile_photo FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row and row.get('profile_photo'):
                session['profile_photo'] = row.get('profile_photo')
        except Exception:
            app.logger.debug('Could not refresh profile_photo into session')
    return render_template('student.html')


@app.route('/student-dashboard')
@login_required('student')
def student_dashboard():
    """Render student dashboard page"""
    return render_template('student-dashboard.html')


@app.route('/student-profile')
@login_required('student')
def student_profile():
    """Render student profile page"""
    return render_template('student-profile.html')


@app.route('/faculty')
@login_required('faculty')
def faculty_page():
    user_id = session.get('user_id')
    if user_id and not session.get('profile_photo'):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT profile_photo FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row and row.get('profile_photo'):
                session['profile_photo'] = row.get('profile_photo')
        except Exception:
            app.logger.debug('Could not refresh profile_photo into session')
    return render_template('faculty.html')


@app.route('/logout')
def logout():
    from flask import session
    session.clear()
    return redirect(url_for('login'))


@app.route('/upload-profile-photo', methods=['POST'])
@login_required()
def upload_profile_photo():
    """Accept a multipart/form-data upload with field 'photo', save file, update users.profile_photo and return JSON with url."""
    try:
        # ensure only student/faculty may have profile photos; run a small cleanup first
        cleanup_profile_photos_for_disallowed_roles()

        user_id = session.get('user_id')
        user_role = session.get('role')
        if not user_id:
            return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401
        if user_role not in ('student', 'faculty'):
            # reject upload from disallowed roles
            return jsonify({'status': 'error', 'error': 'Only students and faculty may upload profile photos'}), 403

        if 'photo' not in request.files:
            return jsonify({'status': 'error', 'error': 'No file part'}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No selected file'}), 400

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
        # create unique filename
        unique = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        dest = os.path.join(upload_dir, unique)

        # save file to disk; if anything fails later we'll remove it
        file.save(dest)

        # update user row and remove previous image if present
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT profile_photo FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            prev = row.get('profile_photo') if row else None
            # store relative path
            rel_path = f"/static/uploads/{unique}"
            upd = conn.cursor()
            upd.execute('UPDATE users SET profile_photo = %s WHERE id = %s', (rel_path, user_id))
            conn.commit()
            upd.close()
            cursor.close()
        except Exception:
            # cleanup newly saved file on error
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except Exception:
                app.logger.exception('Failed to remove temp upload after DB error')
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # delete previous photo file if it was in uploads
        if prev:
            try:
                prev_rel = prev.lstrip('/')
                # only remove files that are inside our uploads folder
                if prev_rel.startswith('static/uploads/'):
                    prev_abs = os.path.join(os.path.dirname(__file__), *prev_rel.split('/'))
                    if os.path.exists(prev_abs):
                        os.remove(prev_abs)
                        app.logger.info('Removed previous profile photo for user %s', user_id)
            except Exception:
                app.logger.exception('Failed to remove previous profile photo for user %s', user_id)
        # update session so the uploaded photo persists across refreshes
        try:
            session['profile_photo'] = rel_path
        except Exception:
            app.logger.debug('Could not set session profile_photo (client may not accept cookies)')

        return jsonify({'status': 'ok', 'url': rel_path})
    except Exception as e:
        app.logger.exception('Upload failed')
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/dashboard')
def dashboard_redirect():
    """Intelligent dashboard redirection based on authentication state"""
    role = session.get('role')
    if role == 'faculty':
        return redirect(url_for('faculty_page'))
    elif role == 'student':
        return redirect(url_for('student_profile'))
    return redirect(url_for('list_assessments'))


@app.route('/profile')
def profile_redirect():
    """Intelligent profile redirection based on authentication state"""
    role = session.get('role')
    if role == 'faculty':
        return redirect(url_for('faculty_page'))
    elif role == 'student':
        return redirect(url_for('student_profile'))
    return redirect(url_for('login'))


@app.route('/how-it-works')
def how_it_works():
    return redirect('/#how-it-works')


@app.route('/about')
def about():
    return redirect('/#about')


@app.route('/assessments')
def list_assessments():
    """Display list of available assessments for students and guests (public-first)"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    is_authenticated = bool(user_id)
    
    return render_template('assessments_list.html', 
                           is_authenticated=is_authenticated,
                           user_id=user_id,
                           user_role=user_role)


@app.route('/test-api')
def test_api_page():
    """Test page for API debugging"""
    return render_template('test_api.html')


@app.route('/assessment/<int:assessment_id>')
def take_assessment(assessment_id):
    """Display assessment taking interface - public-first for students and guests"""
    user_id = session.get('user_id')
    is_guest = not bool(user_id)
    
    # Special handling for Dyslexia Assessment (ID=1)
    if assessment_id == 1:
        app.logger.info('Serving integrated dyslexia assessment (guest=%s)', is_guest)
        return render_template('dyslexia_integrated.html', assessment_id=assessment_id, is_guest=is_guest, user_id=user_id)
    
    # Special handling for Dyscalculia Assessment (ID=2)
    if assessment_id == 2:
        app.logger.info('Serving integrated dyscalculia assessment (guest=%s)', is_guest)
        return render_template('dyscalculia_test.html', assessment_id=assessment_id, is_guest=is_guest, user_id=user_id)
    
    # Special handling for Dysgraphia Assessment (ID=3)
    if assessment_id == 3:
        app.logger.info('Serving integrated dysgraphia assessment (guest=%s)', is_guest)
        return render_template('dysgraphia_test.html', assessment_id=assessment_id, is_guest=is_guest, user_id=user_id)
    
    # Check if assessment has visual or puzzle questions
    has_visual = False
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT COUNT(*) as visual_count FROM questions 
            WHERE assessment_id = %s 
            AND question_type IN ('image', 'puzzle', 'visual_matching', 'pattern', 'sequence', 'sorting')
        ''', (assessment_id,))
        result = cursor.fetchone()
        has_visual = result['visual_count'] > 0 if result else False
        cursor.close()
        conn.close()
    except Exception as e:
        app.logger.warning('Could not check visual questions: %s', e)
    
    template = 'assessment_visual.html' if has_visual else 'assessment_test.html'
    return render_template(template, assessment_id=assessment_id, is_guest=is_guest, user_id=user_id)


@app.route('/assessment/results/<int:student_assessment_id>')
@login_required('student')
def view_assessment_results(student_assessment_id):
    """Display assessment results with ML predictions"""
    user_id = session.get('user_id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify this assessment belongs to the current user
        cursor.execute('''
            SELECT assessment_id FROM student_assessments 
            WHERE id = %s AND student_id = %s
            AND status = 'completed'
        ''', (student_assessment_id, user_id))
        result = cursor.fetchone()
        assessment_id = result['assessment_id'] if result else None
    finally:
        cursor.close()
        conn.close()
    
    if not assessment_id:
        return "Assessment not found or you don't have access to it.", 404
    
    return render_template('assessment_results.html', 
                          assessment_id=assessment_id,
                          student_assessment_id=student_assessment_id)


@app.route('/dyslexia-results/<int:assessment_id>')
def view_dyslexia_results(assessment_id):
    """Display dyslexia assessment results with all attempts (public-friendly)"""
    is_guest = not bool(session.get('user_id'))
    return render_template('dyslexia_results.html', assessment_id=assessment_id, is_guest=is_guest)


@app.route('/dyscalculia-results/<int:assessment_id>')
def view_dyscalculia_results(assessment_id):
    """Display dyscalculia assessment results with all attempts (public-friendly)"""
    is_guest = not bool(session.get('user_id'))
    return render_template('dyscalculia_results.html', assessment_id=assessment_id, is_guest=is_guest)


@app.route('/dysgraphia-results/<int:assessment_id>')
def view_dysgraphia_results(assessment_id):
    """Display dysgraphia assessment results with all attempts (public-friendly)"""
    is_guest = not bool(session.get('user_id'))
    return render_template('dysgraphia_results.html', assessment_id=assessment_id, is_guest=is_guest)


@app.route('/support')
def support():
    return render_template('support.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/api/student-stats')
@login_required('student')
def get_student_stats():
    """API endpoint to return student statistics for dashboard."""
    user_id = session.get('user_id')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get total assessments completed
        cursor.execute("""
            SELECT COUNT(*) as total FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
        """, (user_id,))
        t_row = cursor.fetchone()
        total_assessments = t_row.get('total', 0) if isinstance(t_row, dict) else (t_row[0] if t_row else 0)
        
        # Get average score from all completed assessments
        cursor.execute("""
            SELECT AVG(percentage_score) as avg_score FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
        """, (user_id,))
        result = cursor.fetchone()
        average_score = (result.get('avg_score', 0) if isinstance(result, dict) else (result[0] if result else 0)) or 0
        
        # Get progress by disorder
        cursor.execute("""
            SELECT disorder_type, total_attempts, average_score, last_assessment_date
            FROM student_progress 
            WHERE student_id = %s
        """, (user_id,))
        progress_data = cursor.fetchall()
        
        # Get recent assessments
        cursor.execute("""
            SELECT sa.id, at.name, sa.percentage_score, sa.end_time, at.disorder_type
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            ORDER BY sa.end_time DESC
            LIMIT 5
        """, (user_id,))
        activities = cursor.fetchall() or []
        
        # Format recent activity for frontend
        recent_activity = []
        for activity in activities:
            recent_activity.append({
                'title': activity.get('name', 'Assessment'),
                'score': int(activity.get('percentage_score', 0)),
                'subject': activity.get('disorder_type', 'General'),
                'date': activity.get('end_time', 'Recently'),
                'icon': '📝'
            })
        
        # Get performance data (last 5 assessments)
        cursor.execute("""
            SELECT percentage_score, end_time
            FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
            ORDER BY end_time DESC
            LIMIT 5
        """, (user_id,))
        perf = cursor.fetchall() or []
        performance_data = [{'score': p.get('percentage_score', 0), 'date': p.get('end_time', '')} for p in reversed(perf)]
        
        # Get score distribution
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN percentage_score >= 90 THEN 1 ELSE 0 END) as excellent,
                SUM(CASE WHEN percentage_score >= 80 AND percentage_score < 90 THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN percentage_score >= 70 AND percentage_score < 80 THEN 1 ELSE 0 END) as average,
                SUM(CASE WHEN percentage_score >= 60 AND percentage_score < 70 THEN 1 ELSE 0 END) as fair,
                SUM(CASE WHEN percentage_score < 60 THEN 1 ELSE 0 END) as poor
            FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
        """, (user_id,))
        dist = cursor.fetchone() or {}
        score_data = [
            {'label': 'Excellent (90+)', 'count': dist.get('excellent', 0) or 0},
            {'label': 'Good (80-89)', 'count': dist.get('good', 0) or 0},
            {'label': 'Average (70-79)', 'count': dist.get('average', 0) or 0},
            {'label': 'Fair (60-69)', 'count': dist.get('fair', 0) or 0},
            {'label': 'Poor (<60)', 'count': dist.get('poor', 0) or 0}
        ]
        
        return jsonify({
            'total_assessments': total_assessments,
            'average_score': round(float(average_score), 2),
            'recent_activity': recent_activity,
            'performance_data': performance_data,
            'score_distribution': score_data,
            'progress_by_disorder': progress_data
        }), 200
    
    except Exception as e:
        print(f"Error getting student stats: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/student-info')
@login_required('student')
def get_student_info():
    """Get current student's information."""
    user_id = session.get('user_id')
    app.logger.info(f'Fetching student info for user_id: {user_id}')
    
    if not user_id:
        return jsonify({'error': 'No user ID in session'}), 401
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.contact, u.role, u.class, u.faculty_id,
                   f.name as faculty_name
            FROM users u
            LEFT JOIN users f ON u.faculty_id = f.id AND f.role = 'faculty'
            WHERE u.id = %s
        ''', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            app.logger.info(f'Student info found: {row["name"]} ({row["email"]})')
            return jsonify({
                'id': row.get('id'),
                'name': row.get('name'),
                'email': row.get('email'),
                'contact': row.get('contact'),
                'role': row.get('role'),
                'class': row.get('class'),
                'faculty_id': row.get('faculty_id'),
                'faculty_name': row.get('faculty_name')
            }), 200
        else:
            app.logger.warning(f'Student not found for user_id: {user_id}')
            return jsonify({'error': 'Student not found'}), 404
    except Exception as e:
        app.logger.exception('Failed to get student info')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculties')
@login_required('student')
def get_faculties():
    """Get list of all faculties."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM users WHERE role = "faculty" ORDER BY name')
        faculties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'faculties': faculties
        }), 200
    except Exception as e:
        app.logger.exception('Failed to get faculties')
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-student-info', methods=['POST'])
@login_required('student')
def update_student_info():
    """Update student's personal information including class and faculty."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    contact = data.get('contact', '').strip()
    class_name = data.get('class', '').strip()
    faculty_id = data.get('faculty_id', '')
    
    # If this is a setup-only update (no name/email provided), fetch existing ones
    is_setup_only = not name and not email
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if is_setup_only:
            # Get existing name and email if not provided
            cursor.execute('SELECT name, email, contact FROM users WHERE id = %s', (user_id,))
            existing = cursor.fetchone()
            if existing:
                name = name or existing.get('name', '')
                email = email or existing.get('email', '')
                contact = contact or existing.get('contact', '')
        
        if not name or not email:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if email is already used by another user (only if email was changed)
        if email:
            cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'error': 'Email already in use by another account'}), 400
        
        # Convert empty string to None for faculty_id
        faculty_id = int(faculty_id) if faculty_id else None
        
        # Update user info
        upd = conn.cursor()
        upd.execute('''
            UPDATE users 
            SET name = %s, email = %s, contact = %s, class = %s, faculty_id = %s
            WHERE id = %s
        ''', (name, email, contact, class_name, faculty_id, user_id))
        
        conn.commit()
        upd.close()
        cursor.close()
        conn.close()
        
        # Update session
        session['name'] = name
        
        return jsonify({'status': 'ok', 'message': 'Information updated successfully'}), 200
    except Exception as e:
        app.logger.exception('Failed to update student info')
        return jsonify({'error': str(e)}), 500


@app.route('/api/setup-profile', methods=['POST'])
@login_required('student')
def setup_profile():
    """Complete initial student profile setup with class and faculty."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    class_name = data.get('class', '').strip()
    faculty_id = data.get('faculty_id', '')
    
    if not class_name:
        return jsonify({'error': 'Class is required'}), 400
    
    if not faculty_id:
        return jsonify({'error': 'Faculty is required'}), 400
    
    try:
        faculty_id = int(faculty_id)
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update class and faculty_id
        cursor.execute('''
            UPDATE users 
            SET class = %s, faculty_id = %s
            WHERE id = %s
        ''', (class_name, faculty_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'ok', 'message': 'Profile setup completed successfully'}), 200
    except ValueError:
        return jsonify({'error': 'Invalid faculty ID'}), 400
    except Exception as e:
        app.logger.exception('Failed to setup profile')
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/profile', methods=['GET'])
@login_required('student')
def get_student_profile():
    """Get complete student profile information including assessments and statistics."""
    user_id = session.get('user_id')
    print(f'[DEBUG] Getting profile for user_id: {user_id}')
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get student profile info
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.contact, u.role, u.class, u.faculty_id,
                   u.profile_photo, u.created_at,
                   f.name as faculty_name
            FROM users u
            LEFT JOIN users f ON u.faculty_id = f.id AND f.role = 'faculty'
            WHERE u.id = %s AND u.role = 'student'
        ''', (user_id,))
        
        profile = cursor.fetchone()
        print(f'[DEBUG] Profile retrieved: {profile}')
        
        if not profile:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Get all assessment attempts for this student
        cursor.execute('''
            SELECT 
                sa.id,
                sa.assessment_id,
                sa.percentage_score,
                sa.status,
                sa.created_at,
                at.disorder_type
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s
            ORDER BY sa.created_at DESC
        ''', (user_id,))
        sa_rows = cursor.fetchall() or []
        
        cursor.close()
        conn.close()
        
        # Calculate statistics
        total_assessments = len(sa_rows)
        all_scores = [float(r.get('percentage_score') or 0.0) for r in sa_rows if r.get('percentage_score') is not None]
        avg_score = round(float(sum(all_scores) / len(all_scores)), 1) if all_scores else 0.0
        
        aid_to_disorder = {1: 'dyslexia', 2: 'dyscalculia', 3: 'dysgraphia'}
        
        disorder_map = {
            'dyslexia': {'disorder': 'dyslexia', 'assessment_id': 1, 'attempts': 0, 'average_score': 0.0, 'best_score': 0.0, 'lowest_score': 0.0, '_scores': []},
            'dyscalculia': {'disorder': 'dyscalculia', 'assessment_id': 2, 'attempts': 0, 'average_score': 0.0, 'best_score': 0.0, 'lowest_score': 0.0, '_scores': []},
            'dysgraphia': {'disorder': 'dysgraphia', 'assessment_id': 3, 'attempts': 0, 'average_score': 0.0, 'best_score': 0.0, 'lowest_score': 0.0, '_scores': []}
        }
        
        last_date = None
        attempted_disorders = set()
        
        for row in sa_rows:
            aid = row.get('assessment_id') or 1
            dt = (row.get('disorder_type') or aid_to_disorder.get(aid, 'dyslexia')).lower()
            attempted_disorders.add(dt)
            if dt not in disorder_map:
                disorder_map[dt] = {'disorder': dt, 'assessment_id': aid, 'attempts': 0, 'average_score': 0.0, 'best_score': 0.0, 'lowest_score': 0.0, '_scores': []}
            
            score = float(row.get('percentage_score') or 0.0)
            disorder_map[dt]['_scores'].append(score)
            disorder_map[dt]['assessment_id'] = aid
            if not last_date and row.get('created_at'):
                last_date = row.get('created_at')
        
        for dt, dinfo in disorder_map.items():
            scores = dinfo.pop('_scores', [])
            dinfo['attempts'] = len(scores)
            if scores:
                dinfo['average_score'] = round(float(sum(scores) / len(scores)), 1)
                dinfo['best_score'] = round(float(max(scores)), 1)
                dinfo['lowest_score'] = round(float(min(scores)), 1)
        
        return jsonify({
            'status': 'ok',
            'profile': {
                'id': profile.get('id'),
                'name': profile.get('name'),
                'email': profile.get('email'),
                'contact': profile.get('contact'),
                'role': profile.get('role'),
                'class': profile.get('class'),
                'faculty_id': profile.get('faculty_id'),
                'faculty_name': profile.get('faculty_name'),
                'profile_photo': profile.get('profile_photo'),
                'created_at': str(profile.get('created_at')) if profile.get('created_at') else None
            },
            'statistics': {
                'total_assessments': total_assessments,
                'average_score': avg_score,
                'disorders_attempted': len(attempted_disorders),
                'last_assessment_date': str(last_date) if last_date else None
            },
            'disorder_breakdown': list(disorder_map.values())
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get student profile')
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/profile', methods=['PUT'])
@login_required('student')
def update_student_profile():
    """Update student profile information (name, email, contact, class, faculty)."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current profile
        cursor.execute('SELECT id, name, email, contact, class, faculty_id FROM users WHERE id = %s', (user_id,))
        current = cursor.fetchone()
        
        if not current:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Prepare updated values
        name = data.get('name', current.get('name')).strip()
        email = data.get('email', current.get('email')).strip()
        contact = data.get('contact', current.get('contact', '')).strip()
        class_name = data.get('class', current.get('class', '')).strip()
        faculty_id = data.get('faculty_id', current.get('faculty_id'))
        
        # Validate required fields
        if not name or not email:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if email is already used by another user
        if email != current.get('email'):
            cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'error': 'Email already in use'}), 409
        
        # Convert faculty_id to int or None
        if faculty_id:
            try:
                faculty_id = int(faculty_id)
            except (ValueError, TypeError):
                faculty_id = None
        else:
            faculty_id = None
        
        # Update profile
        upd = conn.cursor()
        upd.execute('''
            UPDATE users 
            SET name = %s, email = %s, contact = %s, class = %s, faculty_id = %s
            WHERE id = %s
        ''', (name, email, contact, class_name, faculty_id, user_id))
        
        conn.commit()
        upd.close()
        
        # Update session
        session['name'] = name
        session['email'] = email
        
        # Fetch and return updated profile
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.contact, u.role, u.class, u.faculty_id,
                   f.name as faculty_name
            FROM users u
            LEFT JOIN users f ON u.faculty_id = f.id AND f.role = 'faculty'
            WHERE u.id = %s
        ''', (user_id,))
        
        updated_profile = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'Profile updated successfully',
            'profile': {
                'id': updated_profile.get('id'),
                'name': updated_profile.get('name'),
                'email': updated_profile.get('email'),
                'contact': updated_profile.get('contact'),
                'role': updated_profile.get('role'),
                'class': updated_profile.get('class'),
                'faculty_id': updated_profile.get('faculty_id'),
                'faculty_name': updated_profile.get('faculty_name')
            }
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to update student profile')
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-password', methods=['POST'])
@login_required()  # Allow both students and faculty
def update_password():
    """Update student's password."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Both passwords are required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current password hash
        cursor.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not check_password_hash(row.get('password', ''), current_password):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash new password
        hashed_password = generate_password_hash(new_password)
        
        # Update password
        upd = conn.cursor()
        upd.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
        conn.commit()
        upd.close()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'ok', 'message': 'Password updated successfully'}), 200
    except Exception as e:
        app.logger.exception('Failed to update password')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty-info', methods=['GET', 'PUT'])
@login_required('faculty')
def faculty_info_handler():
    """Get or update current faculty's information."""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'No user ID in session'}), 401
    
    if request.method == 'GET':
        app.logger.info(f'Fetching faculty info for user_id: {user_id}')
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get faculty profile
            cursor.execute('''
                SELECT id, name, email, contact, role, class, profile_photo
                FROM users
                WHERE id = %s
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                f_class = row.get('class')
                
                # Get student and assessment records (class-specific or overall)
                if f_class:
                    cursor.execute('''
                        SELECT u.id, u.name, u.email, u.class
                        FROM users u
                        WHERE u.role = 'student' AND u.class = %s
                    ''', (f_class,))
                    stu_rows = cursor.fetchall() or []
                    
                    cursor.execute('''
                        SELECT sa.id, sa.percentage_score, sa.status, sa.student_id
                        FROM student_assessments sa
                        JOIN users u ON sa.student_id = u.id
                        WHERE u.class = %s
                    ''', (f_class,))
                    sa_rows = cursor.fetchall() or []
                else:
                    cursor.execute('''
                        SELECT u.id, u.name, u.email, u.class
                        FROM users u
                        WHERE u.role = 'student'
                    ''')
                    stu_rows = cursor.fetchall() or []
                    
                    cursor.execute('''
                        SELECT sa.id, sa.percentage_score, sa.status, sa.student_id
                        FROM student_assessments sa
                    ''')
                    sa_rows = cursor.fetchall() or []
                
                total_students = len(stu_rows)
                total_assessments = len(sa_rows)
                completed_sa = [r for r in sa_rows if (r.get('status') or '').lower() == 'completed']
                completed_count = len(completed_sa)
                comp_scores = [float(r['percentage_score']) for r in completed_sa if r.get('percentage_score') is not None]
                avg_score = round(float(sum(comp_scores) / len(comp_scores)), 1) if comp_scores else 0.0
                
                cursor.close()
                conn.close()
                
                app.logger.info(f'Faculty info found: {row["name"]} ({row["email"]})')
                return jsonify({
                    'profile': {
                        'id': row.get('id'),
                        'name': row.get('name'),
                        'email': row.get('email'),
                        'contact': row.get('contact'),
                        'role': row.get('role'),
                        'class': row.get('class'),
                        'profile_photo': row.get('profile_photo')
                    },
                    'statistics': {
                        'total_students': total_students,
                        'total_assessments': total_assessments,
                        'completed_assessments': completed_count,
                        'average_score': avg_score
                    }
                }), 200
            else:
                cursor.close()
                conn.close()
                app.logger.warning(f'Faculty not found for user_id: {user_id}')
                return jsonify({'error': 'Faculty not found'}), 404
        except Exception as e:
            app.logger.exception('Failed to get faculty info')
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        app.logger.info(f'Updating faculty info for user_id: {user_id}')
        data = request.get_json()
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        contact = data.get('contact', '').strip()
        class_name = data.get('class', '').strip()
        
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if email is already used by another user
            cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'error': 'Email already in use by another account'}), 400
            
            # Update faculty info
            cursor.execute('''
                UPDATE users 
                SET name = %s, email = %s, contact = %s, class = %s
                WHERE id = %s
            ''', (name, email, contact, class_name, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update session
            session['name'] = name
            
            return jsonify({'status': 'ok', 'message': 'Information updated successfully'}), 200
        except Exception as e:
            app.logger.exception('Failed to update faculty info')
            return jsonify({'error': str(e)}), 500


@app.route('/api/setup-faculty-profile', methods=['POST'])
@login_required('faculty')
def setup_faculty_profile():
    """Complete initial faculty profile setup with class/department."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    class_name = data.get('class', '').strip()
    
    if not class_name:
        return jsonify({'error': 'Class/Department is required'}), 400
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update class
        cursor.execute('''
            UPDATE users 
            SET class = %s
            WHERE id = %s
        ''', (class_name, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'ok', 'message': 'Profile setup completed successfully'}), 200
    except Exception as e:
        app.logger.exception('Failed to setup faculty profile')
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-faculty-info', methods=['POST'])
@login_required('faculty')
def update_faculty_info():
    """Update faculty's personal information including class."""
    user_id = session.get('user_id')
    data = request.get_json()
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    contact = data.get('contact', '').strip()
    class_name = data.get('class', '').strip()
    
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if email is already used by another user
        cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already in use by another account'}), 400
        
        # Update faculty info
        cursor.execute('''
            UPDATE users 
            SET name = %s, email = %s, contact = %s, class = %s
            WHERE id = %s
        ''', (name, email, contact, class_name, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session
        session['name'] = name
        
        return jsonify({'status': 'ok', 'message': 'Information updated successfully'}), 200
    except Exception as e:
        app.logger.exception('Failed to update faculty info')
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-students', methods=['GET'])
@login_required('faculty')
def get_students():
    """Get all students in the faculty's class."""
    user_id = session.get('user_id')
    app.logger.info(f'get-students: user_id={user_id}')
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get faculty's class
        cursor.execute('SELECT class FROM users WHERE id = %s AND role = %s', (user_id, 'faculty'))
        faculty = cursor.fetchone()
        app.logger.info(f'get-students: faculty={faculty}')
        
        faculty_class = faculty.get('class') if faculty else None
        app.logger.info(f'get-students: faculty_class={faculty_class}')
        
        # Get all students (class-specific or all students)
        if faculty_class:
            cursor.execute('''
                SELECT 
                    id, 
                    name, 
                    email, 
                    class
                FROM users
                WHERE role = %s AND class = %s
                ORDER BY name ASC
            ''', ('student', faculty_class))
        else:
            cursor.execute('''
                SELECT 
                    id, 
                    name, 
                    email, 
                    class
                FROM users
                WHERE role = %s
                ORDER BY name ASC
            ''', ('student',))
        
        students = cursor.fetchall() or []
        
        # Get all assessments in 1 query for instant in-memory lookup
        cursor.execute('''
            SELECT sa.student_id, sa.percentage_score, sa.status, sa.created_at
            FROM student_assessments sa
            ORDER BY sa.created_at DESC
        ''')
        all_sa = cursor.fetchall() or []
        
        sa_by_student = {}
        for r in all_sa:
            sid = r.get('student_id')
            if sid not in sa_by_student:
                sa_by_student[sid] = []
            sa_by_student[sid].append(r)
        
        # Format the response with dynamic metrics
        formatted_students = []
        for student in students:
            stu_id = student['id']
            stu_sa_rows = sa_by_student.get(stu_id, [])
            
            comp_sa = [r for r in stu_sa_rows if (r.get('status') or '').lower() == 'completed']
            cnt = len(comp_sa)
            scores = [float(r['percentage_score']) for r in comp_sa if r.get('percentage_score') is not None]
            avg = (sum(scores) / len(scores)) if scores else None
            last_d = comp_sa[0].get('created_at') if comp_sa else (stu_sa_rows[0].get('created_at') if stu_sa_rows else None)
            
            formatted_students.append({
                'id': student['id'],
                'name': student['name'],
                'email': student['email'],
                'class': student['class'],
                'assessments_completed': int(cnt or 0),
                'average_score': f"{float(avg):.1f}%" if (avg is not None and cnt > 0) else '-',
                'last_activity': str(last_d) if last_d else 'No activity'
            })
            
        cursor.close()
        conn.close()
        
        return jsonify({'students': formatted_students}), 200
    except Exception as e:
        app.logger.exception('Failed to get students')
        return jsonify({'error': str(e)}), 500


@app.route('/api/student-dashboard/<int:student_id>', methods=['GET'])
@login_required('faculty')
def get_student_dashboard(student_id):
    """Get a specific student's dashboard data for faculty view."""
    faculty_id = session.get('user_id')
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify the student belongs to this faculty's class
        cursor.execute('''
            SELECT u.id, u.name, u.class
            FROM users u
            WHERE u.id = %s AND u.role = 'student'
        ''', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Student not found'}), 404
        
        # Get faculty's class
        cursor.execute('SELECT class FROM users WHERE id = %s AND role = %s', (faculty_id, 'faculty'))
        faculty = cursor.fetchone()
        
        if not faculty or faculty['class'] != student['class']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Unauthorized: Student not in your class'}), 403
        
        # Get assessments completed count
        cursor.execute('''
            SELECT COUNT(*) as total FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
        ''', (student_id,))
        t_row = cursor.fetchone() or {}
        total_assessments = t_row.get('total', 0) if isinstance(t_row, dict) else (t_row[0] if t_row else 0)
        
        # Get average score
        cursor.execute('''
            SELECT AVG(percentage_score) as avg_score FROM student_assessments 
            WHERE student_id = %s AND status = 'completed'
        ''', (student_id,))
        result = cursor.fetchone() or {}
        average_score = result.get('avg_score', 0) if isinstance(result, dict) else (result[0] if result else 0)
        average_score = float(average_score or 0)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'id': student['id'],
            'name': student['name'],
            'class': student['class'],
            'total_assessments': total_assessments,
            'average_score': f"{average_score:.1f}%",
            'current_streak': 0,
            'upcoming_count': 0
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get student dashboard')
        return jsonify({'error': str(e)}), 500


# Faculty Dashboard API Endpoints
@app.route('/api/faculty/dashboard', methods=['GET'])
@login_required('faculty')
def faculty_dashboard():
    """Get faculty dashboard data with student list and analytics"""
    try:
        faculty_id = session.get('user_id')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT class FROM users WHERE id = %s', (faculty_id,))
        fac_row = cursor.fetchone()
        faculty_class = (fac_row.get('class') if fac_row else None) or session.get('class')
        
        # Get all students in faculty's class (or all students if no specific class)
        if faculty_class:
            cursor.execute('''
                SELECT id, name, email, role, profile_photo, class
                FROM users
                WHERE class = %s AND role = 'student'
                ORDER BY name ASC
            ''', (faculty_class,))
        else:
            cursor.execute('''
                SELECT id, name, email, role, profile_photo, class
                FROM users
                WHERE role = 'student'
                ORDER BY name ASC
            ''')
            
        students = cursor.fetchall() or []
        
        # Bulk query all student assessments
        cursor.execute('''
            SELECT sa.student_id, sa.percentage_score, sa.status, sa.created_at, at.disorder_type
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            ORDER BY sa.created_at DESC
        ''')
        all_sa = cursor.fetchall() or []
        
        sa_by_student = {}
        for r in all_sa:
            sid = r.get('student_id')
            if sid not in sa_by_student:
                sa_by_student[sid] = []
            sa_by_student[sid].append(r)
        
        students_data = []
        total_assessments = 0
        
        for student in students:
            stu_id = student['id']
            stu_sa = sa_by_student.get(stu_id, [])
            
            comp_sa = [r for r in stu_sa if (r.get('status') or '').lower() == 'completed']
            assessment_count = len(comp_sa)
            total_assessments += assessment_count
            
            scores = [float(r['percentage_score']) for r in comp_sa if r.get('percentage_score') is not None]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            
            # Group by disorder_type in Python
            disorder_map = {}
            for r in comp_sa:
                dt = (r.get('disorder_type') or 'General').lower()
                score_val = float(r.get('percentage_score') or 0.0)
                if dt not in disorder_map:
                    disorder_map[dt] = {'scores': [], 'attempts': 0, 'last_date': r.get('created_at')}
                disorder_map[dt]['scores'].append(score_val)
                disorder_map[dt]['attempts'] += 1
                
            disorder_risks = []
            for dt, d_info in disorder_map.items():
                best_sc = max(d_info['scores']) if d_info['scores'] else 0.0
                r_lvl = 'Low Risk' if best_sc >= 75 else ('Medium Risk' if best_sc >= 50 else 'High Risk')
                disorder_risks.append({
                    'disorder_type': dt,
                    'risk_level': r_lvl,
                    'score': best_sc,
                    'attempts': d_info['attempts'],
                    'last_date': str(d_info['last_date']) if d_info['last_date'] else ''
                })
            
            # Determine overall risk
            overall_risk = 'No Risk'
            if disorder_risks:
                risk_order = {'High Risk': 0, 'Medium Risk': 1, 'Low Risk': 2, 'No Risk': 3}
                for dr in disorder_risks:
                    dr_risk = dr.get('risk_level', 'No Risk')
                    if risk_order.get(dr_risk, 3) < risk_order.get(overall_risk, 3):
                        overall_risk = dr_risk
            
            students_data.append({
                'id': student.get('id'),
                'name': student.get('name'),
                'email': student.get('email'),
                'profile_photo': student.get('profile_photo'),
                'assessment_count': assessment_count,
                'avg_score': float(avg_score),
                'overall_risk': overall_risk,
                'disorder_risks': disorder_risks
            })
        
        cursor.close()
        conn.close()
        
        # Calculate analytics directly from calculated students_data
        no_risk_count = len([s for s in students_data if s.get('overall_risk') == 'No Risk'])
        low_risk_count = len([s for s in students_data if s.get('overall_risk') == 'Low Risk'])
        med_risk_count = len([s for s in students_data if s.get('overall_risk') == 'Medium Risk'])
        high_risk_count = len([s for s in students_data if s.get('overall_risk') == 'High Risk'])
        
        analytics = {
            'performance': {
                'labels': ['Dyslexia', 'Dyscalculia', 'Dysgraphia'],
                'scores': [65, 72, 58]
            },
            'risk_distribution': {
                'no_risk': no_risk_count,
                'low_risk': low_risk_count,
                'medium_risk': med_risk_count,
                'high_risk': high_risk_count
            },
            'disorder_breakdown': {
                'dyslexia': len([s for s in students_data if any(d.get('disorder_type') == 'dyslexia' for d in s.get('disorder_risks', []))]),
                'dyscalculia': len([s for s in students_data if any(d.get('disorder_type') == 'dyscalculia' for d in s.get('disorder_risks', []))]),
                'dysgraphia': len([s for s in students_data if any(d.get('disorder_type') == 'dysgraphia' for d in s.get('disorder_risks', []))])
            }
        }
        
        return jsonify({
            'status': 'ok',
            'stats': {
                'total_students': len(students_data),
                'total_assessments': total_assessments
            },
            'students': students_data,
            'analytics': analytics
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get faculty dashboard')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty/students', methods=['GET'])
@login_required('faculty')
def faculty_students_filtered():
    """Get filtered list of students"""
    try:
        faculty_class = session.get('class')
        search = request.args.get('search', '').lower()
        disorder = request.args.get('disorder', '')
        risk = request.args.get('risk', '')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get students
        cursor.execute('''
            SELECT id, name, email, profile_photo, class
            FROM users
            WHERE class = %s AND role = 'student'
            ORDER BY name ASC
        ''', (faculty_class,))
        students = cursor.fetchall()
        
        filtered_students = []
        
        for student in students:
            # Apply search filter
            if search and search not in student['name'].lower() and search not in student['email'].lower():
                continue
            
            # Get disorder risks
            cursor.execute('''
                SELECT at.disorder_type, 
                    MAX(sa.percentage_score) as score,
                    COUNT(*) as attempts,
                    MAX(sa.created_at) as last_date
                FROM student_assessments sa
                JOIN assessment_types at ON sa.assessment_id = at.id
                WHERE sa.student_id = %s
                GROUP BY at.disorder_type
            ''', (student['id'],))
            raw_risks = cursor.fetchall() or []
            
            disorder_risks = []
            for rr in raw_risks:
                score_val = float(rr.get('score') or 0)
                r_lvl = 'Low Risk' if score_val >= 75 else ('Medium Risk' if score_val >= 50 else 'High Risk')
                disorder_risks.append({
                    'disorder_type': rr.get('disorder_type') or 'General',
                    'risk_level': r_lvl,
                    'score': score_val,
                    'attempts': rr.get('attempts', 0),
                    'last_date': str(rr.get('last_date')) if rr.get('last_date') else ''
                })
            
            # Apply disorder filter
            if disorder:
                if not any(d.get('disorder_type', '').lower() == disorder.lower() for d in disorder_risks):
                    continue
            
            # Apply risk filter
            if risk:
                if not any(d.get('risk_level', '').lower() == risk.lower() for d in disorder_risks):
                    continue
            
            # Get stats
            cursor.execute('''
                SELECT COUNT(*) as count FROM student_assessments 
                WHERE student_id = %s
            ''', (student['id'],))
            cnt_row = cursor.fetchone() or {}
            count = cnt_row.get('count', 0) if isinstance(cnt_row, dict) else (cnt_row[0] if cnt_row else 0)
            
            cursor.execute('''
                SELECT AVG(percentage_score) as avg_score FROM student_assessments 
                WHERE student_id = %s
            ''', (student['id'],))
            result = cursor.fetchone() or {}
            avg_score = result.get('avg_score', 0) if isinstance(result, dict) else (result[0] if result else 0)
            avg_score = float(avg_score or 0)
            
            # Determine overall risk
            overall_risk = 'No Risk'
            risk_order = {'High Risk': 0, 'Medium Risk': 1, 'Low Risk': 2, 'No Risk': 3}
            for dr in disorder_risks:
                if risk_order.get(dr['risk_level'], 3) < risk_order.get(overall_risk, 3):
                    overall_risk = dr['risk_level']
            
            filtered_students.append({
                'id': student['id'],
                'name': student['name'],
                'email': student['email'],
                'profile_photo': student['profile_photo'],
                'assessment_count': count,
                'avg_score': float(avg_score),
                'overall_risk': overall_risk,
                'disorder_risks': disorder_risks
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'students': filtered_students}), 200
        
    except Exception as e:
        app.logger.exception('Failed to filter students')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty/student/<int:student_id>', methods=['GET'])
@login_required('faculty')
def faculty_student_details(student_id):
    """Get detailed information about a specific student"""
    try:
        faculty_class = session.get('class')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get student
        cursor.execute('''
            SELECT id, name, email, class
            FROM users
            WHERE id = %s AND role = 'student'
        ''', (student_id,))
        student = cursor.fetchone()
        
        if not student or student['class'] != faculty_class:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get assessments
        cursor.execute('''
            SELECT COUNT(*) as count FROM student_assessments 
            WHERE student_id = %s
        ''', (student_id,))
        cnt_row = cursor.fetchone() or {}
        count = cnt_row.get('count', 0) if isinstance(cnt_row, dict) else (cnt_row[0] if cnt_row else 0)
        
        cursor.execute('''
            SELECT AVG(percentage_score) as avg_score FROM student_assessments 
            WHERE student_id = %s
        ''', (student_id,))
        result = cursor.fetchone() or {}
        avg_score = result.get('avg_score', 0) if isinstance(result, dict) else (result[0] if result else 0)
        avg_score = float(avg_score or 0)
        
        # Get disorder risks
        cursor.execute('''
            SELECT at.disorder_type, 
                MAX(sa.percentage_score) as score,
                COUNT(*) as attempts,
                MAX(sa.created_at) as last_date
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s
            GROUP BY at.disorder_type
        ''', (student_id,))
        raw_risks = cursor.fetchall() or []
        disorder_risks = []
        for rr in raw_risks:
            score_val = float(rr.get('score') or 0)
            r_lvl = 'Low Risk' if score_val >= 75 else ('Medium Risk' if score_val >= 50 else 'High Risk')
            disorder_risks.append({
                'disorder_type': rr.get('disorder_type') or 'General',
                'risk_level': r_lvl,
                'score': score_val,
                'attempts': rr.get('attempts', 0),
                'last_date': str(rr.get('last_date')) if rr.get('last_date') else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'student': {
                'id': student['id'],
                'name': student['name'],
                'email': student['email'],
                'class': student['class'],
                'assessment_count': count,
                'avg_score': float(avg_score),
                'disorder_risks': disorder_risks
            }
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get student details')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty/student/<int:student_id>/assessments', methods=['GET'])
@login_required('faculty')
def faculty_student_assessments(student_id):
    """Get all assessments for a student"""
    try:
        faculty_class = session.get('class')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify student belongs to faculty's class
        cursor.execute('''
            SELECT class FROM users WHERE id = %s AND role = 'student'
        ''', (student_id,))
        student = cursor.fetchone()
        
        if not student or student['class'] != faculty_class:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get assessments
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, sa.created_at as date
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s
            ORDER BY sa.created_at DESC
        ''', (student_id,))
        assessments_raw = cursor.fetchall() or []
        assessments = []
        for a in assessments_raw:
            score_val = float(a.get('score') or 0)
            r_lvl = 'Low Risk' if score_val >= 75 else ('Medium Risk' if score_val >= 50 else 'High Risk')
            assessments.append({
                'id': a.get('id'),
                'disorder_type': a.get('disorder_type') or 'General',
                'score': score_val,
                'risk_level': r_lvl,
                'date': str(a.get('date')) if a.get('date') else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'assessments': assessments}), 200
        
    except Exception as e:
        app.logger.exception('Failed to get student assessments')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty/assessment/<int:assessment_id>', methods=['GET'])
@login_required('faculty')
def faculty_assessment_details(assessment_id):
    """Get detailed information about an assessment"""
    try:
        faculty_class = session.get('class')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get assessment
        cursor.execute('''
            SELECT sa.id, sa.student_id, at.disorder_type, sa.percentage_score as score, 
                sa.created_at, u.class
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            JOIN users u ON sa.student_id = u.id
            WHERE sa.id = %s
        ''', (assessment_id,))
        assessment = cursor.fetchone()
        
        if not assessment or assessment.get('class') != faculty_class:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get predictions with recommendations
        cursor.execute('''
            SELECT risk_level, confidence_score, recommendations
            FROM ml_predictions
            WHERE assessment_id = %s
        ''', (assessment_id,))
        prediction = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        recommendations = []
        if prediction and prediction.get('recommendations'):
            recs_val = prediction.get('recommendations')
            recommendations = recs_val.split(',') if isinstance(recs_val, str) else recs_val
        
        score_val = float(assessment.get('score') or 0)
        risk_lvl = 'Low Risk' if score_val >= 75 else ('Medium Risk' if score_val >= 50 else 'High Risk')
        
        return jsonify({
            'assessment': {
                'id': assessment.get('id'),
                'disorder_type': assessment.get('disorder_type') or 'General',
                'score': score_val,
                'risk_level': risk_lvl,
                'date': str(assessment.get('created_at')) if assessment.get('created_at') else '',
                'recommendations': recommendations
            }
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get assessment details')
        return jsonify({'error': str(e)}), 500


@app.route('/api/faculty/export-csv', methods=['GET'])
@login_required('faculty')
def faculty_export_csv():
    """Export class data as CSV"""
    try:
        import csv
        from io import StringIO
        
        faculty_class = session.get('class')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get students
        cursor.execute('''
            SELECT id, name, email
            FROM users
            WHERE class = %s AND role = 'student'
            ORDER BY name ASC
        ''', (faculty_class,))
        students = cursor.fetchall() or []
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Email', 'Assessments', 'Average Score'])
        
        for student in students:
            stu_id = student.get('id')
            cursor.execute('''
                SELECT COUNT(*) as count, AVG(percentage_score) as avg_score
                FROM student_assessments
                WHERE student_id = %s AND status = 'completed'
            ''', (stu_id,))
            s_row = cursor.fetchone() or {}
            cnt = s_row.get('count', 0) if isinstance(s_row, dict) else (s_row[0] if s_row else 0)
            avg = s_row.get('avg_score', 0) if isinstance(s_row, dict) else (s_row[1] if len(s_row) > 1 else 0)
            avg_f = float(avg or 0)
            writer.writerow([
                student.get('name', ''),
                student.get('email', ''),
                int(cnt or 0),
                f"{avg_f:.1f}%"
            ])
            
        cursor.close()
        conn.close()
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=class_report_{faculty_class}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        app.logger.exception('Failed to export CSV')
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/dashboard', methods=['GET'])
@login_required('student')
def student_dashboard_api():
    """Get student dashboard data including assessments, progress, and recommendations"""
    try:
        student_id = session.get('user_id')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Helper function to determine risk level
        def get_risk_level(score):
            if score is None:
                return 'Medium'
            try:
                score_f = float(score)
                if score_f >= 75:
                    return 'Low'
                elif score_f >= 50:
                    return 'Medium'
                else:
                    return 'High'
            except Exception:
                return 'Medium'
        
        # Get recent assessments with disorder type from assessment_types
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
                   sa.created_at as date, sa.status
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s
            ORDER BY sa.created_at DESC
            LIMIT 5
        ''', (student_id,))
        recent = cursor.fetchall() or []
        
        # Format recent assessments
        for item in recent:
            item['score'] = float(item.get('score')) if item.get('score') is not None else None
            item['date'] = str(item.get('date')) if item.get('date') else ''
            item['disorder_type'] = item.get('disorder_type') or 'General'
            item['risk_level'] = get_risk_level(item.get('score'))
        
        # Get full assessment history
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
                   sa.created_at as date, sa.status
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s
            ORDER BY sa.created_at DESC
        ''', (student_id,))
        history = cursor.fetchall() or []
        
        # Format history
        for item in history:
            item['score'] = float(item.get('score')) if item.get('score') is not None else None
            item['date'] = str(item.get('date')) if item.get('date') else ''
            item['disorder_type'] = item.get('disorder_type') or 'General'
            item['risk_level'] = get_risk_level(item.get('score'))
        
        # Get quick stats
        cursor.execute('''
            SELECT COUNT(*) as total_assessments, 
                   AVG(percentage_score) as average_score
            FROM student_assessments sa
            WHERE sa.student_id = %s AND sa.status = 'completed'
        ''', (student_id,))
        stats_result = cursor.fetchone() or {}
        
        # Get disorder-wise progress
        cursor.execute('''
            SELECT at.disorder_type,
                   COUNT(*) as attempts,
                   AVG(percentage_score) as average_score
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.student_id = %s AND sa.status = 'completed'
            GROUP BY at.disorder_type
        ''', (student_id,))
        disorder_progress = cursor.fetchall() or []
        
        # Get recommendations
        recommendations = []
        try:
            cursor.execute('''
                SELECT id, disorder_type, recommendation_text as title, 
                       recommendation_details as description, created_at as date
                FROM recommendations
                WHERE student_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            ''', (student_id,))
            recommendations = cursor.fetchall() or []
        except Exception as rec_err:
            app.logger.warning('Could not query recommendations: %s', rec_err)
        
        # Format recommendations
        formatted_recs = []
        for idx, rec in enumerate(recommendations, 1):
            formatted_recs.append({
                'index': idx,
                'id': rec.get('id'),
                'title': rec.get('title') or 'Recommendation',
                'description': rec.get('description') or '',
                'disorder': rec.get('disorder_type') or 'General',
                'date': str(rec.get('date')) if rec.get('date') else '',
                'indicator': '⚠️',
                'risk_class': 'high'
            })
        
        # Build progress dict
        progress_data = {}
        for disorder_type in ['dyslexia', 'dyscalculia', 'dysgraphia']:
            progress_data[disorder_type] = {
                'attempts': 0,
                'average_score': None,
                'risk_level': '-',
                'history': []
            }
        
        for dp in disorder_progress:
            dt = (dp.get('disorder_type') or '').lower().strip()
            if dt in progress_data:
                progress_data[dt]['attempts'] = dp.get('attempts', 0)
                avg_val = float(dp.get('average_score')) if dp.get('average_score') is not None else None
                progress_data[dt]['average_score'] = avg_val
                progress_data[dt]['risk_level'] = get_risk_level(avg_val)
        
        # Get history for mini charts
        for disorder_type in ['dyslexia', 'dyscalculia', 'dysgraphia']:
            cursor.execute('''
                SELECT sa.percentage_score as score, sa.created_at as date, sa.status
                FROM student_assessments sa
                JOIN assessment_types at ON sa.assessment_id = at.id
                WHERE sa.student_id = %s AND LOWER(at.disorder_type) = %s
                  AND sa.status = 'completed'
                ORDER BY sa.created_at
            ''', (student_id, disorder_type))
            scores = cursor.fetchall() or []
            for s in scores:
                s['date'] = str(s.get('date')) if s.get('date') else ''
                s['score'] = float(s.get('score')) if s.get('score') is not None else 0
            progress_data[disorder_type]['history'] = scores
        
        cursor.close()
        conn.close()
        
        tot_assess = stats_result.get('total_assessments') or (len(history) if history else 0)
        avg_score_val = float(stats_result.get('average_score') or 0)
        
        return jsonify({
            'status': 'ok',
            'stats': {
                'total_assessments': tot_assess,
                'average_score': round(avg_score_val, 2),
                'overall_risk': get_risk_level(avg_score_val if tot_assess > 0 else None),
                'latest_disorder': recent[0].get('disorder_type', '-') if recent else '-'
            },
            'recent': recent,
            'history': history,
            'progress': progress_data,
            'recommendations': formatted_recs
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get student dashboard data')
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/student/assessment/<int:assessment_id>', methods=['GET'])
@login_required('student')
def student_assessment_details(assessment_id):
    """Get detailed information about a specific student assessment"""
    try:
        student_id = session.get('user_id')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Helper function to determine risk level
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
        
        # Get assessment with disorder type from assessment_types
        cursor.execute('''
            SELECT sa.id, at.disorder_type, sa.percentage_score as score, 
                   sa.created_at as date
            FROM student_assessments sa
            JOIN assessment_types at ON sa.assessment_id = at.id
            WHERE sa.id = %s AND sa.student_id = %s
        ''', (assessment_id, student_id))
        assessment = cursor.fetchone()
        
        if not assessment:
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'error': 'Assessment not found'}), 404
        
        # Get related recommendations
        recommendations = []
        cursor.execute('''
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'recommendations' LIMIT 1
        ''')
        has_recommendations = cursor.fetchone()
        
        if has_recommendations:
            cursor.execute('''
                SELECT recommendation_text, recommendation_details
                FROM recommendations
                WHERE student_id = %s AND disorder_type = %s
                ORDER BY created_at DESC
                LIMIT 3
            ''', (student_id, assessment['disorder_type']))
            recommendations = cursor.fetchall() or []
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'assessment': {
                'id': assessment['id'],
                'disorder_type': assessment['disorder_type'],
                'score': assessment['score'],
                'risk_level': get_risk_level(assessment['score']),
                'date': assessment['date'],
                'recommendations': [
                    {'recommendation_text': r.get('recommendation_text', r)} 
                    for r in recommendations
                ]
            }
        }), 200
        
    except Exception as e:
        app.logger.exception('Failed to get assessment details')
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/faculty-dashboard', methods=['GET'])
@login_required('faculty')
def faculty_dashboard_page():
    """Render faculty dashboard page"""
    return render_template('faculty-dashboard.html')


if __name__ == '__main__':
    # Keep debug=True for development; set to False in production
    app.run(debug=True)
