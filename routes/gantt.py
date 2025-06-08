from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from app_factory import db

gantt_bp = Blueprint('gantt', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@gantt_bp.route('/gantt')
@login_required
def gantt():
    return render_template('gantt.html')
