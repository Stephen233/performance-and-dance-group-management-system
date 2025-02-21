from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt
import requests
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = '4a2f9d837e6b1c5028f4e9x7k3m1n5p2q'

# reCAPTCHA config
RECAPTCHA_SITE_KEY = "6LeSwtUqAAAAABM5F428nAqec2QLGg8kskzVUPTl"
RECAPTCHA_SECRET_KEY = "6LeSwtUqAAAAAAe04k6EPYUeC255jfXOzoYsv9sq"

# otp config
app.config['CAPTCHA_VALID_TIME'] = timedelta(hours=24)  # otp 24 hour

DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "danceclub"
}

def get_db_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)

def verify_recaptcha(recaptcha_response):
    if not recaptcha_response:
        return False
    
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": recaptcha_response
    }
    
    response = requests.post(verify_url, data=payload)
    result = response.json()
    
    return result.get("success", False)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_admin = request.form['email'].strip().lower()
        password = request.form['password'].encode('utf-8')
        
        if email_or_admin == "admin":
            email_or_admin = "admin@danceclub.com"
        
        # Check if verification code is required
        needs_captcha = True
        if 'last_captcha_verify' in session:
            last_verify_time = session['last_captcha_verify']
            if isinstance(last_verify_time, str):
                last_verify_time = datetime.fromisoformat(last_verify_time)
            current_time = datetime.now(timezone.utc)
            if current_time - last_verify_time < app.config['CAPTCHA_VALID_TIME']:
                needs_captcha = False
        
        # if need Verify
        if needs_captcha:
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not verify_recaptcha(recaptcha_response):
                flash('Please complete the reCAPTCHA verification.', 'danger')
                return render_template('login.html', 
                                    recaptcha_site_key=RECAPTCHA_SITE_KEY,
                                    show_captcha=True)
            else:
                # success mark time
                session['last_captcha_verify'] = datetime.now(timezone.utc)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, name, password, role FROM users WHERE email = %s", 
                      (email_or_admin,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    show_captcha = True
    if 'last_captcha_verify' in session:
        last_verify_time = session['last_captcha_verify']
        if isinstance(last_verify_time, str):
            last_verify_time = datetime.fromisoformat(last_verify_time)
        current_time = datetime.now(timezone.utc)
        if current_time - last_verify_time < app.config['CAPTCHA_VALID_TIME']:
            show_captcha = False
            
    return render_template('login.html', 
                         recaptcha_site_key=RECAPTCHA_SITE_KEY,
                         show_captcha=show_captcha)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    role = session['role']
    if role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    elif role == 'director':
        return redirect(url_for('director.director_dashboard'))
    elif role == 'coach':
        return redirect(url_for('coach.coach_dashboard'))
    elif role == 'artist':
        return redirect(url_for('artist.artist_dashboard'))

    return "Invalid role"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Import blueprints
from admin import admin_bp
from director import director_bp
from coach import coach_bp
from artist import artist_bp
from admin_register import admin_register_bp
from admin_users import admin_users_bp
from forgot_password import forgot_password_bp
from admin_attendance import admin_attendance_bp
from admin_injury import admin_injury_bp
from admin_performance import admin_performance_bp
from admin_training import admin_training_bp
from common_attendance import common_attendance_bp
from director_injury import director_injury_bp
from director_performance import director_performance_bp
from director_training import director_training_bp
from artist_injury import artist_injury_bp
from artist_performance import artist_performance_bp
from artist_training import artist_training_bp
from artist_attendance import artist_attendance_bp


# Registration Blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(director_bp, url_prefix='/director')
app.register_blueprint(coach_bp, url_prefix='/coach')
app.register_blueprint(artist_bp, url_prefix='/artist')
app.register_blueprint(admin_register_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(forgot_password_bp)
app.register_blueprint(admin_attendance_bp)
app.register_blueprint(admin_injury_bp)
app.register_blueprint(admin_performance_bp)
app.register_blueprint(admin_training_bp)
app.register_blueprint(common_attendance_bp)
app.register_blueprint(director_injury_bp)
app.register_blueprint(director_performance_bp)
app.register_blueprint(director_training_bp)
app.register_blueprint(artist_injury_bp)
app.register_blueprint(artist_performance_bp)
app.register_blueprint(artist_training_bp)
app.register_blueprint(artist_attendance_bp)



if __name__ == '__main__':
    app.run(debug=True)