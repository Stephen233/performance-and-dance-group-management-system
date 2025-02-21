from flask import Blueprint, render_template, request, jsonify, session
from db_config import get_db_connection
import mysql.connector

artist_attendance_bp = Blueprint('artist_attendance', __name__)

@artist_attendance_bp.route('/api/artist/attendance')
def get_attendance():
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
        SELECT ar.*, u.name as user_name, u.role
        FROM attendance_records ar
        JOIN users u ON ar.user_id = u.user_id
        WHERE ar.user_id = %s
    """
    params = [session['user_id']]
    
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
            
        # Calculate attendance statistics
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
        
        # Calculate attendance rate
        if stats['total_records'] > 0:
            present_rate = (stats['present_count'] / stats['total_records']) * 100
            late_rate = (stats['late_count'] / stats['total_records']) * 100
            absent_rate = (stats['absent_count'] / stats['total_records']) * 100
        else:
            present_rate = late_rate = absent_rate = 0
            
        stats['present_rate'] = round(present_rate, 1)
        stats['late_rate'] = round(late_rate, 1)
        stats['absent_rate'] = round(absent_rate, 1)
        
        return jsonify({
            "records": records,
            "stats": stats
        })
        
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()