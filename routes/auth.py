from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app_factory import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.get_user_by_username(username)

        if user:
            password_hash = user['password_hash']
            if check_password_hash(password_hash, password):
                session['user_id'] = user['id']
                return redirect(url_for('calendar.index'))
            else:
                flash('Неверный пароль.')
        else:
            flash('Пользователь не найден.')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = db.get_user_by_username(username)

        if existing_user:
            flash('Пользователь уже существует.')
        else:
            db.create_user(username, password)
            flash('Регистрация успешна! Войдите в систему.')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
