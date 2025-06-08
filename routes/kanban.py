from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from app_factory import db


kanban_bp = Blueprint('kanban', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@kanban_bp.route('/kanban')
@login_required
def kanban():
    return render_template('kanban.html')
