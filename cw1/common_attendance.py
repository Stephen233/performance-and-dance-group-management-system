from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector

common_attendance_bp = Blueprint('common_attendance', __name__)

@common_attendance_bp.route('/<role>/attendance')
def attendance_page(role):
    if 'user_id' not in session or session['role'] != role:
        return "Access Denied", 403
        
    # Use different templates depending on the role
    if role == 'artist':
        return render_template('artist/artist_attendance.html', 
                             user=session['user_name'],
                             role=role)
    else:
        return render_template('common/attendance.html', 
                             user=session['user_name'],
                             role=role)

@common_attendance_bp.route('/api/<role>/attendance')
def get_attendance(role):
    if 'user_id' not in session or session['role'] != role:
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    if role == 'artist':
        # art search
        query = """
            SELECT ar.*, u.name as user_name, u.role
            FROM attendance_records ar
            JOIN users u ON ar.user_id = u.user_id
            WHERE ar.user_id = %s
        """
        params = [session['user_id']]
    else:
        # other search
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
    
    # Add date filters
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
            
        # Get statistics
        if role == 'artist':
            # get art attendance
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
                    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_count,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count
                FROM attendance_records
                WHERE user_id = %s
            """, [session['user_id']])
            
            stats = cursor.fetchone()
            if stats and stats['total_records'] > 0:
                stats['present_rate'] = round((stats['present_count'] / stats['total_records']) * 100, 1)
                stats['late_rate'] = round((stats['late_count'] / stats['total_records']) * 100, 1)
                stats['absent_rate'] = round((stats['absent_count'] / stats['total_records']) * 100, 1)
            else:
                stats = {
                    'total_records': 0,
                    'present_rate': 0,
                    'late_rate': 0,
                    'absent_rate': 0
                }
            
            response_data = {
                "records": records,
                "stats": stats
            }
        else:
            # Get a list of users to filter
            cursor.execute("""
                SELECT user_id, name 
                FROM users 
                WHERE role != 'admin'
                ORDER BY name
            """)
            users = cursor.fetchall()
            
            response_data = {
                "records": records,
                "users": users
            }
        
        return jsonify(response_data)
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@common_attendance_bp.route('/api/<role>/attendance', methods=['POST'])
def add_attendance(role):
    if 'user_id' not in session or session['role'] != role or role == 'artist':
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

@common_attendance_bp.route('/api/<role>/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(role, attendance_id):
    if 'user_id' not in session or session['role'] != role or role == 'artist':
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

@common_attendance_bp.route('/api/<role>/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(role, attendance_id):
    if 'user_id' not in session or session['role'] != role or role == 'artist':
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