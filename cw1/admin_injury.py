from flask import Blueprint, render_template, request, jsonify, session
import mysql.connector
from datetime import datetime

admin_injury_bp = Blueprint('admin_injury', __name__)

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

@admin_injury_bp.route('/admin/injury')
def injury_page():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_injury.html', user=session['user_name'])

@admin_injury_bp.route('/api/injury')
def get_injuries():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    query = """
        SELECT ir.*, u.name as user_name, u.role
        FROM injury_records ir
        JOIN users u ON ir.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    # Add filters
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
    
    # Add sorting
    query += " ORDER BY ir.injury_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Format dates for JSON
        for record in records:
            record['injury_date'] = record['injury_date'].strftime('%Y-%m-%d')
            
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

@admin_injury_bp.route('/api/injury', methods=['POST'])
def add_injury():
    if 'user_id' not in session or session['role'] != 'admin':
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

@admin_injury_bp.route('/api/injury/<int:injury_id>', methods=['PUT'])
def update_injury(injury_id):
    if 'user_id' not in session or session['role'] != 'admin':
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

@admin_injury_bp.route('/api/injury/<int:injury_id>', methods=['DELETE'])
def delete_injury(injury_id):
    if 'user_id' not in session or session['role'] != 'admin':
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