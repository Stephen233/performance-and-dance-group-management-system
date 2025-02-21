from flask import Blueprint, render_template, session, request, flash
from db_config import get_db_connection
import bcrypt

artist_bp = Blueprint('artist', __name__)

@artist_bp.route('/dashboard')
def artist_dashboard():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_dashboard.html', 
                         user=session['user_name'],
                         role='artist')

@artist_bp.route('/personal', methods=['GET', 'POST'])
def personal_information():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        new_password = request.form.get('new_password')
        guardian = request.form.get('guardian')
        
        # update
        update_fields = []
        params = []
        
        update_fields.append("phone = %s")
        params.append(phone)
        
        update_fields.append("guardian = %s")
        params.append(guardian)
        
        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            update_fields.append("password = %s")
            params.append(hashed_password.decode('utf-8'))
        
        # Construct and execute an update query
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE user_id = %s
        """
        params.append(session['user_id'])
        
        cursor.execute(query, tuple(params))
        conn.commit()
        flash('Personal information updated successfully!', 'success')
    
    # get user info
    cursor.execute("""
        SELECT name, email, birth_date, phone, user_id, role, guardian
        FROM users 
        WHERE user_id = %s
    """, (session['user_id'],))
    user_info = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('artist/artist_personal.html',
                         user=session['user_name'],
                         role='artist',
                         user_info=user_info)

@artist_bp.route('/injury', methods=['GET'])
def injury_record():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_injury.html', 
                         user=session['user_name'],
                         role='artist')

@artist_bp.route('/performance', methods=['GET'])
def performance_record():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_performance.html', 
                         user=session['user_name'],
                         role='artist')

@artist_bp.route('/training', methods=['GET'])
def training_record():
    if 'user_id' not in session or session['role'] != 'artist':
        return "Access Denied", 403
    return render_template('artist/artist_training.html', 
                         user=session['user_name'],
                         role='artist')