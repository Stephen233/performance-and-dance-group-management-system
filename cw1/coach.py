from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector
from datetime import datetime
from common_personal import handle_personal_information

coach_bp = Blueprint('coach', __name__)

# Dashboard route
@coach_bp.route('/dashboard')
def coach_dashboard():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('coach/coach_dashboard.html', 
                         user=session['user_name'],
                         role='coach')

# Personal information route
@coach_bp.route('/personal', methods=['GET', 'POST'])
def personal_information():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return handle_personal_information()

# Users information route
@coach_bp.route('/users')
def users_information():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('common/users.html', 
                         user=session['user_name'],
                         role='coach')

# Users API route
@coach_bp.route('/api/users')
def get_users():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
        
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian 
            FROM users 
            WHERE name LIKE %s AND role != 'admin'
            ORDER BY user_id
        """, (f"%{search}%",))
    else:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian 
            FROM users 
            WHERE role != 'admin'
            ORDER BY user_id
        """)
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format dates for JSON
    for user in users:
        user['birth_date'] = user['birth_date'].strftime('%Y-%m-%d')
    
    return jsonify({"users": users})

# Attendance record routes
@coach_bp.route('/attendance')
def attendance_record():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('common/attendance.html', 
                         user=session['user_name'],
                         role='coach')

@coach_bp.route('/api/attendance')
def get_attendance():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT ar.*, u.name as user_name, u.role
        FROM attendance_records ar
        JOIN users u ON ar.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    if user_id:
        query += " AND ar.user_id = %s"
        params.append(user_id)
    
    if start_date:
        query += " AND ar.attendance_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND ar.attendance_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY ar.attendance_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        for record in records:
            record['attendance_date'] = record['attendance_date'].strftime('%Y-%m-%d')
            
        cursor.execute("SELECT user_id, name FROM users WHERE role != 'admin' ORDER BY name")
        users = cursor.fetchall()
        
        return jsonify({
            "records": records,
            "users": users
        })
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

# Injury record routes
@coach_bp.route('/injury')
def injury_record():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('coach/coach_injury.html', 
                         user=session['user_name'],
                         role='coach')

