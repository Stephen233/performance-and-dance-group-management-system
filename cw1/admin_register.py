from flask import Blueprint, request, flash, redirect, url_for, render_template, session, get_flashed_messages
import mysql.connector
import bcrypt
from datetime import datetime

# Blueprint
admin_register_bp = Blueprint('admin_register', __name__)


DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "danceclub"
}

# connect database
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def generate_user_id(role):
    # create unique user_id based on role (AT001, CH001, DR001)
    role_prefix = {
        "artist": "AT",
        "coach": "CH",
        "director": "DR"
    }

    if role not in role_prefix:
        return None  

    prefix = role_prefix[role]
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    cursor.execute(f"SELECT user_id FROM users WHERE user_id LIKE '{prefix}%' ORDER BY user_id DESC LIMIT 1")
    last_id = cursor.fetchone()

    new_num = int(last_id[0][2:]) + 1 if last_id else 1
    new_user_id = f"{prefix}{new_num:03d}"  
    cursor.close()
    conn.close()
    
    return new_user_id

@admin_register_bp.route('/admin/register', methods=['GET', 'POST'])
def register_user():
    # Register User
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        birth_date = request.form.get('birth_date', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').encode('utf-8')
        role = request.form.get('role', '').strip()
        guardian = request.form.get('guardian', '').strip() or None  # if empty，set None

        # Calculate user age
        try:
            birth_year = int(birth_date.split("-")[0])
            current_year = datetime.now().year
            age = current_year - birth_year
        except ValueError:
            flash("Invalid date of birth!", "danger")
            return redirect(url_for('admin_register.register_user'))

        # Age restriction
        if age < 7 or age > 70:
            flash("Only users aged 7-70 can register！", "danger")
            return redirect(url_for('admin_register.register_user'))

        # 🚀 7-12 岁必须填写监护人
        if 7 <= age <= 12 and not guardian:
            flash("Between 7 and 12 years old, guardian's name is required！", "danger")
            return redirect(url_for('admin_register.register_user'))

        # if age >12 set null
        if age > 12:
            guardian = None

        # Connect to the database and check if the mailbox is registered
        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed, please contact the administrator!", "danger")
            session["_flashes"] = get_flashed_messages(with_categories=True)  
            return redirect(url_for('admin_register.register_user'))

        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        email_exists = cursor.fetchone()

        if email_exists:
            flash("The email address already exists, please use another email address！", "danger")
            print("Flash message sent: The email address already exists, please use another email address！")
            session["_flashes"] = get_flashed_messages(with_categories=True)  
            cursor.close()
            conn.close()
            return redirect(url_for('admin_register.register_user'))

        # create user id
        user_id = generate_user_id(role)
        if user_id is None:
            flash("Unable to generate user ID, please try again!", "danger")
            session["_flashes"] = get_flashed_messages(with_categories=True)
            return redirect(url_for('admin_register.register_user'))

        # bcrypt
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode()

        # Insert into database
        try:
            cursor.execute('''
                INSERT INTO users (user_id, name, birth_date, email, password, role, guardian)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, name, birth_date, email, hashed_password, role, guardian))
            conn.commit()
            flash(f"User {name} successfully registered！ID: {user_id}", "success")
            print(f"Flash message sent: User {name} successfully registered！ID: {user_id}")
            session["_flashes"] = get_flashed_messages(with_categories=True)  
        except mysql.connector.Error as e:
            flash(f"Registration failed, please try again! Error: {e}", "danger")
            print(f"Flash message sent: Registration failed, please try again! Error {e}")
            session["_flashes"] = get_flashed_messages(with_categories=True)  

        cursor.close()
        conn.close()
        return redirect(url_for('admin_register.register_user'))

    # get Flash messages
    messages = session.pop("_flashes", [])  
    print(f"✅ Sending to HTML: {messages}")  
    return render_template('admin/admin_register.html', flashes=messages)
