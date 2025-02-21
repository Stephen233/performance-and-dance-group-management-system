from flask import Blueprint, render_template, request, jsonify, session
import mysql.connector
from datetime import datetime

admin_attendance_bp = Blueprint('admin_attendance', __name__)

# Database configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "danceclub"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

@admin_attendance_bp.route('/admin/attendance')
def attendance_page():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_attendance.html', user=session['user_name'])

@admin_attendance_bp.route('/api/attendance')
def get_attendance():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    query = """
        SELECT ar.*, u.name as user_name, u.role
        FROM attendance_records ar
        JOIN users u ON ar.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    # Add filters
    if user_id:
        query += " AND ar.user_id = %s"
        params.append(user_id)
    
    if start_date:
        query += " AND ar.attendance_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND ar.attendance_date <= %s"
        params.append(end_date)
    
    # Add sorting
    query += " ORDER BY ar.attendance_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Format dates for JSON
        for record in records:
            record['attendance_date'] = record['attendance_date'].strftime('%Y-%m-%d')
            
        # Get all users for the filter dropdown
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

@admin_attendance_bp.route('/api/attendance', methods=['POST'])
def add_attendance():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['user_id', 'attendance_date', 'status']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO attendance_records 
            (user_id, attendance_date, status, comments)
            VALUES (%s, %s, %s, %s)
        """, (
            data['user_id'],
            data['attendance_date'],
            data['status'],
            data.get('comments', '')
        ))
        
        conn.commit()
        return jsonify({"message": "Attendance record added successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@admin_attendance_bp.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['status']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE attendance_records 
            SET status = %s,
                comments = %s
            WHERE attendance_id = %s
        """, (
            data['status'],
            data.get('comments', ''),
            attendance_id
        ))
        
        conn.commit()
        return jsonify({"message": "Attendance record updated successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@admin_attendance_bp.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM attendance_records WHERE attendance_id = %s", (attendance_id,))
        conn.commit()
        return jsonify({"message": "Attendance record deleted successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()