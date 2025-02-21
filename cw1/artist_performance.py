from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector

artist_performance_bp = Blueprint('artist_performance', __name__)

@artist_performance_bp.route('/artist/performance')
def performance_page():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_performance.html', 
                         user=session['user_name'],
                         role='artist')

@artist_performance_bp.route('/api/artist/performance')
def get_performances():
    if 'user_id' not in session or session['role'] != 'artist':
        return jsonify({"error": "Unauthorized"}), 403
        
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Base query - only get current artist's records
    query = """
        SELECT pr.*, u.name as user_name, u.role
        FROM performance_records pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.user_id = %s
    """
    params = [session['user_id']]
    
    # Add date filters
    if start_date:
        query += " AND pr.performance_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND pr.performance_date <= %s"
        params.append(end_date)
    
    # Add sorting
    query += " ORDER BY pr.performance_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Format dates for JSON
        for record in records:
            record['performance_date'] = record['performance_date'].strftime('%Y-%m-%d')
        
        return jsonify({"records": records})
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()