from flask import Blueprint, render_template, request, jsonify, session
import mysql.connector
import bcrypt

admin_users_bp = Blueprint('admin_users', __name__)

# database config
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

@admin_users_bp.route('/admin/users')
def users_page():
    if 'user_id' not in session or session['role'] != 'admin':
        return "Access Denied", 403
    return render_template('admin/admin_users.html', user=session['user_name'])

@admin_users_bp.route('/api/users')
def get_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian, phone 
            FROM users 
            WHERE name LIKE %s AND role != 'admin'
            ORDER BY user_id
        """, (f"%{search}%",))
    else:
        cursor.execute("""
            SELECT user_id, name, email, role, birth_date, guardian, phone 
            FROM users 
            WHERE role != 'admin'
            ORDER BY user_id
        """)
    
    users = cursor.fetchall()  # Get query results
    cursor.close()
    conn.close()
    
    # date format → string
    for user in users:
        user['birth_date'] = user['birth_date'].strftime('%Y-%m-%d')
    
    return jsonify({"users": users})

@admin_users_bp.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'email', 'role', 'birth_date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Required field is missing"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    
    try:
        # Check if the mailbox already exists (excluding the current user)
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE email = %s AND user_id != %s
        """, (data['email'], user_id))
        
        if cursor.fetchone():
            return jsonify({
                "error": "email_exists",
                "message": "This email address has been used by another user."
            }), 400
            
        # Update password if a new password was provided
        if 'password' in data and data['password']:
            hashed_password = bcrypt.hashpw(
                data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode()
            
            cursor.execute("""
                UPDATE users 
                SET name = %s, 
                    email = %s, 
                    role = %s, 
                    birth_date = %s, 
                    guardian = %s,
                    phone = %s,
                    password = %s
                WHERE user_id = %s
            """, (
                data['name'], 
                data['email'], 
                data['role'], 
                data['birth_date'],
                data.get('guardian'),
                data.get('phone'),
                hashed_password,
                user_id
            ))
        else:
            cursor.execute("""
                UPDATE users 
                SET name = %s, 
                    email = %s, 
                    role = %s, 
                    birth_date = %s, 
                    guardian = %s,
                    phone = %s
                WHERE user_id = %s
            """, (
                data['name'], 
                data['email'], 
                data['role'], 
                data['birth_date'],
                data.get('guardian'),
                data.get('phone'),
                user_id
            ))
        
        conn.commit()
        return jsonify({"message": "User information updated successfully"})
    
    except mysql.connector.Error as e:
        return jsonify({
            "error": "database_error",
            "message": "Database error, please try again later"
        }), 500
    finally:
        cursor.close()
        conn.close()

@admin_users_bp.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully"})
    except mysql.connector.Error as e:
        return jsonify({
            "error": "database_error",
            "message": "Deletion failed, please try again later"
        }), 500
    finally:
        cursor.close()
        conn.close()