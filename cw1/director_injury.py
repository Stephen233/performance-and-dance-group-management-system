from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector
from datetime import datetime

director_injury_bp = Blueprint('director_injury', __name__)

@director_injury_bp.route('/director/injury')
def injury_page():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_injury.html', user=session['user_name'])

@director_injury_bp.route('/api/director/injury')
def get_injuries():
    if 'user_id' not in session or session['role'] != 'director':
        return jsonify({"error": "Unauthorized"}), 403
        
    user_id = request.args.get('user_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query - exclude admin users
    query = """
        SELECT ir.*, u.name as user_name, u.role
        FROM injury_records ir
        JOIN users u ON ir.user_id = u.user_id
        WHERE u.role != 'admin'
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
            
        # Get all non-admin users for the filter dropdown
        cursor.execute("""
            SELECT user_id, name 
            FROM users 
            WHERE role != 'admin' 
            ORDER BY name
        """)
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