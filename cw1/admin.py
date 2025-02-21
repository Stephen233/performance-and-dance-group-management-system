from flask import Blueprint, render_template, session, url_for, jsonify
import mysql.connector
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

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

@admin_bp.route('/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_dashboard.html', user=session['user_name'])

@admin_bp.route('/dashboard/stats')
def get_dashboard_stats():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get total users
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role != 'admin'")
        total_users = cursor.fetchone()['total']
        
        # Get today's attendance rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as rate
            FROM attendance_records 
            WHERE attendance_date = CURDATE()
        """)
        result = cursor.fetchone()
        attendance_rate = round(result['rate'], 1) if result['rate'] is not None else 0
        
        # Get active injuries
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM injury_records 
            WHERE recovery_status IN ('not recovered', 'recovering')
        """)
        active_injuries = cursor.fetchone()['total']
        
        # Get average performance score
        cursor.execute("""
            SELECT ROUND(AVG(score), 1) as avg_score 
            FROM performance_records
            WHERE performance_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        avg_score = cursor.fetchone()['avg_score'] or 0

        # Get recent activities with correct timestamps
        cursor.execute("""
            (SELECT 
                'register' as type,
                CONCAT('New User Registration: ', u.name, ' (', u.user_id, ')') as content,
                CAST(u.created_at AS CHAR) as timestamp
            FROM users u 
            WHERE role != 'admin'
            ORDER BY u.created_at DESC
            LIMIT 1)
            
            UNION ALL
            
            (SELECT 
                'injury' as type,
                CONCAT('Injury Update: ', u.name, ' (', ir.user_id, ') - ', ir.injury_type) as content,
                CAST(ir.injury_date AS CHAR) as timestamp
            FROM injury_records ir
            JOIN users u ON ir.user_id = u.user_id
            ORDER BY ir.injury_date DESC
            LIMIT 1)
            
            UNION ALL
            
            (SELECT 
                'training' as type,
                CONCAT('Training Record Added: ', tr.training_type, ' - ', u.name) as content,
                CAST(tr.training_date AS CHAR) as timestamp
            FROM training_records tr
            JOIN users u ON tr.user_id = u.user_id
            ORDER BY tr.training_date DESC
            LIMIT 1)
            
            UNION ALL
            
            (SELECT 
                'performance' as type,
                CONCAT('Performance Update: ', performance_name) as content,
                CAST(performance_date AS CHAR) as timestamp
            FROM performance_records
            ORDER BY performance_date DESC
            LIMIT 1)
            
            ORDER BY timestamp DESC
        """)
        activities = cursor.fetchall()
        
        return jsonify({
            "stats": {
                "totalUsers": total_users,
                "attendanceRate": attendance_rate,
                "activeInjuries": active_injuries,
                "performanceScore": float(avg_score)
            },
            "recentActivities": activities
        })
        
    except mysql.connector.Error as e:
        print(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
        
    finally:
        cursor.close()
        conn.close()