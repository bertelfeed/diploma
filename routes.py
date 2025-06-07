from flask import render_template, request, redirect, url_for
from datetime import datetime, timedelta
from uuid import uuid4
import calendar


class Routes:
    def __init__(self, db):
        self.db = db

    def index(self):
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        selected_calendars = request.args.getlist('calendar')
        today = datetime.today()

        if not year:
            year = today.year
        if not month:
            month = today.month
        if not selected_calendars:
            selected_calendars = list(self.db.get_calendars().keys())

        active_calendar = selected_calendars[0] if selected_calendars else None
        calendars = self.db.get_calendars()
        calendar_colors = self.db.get_calendar_colors()

        cal = calendar.Calendar()
        days = list(cal.itermonthdates(year, month))
        month_name = calendar.month_name[month].capitalize()

        # Подготовим события
        raw_events = self.db.get_events(selected_calendars)
        events = {d.strftime('%Y-%m-%d'): [] for d in days}
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
                               multiday_events=[],  # пока опущено
                               datetime=datetime)

    def add_event(self):
        form = request.form
        event = {
            'uid': f'{uuid4()}@findtime.local',
            'title': form['title'],
            'description': form.get('description', ''),
            'start': datetime.strptime(form['start_datetime'], "%Y-%m-%dT%H:%M"),
            'end': datetime.strptime(form['end_datetime'], "%Y-%m-%dT%H:%M"),
            'location': form.get('location', ''),
            'url': form.get('url', ''),
            'reminder': form.get('reminder'),
            'repeat': form.get('repeat', 'none'),
            'status': 'todo',
            'type': 'task',
            'calendar_id': form['calendar']
        }
        self.db.add_event(event)
        return redirect(url_for('index'))

    def edit_event(self):
        form = request.form
        uid = form['event_uid']
        updated = {
            'title': form['title'],
            'description': form.get('description', ''),
            'start': datetime.strptime(form['start_datetime'], "%Y-%m-%dT%H:%M"),
            'end': datetime.strptime(form['end_datetime'], "%Y-%m-%dT%H:%M")
        }
        self.db.edit_event(uid, updated)
        return redirect(url_for('index'))

    def delete_event(self):
        uid = request.form['event_uid']
        self.db.delete_event(uid)
        return redirect(url_for('index'))
    def gantt_view(self):
        selected_calendars = request.args.getlist('calendar')
        calendars = self.db.get_calendars()
        calendar_colors = self.db.get_calendar_colors()

        if not selected_calendars:
            selected_calendars = list(calendars.keys())

        raw_events = self.db.get_events(selected_calendars)

        gantt_events = []
        for e in raw_events:
            start = e.get('start')
            end = e.get('end')
            if not start or not end:
                continue
            gantt_events.append({
                'uid': e['uid'],
                'title': e['title'],
                'description': e.get('description'),
                'start': start,
                'end': end,
                'calendar_id': e['calendar_id']
            })

        min_start = min((ev['start'] for ev in gantt_events), default=datetime.today())

        return render_template('gantt.html',
                               events=gantt_events,
                               calendars=calendars,
                               selected_calendars=selected_calendars,
                               calendar_colors=calendar_colors,
                               min_start=min_start)

    def kanban_view(self):
        selected_calendars = request.args.getlist('calendar')
        calendars = self.db.get_calendars()
        calendar_colors = self.db.get_calendar_colors()

        if not selected_calendars:
            selected_calendars = list(calendars.keys())

        raw_events = self.db.get_events(selected_calendars)

        kanban = {'todo': [], 'in_progress': [], 'done': []}
        for e in raw_events:
            status = e.get('status', 'todo')
            if status not in kanban:
                status = 'todo'
            kanban[status].append(e)

        return render_template('kanban.html',
                               kanban=kanban,
                               calendars=calendars,
                               selected_calendars=selected_calendars,
                               calendar_colors=calendar_colors)

    def create_calendar(self):
        form = request.form
        calendar_id = form['id']
        name = form['name']
        color = form['color']
        self.db.create_calendar(calendar_id, name, color)
        return redirect(url_for('index'))

    def edit_calendar(self):
        form = request.form
        calendar_id = form['id']
        name = form['name']
        color = form['color']
        self.db.edit_calendar(calendar_id, name, color)
        return redirect(url_for('index'))

    def export_ics(self):
        from icalendar import Calendar, Event
        from flask import Response

        cal = Calendar()
        events = self.db.get_events(list(self.db.get_calendars().keys()))

        for e in events:
            ical_event = Event()
            ical_event.add('uid', e['uid'])
            ical_event.add('summary', e['title'])
            ical_event.add('dtstart', e['start'])
            ical_event.add('dtend', e['end'])
            ical_event.add('description', e.get('description', ''))
            ical_event.add('location', e.get('location', ''))
            ical_event.add('status', e.get('status', 'CONFIRMED').upper())
            cal.add_component(ical_event)

        return Response(cal.to_ical(), mimetype='text/calendar')
