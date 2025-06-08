from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, flash
from functools import wraps
from app_factory import db
from datetime import datetime
import calendar
import io

calendar_bp = Blueprint('calendar', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@login_required
@calendar_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # если login находится в auth.py

    user_id = session['user_id']
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    selected_calendars = request.args.getlist('calendar')
    today = datetime.today()

    if not year:
        year = today.year
    if not month:
        month = today.month
    if not selected_calendars:
        selected_calendars = list(db.get_calendars(user_id).keys())

    active_calendar = selected_calendars[0] if selected_calendars else None
    calendars = db.get_calendars(user_id)
    calendar_colors = db.get_calendar_colors(user_id)

    cal = calendar.Calendar()
    days = list(cal.itermonthdates(year, month))
    month_name = calendar.month_name[month].capitalize()

    raw_events = db.get_events(user_id, selected_calendars)
    events = {d.strftime('%Y-%m-%d'): [] for d in days}

    achievements = db.get_achievements(user_id)

    for e in raw_events:
        start = e.get('start')
        end = e.get('end')
        repeat = e.get('repeat', 'none')
        calendar_id = e.get('calendar_id')

        if not start or not end:
            continue

        start_date = start.date()
        end_date = end.date()
        span = (end_date - start_date).days

        # Однодневные
        if start_date == end_date:
            key = start_date.strftime('%Y-%m-%d')
            if key in events:
                events[key].append(e)
        # Многодневные
        else:
            for d in days:
                if start_date <= d <= end_date:
                    key = d.strftime('%Y-%m-%d')
                    if key in events:
                        events[key].append(e)

        # Повторения
        for d in days:
            d_key = d.strftime('%Y-%m-%d')
            if d_key == start_date.strftime('%Y-%m-%d'):
                continue
            if repeat == 'daily' and d >= start_date:
                events[d_key].append(e)
            elif repeat == 'weekly' and d.weekday() == start.weekday() and d >= start_date:
                events[d_key].append(e)
            elif repeat == 'monthly' and d.day == start.day and d >= start_date:
                events[d_key].append(e)
            elif repeat == 'yearly' and d.day == start.day and d.month == start.month and d >= start_date:
                events[d_key].append(e)

    return render_template('index.html',
                           days=days,
                           month=month,
                           year=year,
                           current_date=today.date(),
                           month_name=month_name,
                           events=events,
                           calendars=calendars,
                           active_calendar=active_calendar,
                           selected_calendars=selected_calendars,
                           calendar_colors=calendar_colors,
                           multiday_events=[],
                           datetime=datetime,
                           achievements=achievements,
                           )


@calendar_bp.route('/event/create', methods=['POST'])
@login_required
def create_event():
    try:
        user_id = session['user_id']
        title = request.form['title']
        start = request.form['start']
        end = request.form['end']
        location = request.form.get('location')
        calendar_id = request.form.get('calendar_id', type=int)
        description = request.form.get('description')
        repeat = request.form.get('repeat', 'none')  # если поддерживается

        db.create_event(user_id, title, start, end, location, calendar_id, description, repeat)
        return redirect(url_for('calendar.index'))

    except KeyError as e:
        flash(f"Отсутствует обязательное поле: {str(e)}", "danger")
        return redirect(url_for('calendar.index'))

    except Exception as e:
        flash(f"Ошибка при создании события: {str(e)}", "danger")
        return redirect(url_for('calendar.index'))


@calendar_bp.route('/event/edit', methods=['POST'])
@login_required
def edit_event():
    event_id = int(request.form['event_id'])
    title = request.form['title']
    start = request.form['start']
    end = request.form['end']
    location = request.form.get('location')
    calendar_id = int(request.form['calendar_id'])
    description = request.form.get('description')
    db.update_event(event_id, title, start, end, location, calendar_id, description)
    return redirect(url_for('calendar.index'))

@calendar_bp.route('/event/delete', methods=['POST'])
@login_required
def delete_event():
    event_id = int(request.form['event_id'])
    db.delete_event(event_id)
    return redirect(url_for('calendar.index'))

@calendar_bp.route('/calendar/create', methods=['POST'])
@login_required
def create_calendar():
    user_id = session['user_id']
    name = request.form['calendar_name']
    color = request.form['calendar_color']
    db.create_calendar(user_id, name, color)
    return redirect(url_for('calendar.index'))

@calendar_bp.route('/calendar/edit', methods=['POST'])
@login_required
def edit_calendar():
    calendar_id = int(request.form['calendar_id'])
    name = request.form['calendar_name']
    color = request.form['calendar_color']
    db.update_calendar(calendar_id, name, color)
    return redirect(url_for('calendar.index'))

@calendar_bp.route('/gantt')
@login_required
def gantt_view():
    user_id = session['user_id']
    events = db.get_events(user_id)
    colors = db.get_calendar_colors(user_id)
    return render_template('gantt.html', events=events, colors=colors)

@calendar_bp.route('/kanban')
@login_required
def kanban_view():
    user_id = session['user_id']
    events = db.get_events(user_id)
    return render_template('kanban.html', events=events)