@coach_bp.route('/api/injury')
def get_injuries():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT ir.*, u.name as user_name, u.role
        FROM injury_records ir
        JOIN users u ON ir.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    if user_id:
        query += " AND ir.user_id = %s"
        params.append(user_id)
    
    if start_date:
        query += " AND ir.injury_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND ir.injury_date <= %s"
        params.append(end_date)
        
    if status:
        query += " AND ir.recovery_status = %s"
        params.append(status)
    
    query += " ORDER BY ir.injury_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        for record in records:
            record['injury_date'] = record['injury_date'].strftime('%Y-%m-%d')
            
        cursor.execute("SELECT user_id, name FROM users WHERE role != 'admin' ORDER BY name")
        users = cursor.fetchall()
        
        return jsonify({
            "records": records,
            "users": users
        })
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/api/injury', methods=['POST'])
def add_injury():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['user_id', 'injury_date', 'injury_type', 'recovery_status']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO injury_records 
            (user_id, injury_date, injury_type, recovery_status, comments)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['user_id'],
            data['injury_date'],
            data['injury_type'],
            data['recovery_status'],
            data.get('comments', '')
        ))
        
        conn.commit()
        return jsonify({"message": "Injury record added successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/api/injury/<int:injury_id>', methods=['PUT'])
def update_injury(injury_id):
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['injury_type', 'recovery_status']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE injury_records 
            SET injury_type = %s,
                recovery_status = %s,
                comments = %s
            WHERE injury_id = %s
        """, (
            data['injury_type'],
            data['recovery_status'],
            data.get('comments', ''),
            injury_id
        ))
        
        conn.commit()
        return jsonify({"message": "Injury record updated successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/api/injury/<int:injury_id>', methods=['DELETE'])
def delete_injury(injury_id):
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM injury_records WHERE injury_id = %s", (injury_id,))
        conn.commit()
        return jsonify({"message": "Injury record deleted successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

# Performance record routes
@coach_bp.route('/performance')
def performance_record():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('coach/coach_performance.html', 
                         user=session['user_name'],
                         role='coach')

@coach_bp.route('/api/performance')
def get_performances():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    min_score = request.args.get('min_score', '')
    max_score = request.args.get('max_score', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query - only get artists' records
    query = """
        SELECT pr.*, u.name as user_name, u.role
        FROM performance_records pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE u.role = 'artist'
    """
    params = []
    
    # Add filters
    if user_id:
        query += " AND pr.user_id = %s"
        params.append(user_id)
    
    if start_date:
        query += " AND pr.performance_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND pr.performance_date <= %s"
        params.append(end_date)
        
    if min_score:
        query += " AND pr.score >= %s"
        params.append(int(min_score))
    
    if max_score:
        query += " AND pr.score <= %s"
        params.append(int(max_score))
    
    # Add sorting
    query += " ORDER BY pr.performance_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Format dates for JSON
        for record in records:
            record['performance_date'] = record['performance_date'].strftime('%Y-%m-%d')
            
        # Get all artists for the filter dropdown
        cursor.execute("SELECT user_id, name FROM users WHERE role = 'artist' ORDER BY name")
        users = cursor.fetchall()
        
        return jsonify({
            "records": records,
            "users": users
        })
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/training')
def training_record():
    if 'user_id' not in session or session['role'] != 'coach':
        return "Access Denied", 403
    return render_template('coach/coach_training.html', 
                         user=session['user_name'],
                         role='coach')

@coach_bp.route('/api/training')
def get_training():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        user_id = request.args.get('user_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get only artist list
        cursor.execute("SELECT user_id, name FROM users WHERE role = 'artist' ORDER BY name")
        users = cursor.fetchall()
        
        # Only get artist records
        query = """
            SELECT tr.*, u.name as user_name, u.role
            FROM training_records tr
            JOIN users u ON tr.user_id = u.user_id
            WHERE u.role = 'artist'
        """
        params = []
        
        if user_id:
            query += " AND tr.user_id = %s"
            params.append(user_id)
        
        if start_date:
            query += " AND tr.training_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND tr.training_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY tr.training_date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        for record in records:
            if record['training_date']:
                record['training_date'] = record['training_date'].strftime('%Y-%m-%d')
                
        cursor.close()
        conn.close()
        
        return jsonify({
            "records": records,
            "users": users
        })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            "error": str(e),
            "records": [],
            "users": []
        }), 500

@coach_bp.route('/api/training', methods=['POST'])
def add_training():
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['user_id', 'training_date', 'training_type', 'duration']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        duration = int(data['duration'])
        if duration <= 0:
            return jsonify({"error": "Duration must be a positive number"}), 400
    except ValueError:
        return jsonify({"error": "Duration must be a valid number"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO training_records 
            (user_id, training_date, training_type, duration, comments)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['user_id'],
            data['training_date'],
            data['training_type'],
            duration,
            data.get('comments', '')
        ))
        
        conn.commit()
        return jsonify({"message": "Training record added successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/api/training/<int:training_id>', methods=['PUT'])
def update_training(training_id):
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['training_type', 'duration']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        duration = int(data['duration'])
        if duration <= 0:
            return jsonify({"error": "Duration must be a positive number"}), 400
    except ValueError:
        return jsonify({"error": "Duration must be a valid number"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE training_records 
            SET training_type = %s,
                duration = %s,
                comments = %s
            WHERE training_id = %s
        """, (
            data['training_type'],
            duration,
            data.get('comments', ''),
            training_id
        ))
        
        conn.commit()
        return jsonify({"message": "Training record updated successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@coach_bp.route('/api/training/<int:training_id>', methods=['DELETE'])
def delete_training(training_id):
    if 'user_id' not in session or session['role'] != 'coach':
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM training_records WHERE training_id = %s", (training_id,))
        conn.commit()
        return jsonify({"message": "Training record deleted successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()