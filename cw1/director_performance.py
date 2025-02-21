from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector
from markupsafe import escape
import re
import bleach

director_performance_bp = Blueprint('director_performance', __name__)

# 定义允许的HTML标签和属性
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'li']
ALLOWED_ATTRIBUTES = {}

def sanitize_input(content):
    """清理和验证用户输入"""
    if not content:
        return ''
        
    # 1. 基本的HTML转义
    content = escape(content)
    
    # 2. 使用bleach进行额外的HTML清理
    cleaned_content = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    # 3. 长度限制
    MAX_LENGTH = 1000
    if len(cleaned_content) > MAX_LENGTH:
        cleaned_content = cleaned_content[:MAX_LENGTH]
        
    return cleaned_content

@director_performance_bp.route('/director/performance')
def performance_page():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_performance.html', 
                         user=session['user_name'],
                         role='director')

@director_performance_bp.route('/api/director/performance')
def get_performances():
    if 'user_id' not in session or session['role'] != 'director':
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
            if record['feedback']:
                record['feedback'] = sanitize_input(record['feedback'])
            
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

@director_performance_bp.route('/api/director/performance', methods=['POST'])
def add_performance():
    if 'user_id' not in session or session['role'] != 'director':
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
        # Verify that the user is an artist
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (data['user_id'],))
        user_role = cursor.fetchone()
        if not user_role or user_role[0] != 'artist':
            return jsonify({"error": "Can only add performance records for artists"}), 400
            
        # Clean feedback before saving
        cleaned_feedback = sanitize_input(data.get('feedback', ''))
            
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
            cleaned_feedback
        ))
        
        conn.commit()
        return jsonify({"message": "Performance record added successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@director_performance_bp.route('/api/director/performance/<int:performance_id>', methods=['PUT'])
def update_performance(performance_id):
    if 'user_id' not in session or session['role'] != 'director':
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
        # Verify the record belongs to an artist
        cursor.execute("""
            SELECT u.role 
            FROM performance_records pr
            JOIN users u ON pr.user_id = u.user_id
            WHERE pr.performance_id = %s
        """, (performance_id,))
        user_role = cursor.fetchone()
        if not user_role or user_role[0] != 'artist':
            return jsonify({"error": "Can only update performance records for artists"}), 400
            
        # Clean feedback before updating
        cleaned_feedback = sanitize_input(data.get('feedback', ''))
            
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
            cleaned_feedback,
            performance_id
        ))
        
        conn.commit()
        return jsonify({"message": "Performance record updated successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()

@director_performance_bp.route('/api/director/performance/<int:performance_id>', methods=['DELETE'])
def delete_performance(performance_id):
    if 'user_id' not in session or session['role'] != 'director':
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        # Verify the record belongs to an artist
        cursor.execute("""
            SELECT u.role 
            FROM performance_records pr
            JOIN users u ON pr.user_id = u.user_id
            WHERE pr.performance_id = %s
        """, (performance_id,))
        user_role = cursor.fetchone()
        if not user_role or user_role[0] != 'artist':
            return jsonify({"error": "Can only delete performance records for artists"}), 400
            
        cursor.execute("DELETE FROM performance_records WHERE performance_id = %s", (performance_id,))
        conn.commit()
        return jsonify({"message": "Performance record deleted successfully"})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()