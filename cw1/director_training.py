from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector

director_training_bp = Blueprint('director_training', __name__)

@director_training_bp.route('/director/training')
def training_page():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_training.html', 
                         user=session['user_name'],
                         role='director')

@director_training_bp.route('/api/director/training')
def get_training():
    if 'user_id' not in session or session['role'] != 'director':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        user_id = request.args.get('user_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # get only artist list
        cursor.execute("SELECT user_id, name FROM users WHERE role = 'artist' ORDER BY name")
        users = cursor.fetchall()
        
        # only get artist record
        query = """
            SELECT tr.*, u.name as user_name, u.role
            FROM training_records tr
            JOIN users u ON tr.user_id = u.user_id
            WHERE u.role = 'artist'
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
        
        # execute
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # date formate
        for record in records:
            if record['training_date']:
                record['training_date'] = record['training_date'].strftime('%Y-%m-%d')
        
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