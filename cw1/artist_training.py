from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector

artist_training_bp = Blueprint('artist_training', __name__)

@artist_training_bp.route('/artist/training')
def training_page():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_training.html', 
                         user=session['user_name'],
                         role='artist')

@artist_training_bp.route('/api/artist/training')
def get_training():
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
        SELECT tr.*, u.name as user_name
        FROM training_records tr
        JOIN users u ON tr.user_id = u.user_id
        WHERE tr.user_id = %s
    """
    params = [session['user_id']]
    
    # Add date filters
    if start_date:
        query += " AND tr.training_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND tr.training_date <= %s"
        params.append(end_date)
    
    # Add sorting
    query += " ORDER BY tr.training_date DESC"
    
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Format dates for JSON
        for record in records:
            record['training_date'] = record['training_date'].strftime('%Y-%m-%d')
        
        # Get training statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trainings,
                SUM(duration) as total_duration,
                AVG(duration) as average_duration,
                COUNT(DISTINCT training_type) as training_types
            FROM training_records
            WHERE user_id = %s
        """, [session['user_id']])
        
        stats = cursor.fetchone()
        
        return jsonify({
            "records": records,
            "stats": stats
        })
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()