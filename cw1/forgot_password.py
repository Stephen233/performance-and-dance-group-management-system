from flask import Blueprint, render_template, request, jsonify, url_for, redirect
import mysql.connector
import bcrypt
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import jwt

forgot_password_bp = Blueprint('forgot_password', __name__)

# JWT key
JWT_SECRET = '4a2f9d837e6b1c5028f4e9x7k3m1n5p2q'

DATABASE_CONFIG = {
   "host": "localhost",
   "user": "root", 
   "password": "",
   "database": "danceclub"
}

# mail config
EMAIL_CONFIG = {
   "SMTP_SERVER": "smtp.gmail.com",
   "SMTP_PORT": 587,
   "SENDER_EMAIL": "danceclubtest@gmail.com",
   "SENDER_PASSWORD": "udrh dbgg nbaa iawu"
}

def get_db_connection():
   try:
       conn = mysql.connector.connect(**DATABASE_CONFIG)
       return conn
   except mysql.connector.Error as e:
       print(f"Database connection error: {e}")
       return None

def generate_otp():
   # Generate 6 digit OTP
   return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
   # send
   try:
       msg = MIMEMultipart()
       msg['From'] = EMAIL_CONFIG['SENDER_EMAIL']
       msg['To'] = email
       msg['Subject'] = "Reset Password Verification Code"
       
       body = f"""
       Your OTP: {otp}
       
       This verification code will be valid for 10 minutes.
       If this is not your action, please ignore this email.
       """
       
       msg.attach(MIMEText(body, 'plain'))
       
       server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
       server.starttls()
       server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['SENDER_PASSWORD'])
       server.send_message(msg)
       server.quit()
       return True
   except Exception as e:
       print(f"Error sending email: {e}")
       return False

@forgot_password_bp.route('/forgot-password')
def forgot_password_page():
   return render_template('password/forgot_password.html')

@forgot_password_bp.route('/verify-otp')
def verify_otp_page():
   return render_template('password/verify_otp.html')

@forgot_password_bp.route('/reset-password')
def reset_password_page():
   return render_template('password/reset_password.html')

@forgot_password_bp.route('/api/send-otp', methods=['POST'])
def send_otp():
   email = request.json.get('email', '').strip().lower()
   
   if not email:
       return jsonify({"error": "Please enter your email address"}), 400
       
   conn = get_db_connection()
   if conn is None:
       return jsonify({"error": "Server Error"}), 500
       
   cursor = conn.cursor()
   
   try:
       # Verify that the mailbox exists
       cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
       user = cursor.fetchone()
       
       if not user:
           return jsonify({"error": "This email address is not registered"}), 404
           
       # Generate OTP and store it
       otp = generate_otp()
       expiry_time = datetime.now() + timedelta(minutes=10)
       
       try:
           cursor.execute("""
               INSERT INTO password_resets (email, otp, expiry_time)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE
               otp = VALUES(otp),
               expiry_time = VALUES(expiry_time),
               used = 0
           """, (email, otp, expiry_time))
           
           conn.commit()
       except mysql.connector.Error as e:
           print(f"Database Error: {e}")
           return jsonify({"error": "Database Error"}), 500
       
       # send otp
       if send_otp_email(email, otp):
           return jsonify({"message": "The verification code has been sent to your email"})
       else:
           return jsonify({"error": "Failed to send verification code"}), 500
           
   except mysql.connector.Error as e:
       return jsonify({"error": "Database Error"}), 500
   finally:
       cursor.close()
       conn.close()

@forgot_password_bp.route('/api/verify-otp', methods=['POST'])
def verify_otp():
   email = request.json.get('email')
   otp = request.json.get('otp')
   
   conn = get_db_connection()
   cursor = conn.cursor()
   
   try:
       cursor.execute("""
           SELECT * FROM password_resets 
           WHERE email = %s AND otp = %s AND expiry_time > NOW()
           AND used = 0
       """, (email, otp))
       
       reset_record = cursor.fetchone()
       if not reset_record:
           return jsonify({"error": "The verification code is invalid or has expired"}), 400
           
       # Generate a reset token
       token = jwt.encode({
           'email': email,
           'exp': datetime.utcnow() + timedelta(minutes=10)
       }, JWT_SECRET, algorithm='HS256')
       
       return jsonify({"token": token})
       
   finally:
       cursor.close()
       conn.close()

@forgot_password_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
   email = request.json.get('email')
   token = request.json.get('token')
   new_password = request.json.get('new_password')
   
   try:
       # Verify Token
       decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
       if decoded['email'] != email:
           return jsonify({"error": "Invalid request"}), 400
           
       conn = get_db_connection()
       cursor = conn.cursor()
       
       try:
           # mark otp used
           cursor.execute("""
               UPDATE password_resets SET used = 1 
               WHERE email = %s AND used = 0
           """, (email,))
           
           # update password
           hashed_password = bcrypt.hashpw(
               new_password.encode(), 
               bcrypt.gensalt()
           ).decode()
           
           cursor.execute("""
               UPDATE users SET password = %s 
               WHERE email = %s
           """, (hashed_password, email))
           
           conn.commit()
           return jsonify({"message": "Password reset successful"})
           
       finally:
           cursor.close()
           conn.close()
           
   except jwt.ExpiredSignatureError:
       return jsonify({"error": "Reset link has expired"}), 400
   except jwt.InvalidTokenError:
       return jsonify({"error": "Invalid reset link"}), 400