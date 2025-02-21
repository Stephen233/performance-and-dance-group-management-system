from flask import Blueprint, render_template, request, jsonify, session
import mysql.connector
from datetime import datetime

admin_training_bp = Blueprint('admin_training', __name__)

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

@admin_training_bp.route('/admin/training')
def training_page():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_training.html', user=session['user_name'])

@admin_training_bp.route('/api/training')
def get_training():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        user_id = request.args.get('user_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # get user list
        cursor.execute("SELECT user_id, name FROM users WHERE role != 'admin' ORDER BY name")
        users = cursor.fetchall()
        print("DEBUG: Users data:", [{"user_id": user['user_id'], "name": user['name']} for user in users])  # 详细的用户数据日志
        
        # Base query
        query = """
            SELECT tr.*, u.name as user_name, u.role
            FROM training_records tr
            JOIN users u ON tr.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if user_id:
            query += " AND tr.user_id = %s"
            params.append(user_id)
        
        if start_date:
            query += " AND tr.training_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND tr.training_date <= %s"
            params.append(end_date)
        
        # Add sorting
        query += " ORDER BY tr.training_date DESC"
        
        # Execute record query
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Date formatting
        for record in records:
            if record['training_date']:
                record['training_date'] = record['training_date'].strftime('%Y-%m-%d')
                
        print("DEBUG: Users found:", len(users))
        print("DEBUG: Records found:", len(records))
        
        response_data = {
            "records": records if records else [],
            "users": users if users else []
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            "error": str(e),
            "records": [],
            "users": []
        }), 500

@admin_training_bp.route('/api/training', methods=['POST'])
def add_training():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['user_id', 'training_date', 'training_type', 'duration']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Validate duration (must be positive integer)
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

@admin_training_bp.route('/api/training/<int:training_id>', methods=['PUT'])
def update_training(training_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['training_type', 'duration']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Validate duration (must be positive integer)
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

@admin_training_bp.route('/api/training/<int:training_id>', methods=['DELETE'])
def delete_training(training_id):
    if 'user_id' not in session or session['role'] != 'admin':
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