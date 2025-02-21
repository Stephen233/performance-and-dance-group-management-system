from flask import Blueprint, render_template, request, jsonify, session
import mysql.connector
from datetime import datetime

admin_performance_bp = Blueprint('admin_performance', __name__)

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

@admin_performance_bp.route('/admin/performance')
def performance_page():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_performance.html', user=session['user_name'])

@admin_performance_bp.route('/api/performance')
def get_performances():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')
    min_score = request.args.get('min_score', '')
    max_score = request.args.get('max_score', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    query = """
        SELECT pr.*, u.name as user_name, u.role
        FROM performance_records pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE 1=1
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
        
    if search:
        query += " AND (pr.performance_name LIKE %s OR pr.location LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
        
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

@admin_performance_bp.route('/api/performance', methods=['POST'])
def add_performance():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['user_id', 'performance_date', 'performance_name', 'location', 'score']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    if not 1 <= int(data['score']) <= 5:
        return jsonify({"error": "Score must be between 1 and 5"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO performance_records 
            (user_id, performance_date, performance_name, location, score, feedback)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['user_id'],
            data['performance_date'],
            data['performance_name'],
            data['location'],
            data['score'],
            data.get('feedback', '')
        ))
        
        conn.commit()
        return jsonify({"message": "Performance record added successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@admin_performance_bp.route('/api/performance/<int:performance_id>', methods=['PUT'])
def update_performance(performance_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    required_fields = ['performance_name', 'location', 'score']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    if not 1 <= int(data['score']) <= 5:
        return jsonify({"error": "Score must be between 1 and 5"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE performance_records 
            SET performance_name = %s,
                location = %s,
                score = %s,
                feedback = %s
            WHERE performance_id = %s
        """, (
            data['performance_name'],
            data['location'],
            data['score'],
            data.get('feedback', ''),
            performance_id
        ))
        
        conn.commit()
        return jsonify({"message": "Performance record updated successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@admin_performance_bp.route('/api/performance/<int:performance_id>', methods=['DELETE'])
def delete_performance(performance_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM performance_records WHERE performance_id = %s", (performance_id,))
        conn.commit()
        return jsonify({"message": "Performance record deleted successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()