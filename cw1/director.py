from flask import Blueprint, render_template, session, jsonify
from db_config import get_db_connection
from common_personal import handle_personal_information
from common_users import handle_users_information, handle_users_api

director_bp = Blueprint('director', __name__)

@director_bp.route('/dashboard')
def director_dashboard():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_dashboard.html',
                         user=session['user_name'],
                         role='director')

@director_bp.route('/personal', methods=['GET', 'POST'])
def personal_information():
    return handle_personal_information()

@director_bp.route('/users')
def users_information():
    return handle_users_information()

@director_bp.route('/api/users')
def users_api():
    return handle_users_api()

@director_bp.route('/attendance')
def attendance_record():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('common/attendance.html', 
                         user=session['user_name'],
                         role='director')

@director_bp.route('/injury')
def injury_record():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_injury.html', 
                         user=session['user_name'],
                         role='director')

@director_bp.route('/training')
def training_record():
    if 'user_id' not in session or session['role'] != 'director':
        return "Access Denied", 403
    return render_template('director/director_training.html', 
                         user=session['user_name'],
                         role='director')