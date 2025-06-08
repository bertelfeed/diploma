from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from app_factory import db

eisenhower_bp = Blueprint('eisenhower', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@eisenhower_bp.route('/eisenhower')
@login_required
def eisenhower():
    user_id = session['user_id']
    tasks = db.get_eisenhower_tasks(user_id)
    return render_template('eisenhower.html', tasks=tasks)

@eisenhower_bp.route('/eisenhower/create', methods=['POST'])
@login_required
def create_task():
    user_id = session['user_id']
    title = request.form['title']
    description = request.form.get('description', '')
    deadline = request.form.get('deadline') or None
    quadrant = int(request.form['quadrant'])
    db.create_eisenhower_task(user_id, title, description, deadline, quadrant)
    return redirect(url_for('eisenhower.eisenhower'))

@eisenhower_bp.route('/eisenhower/update', methods=['POST'])
@login_required
def update_task():
    task_id = int(request.form['task_id'])
    is_done = request.form.get('is_done') == 'True'
    tasks = db.get_eisenhower_tasks(session['user_id'])
    task = next((t for t in tasks if t['id'] == task_id), None)
    if task:
        db.update_eisenhower_task(
            task_id,
            task['title'],
            task['description'],
            task['deadline'],
            task['quadrant'],
            is_done
        )
    return redirect(url_for('eisenhower.eisenhower'))

@eisenhower_bp.route('/eisenhower/delete', methods=['POST'])
@login_required
def delete_task():
    task_id = int(request.form['task_id'])
    db.delete_eisenhower_task(task_id)
    return redirect(url_for('eisenhower.eisenhower'))
