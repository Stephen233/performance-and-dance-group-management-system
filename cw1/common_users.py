from flask import render_template, session, jsonify, request
import mysql.connector

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

def handle_users_information():

    if 'user_id' not in session:
        return "Access Denied", 403
    
    return render_template('common/users.html',
                         user=session['user_name'],
                         role=session['role'])

def handle_users_api():

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403
        
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian
            FROM users 
            WHERE name LIKE %s AND role != 'admin'
            ORDER BY user_id
        """, (f"%{search}%",))
    else:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian
            FROM users 
            WHERE role != 'admin'
            ORDER BY user_id
        """)
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # date format → string
    for user in users:
        user['birth_date'] = user['birth_date'].strftime('%Y-%m-%d')
    
    return jsonify({"users": users})