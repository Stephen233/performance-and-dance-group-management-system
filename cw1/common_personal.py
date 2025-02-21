from flask import render_template, session, request, flash, redirect, url_for
import mysql.connector
import bcrypt

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

def handle_personal_information():

    # Processing personal information

    if 'user_id' not in session:
        return "Access Denied", 403
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'danger')
        return redirect(url_for(f'{session["role"]}.{session["role"]}_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Get form data
        phone = request.form.get('phone', '').strip() or None
        new_password = request.form.get('new_password', '').strip()
        guardian = request.form.get('guardian', '').strip() or None
        
        try:
            update_fields = []
            update_values = []
            
            if phone is not None:
                update_fields.append("phone = %s")
                update_values.append(phone)
            
            if guardian is not None:
                update_fields.append("guardian = %s")
                update_values.append(guardian)
            
            if new_password:
                # Encrypt New Password
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                update_fields.append("password = %s")
                update_values.append(hashed_password.decode('utf-8'))
            
            if update_fields:
                # Construct and execute an update query
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
                update_values.append(session['user_id'])
                
                cursor.execute(update_query, update_values)
                conn.commit()
                flash('Information updated successfully!', 'success')
            
        except mysql.connector.Error as e:
            conn.rollback()
            flash(f'Error updating information: {str(e)}', 'danger')
    
    # ger user info
    try:
        cursor.execute("""
            SELECT user_id, name, email, phone, role, birth_date, guardian
            FROM users WHERE user_id = %s
        """, (session['user_id'],))
        user_info = cursor.fetchone()
        
    except mysql.connector.Error as e:
        flash(f'Error fetching user information: {str(e)}', 'danger')
        user_info = None
    
    cursor.close()
    conn.close()
    
    return render_template('common/personal.html',
                         user=session['user_name'],
                         role=session['role'],
                         user_info=user_info)