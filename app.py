from flask import Flask, Response, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import calendar
from uuid import uuid4
from slugify import slugify
from collections import defaultdict
from math import floor


app = Flask(__name__)

EVENTS = {
    'work': {
        '2025-05-21': [
            {'title': 'Совещание', 'time': '10:00'}
        ]
    },
    'home': {
        '2025-05-21': [
            {'title': 'Поход в магазин', 'time': '18:00'}
        ]
    }
}

CALENDARS = {
    'work': 'Рабочий',
    'home': 'Домашний'
}

CALENDAR_COLORS = {
    'work': '#0d6efd',
    'home': '#198754'
}



@app.template_filter('format_date')
def format_date(value):
    return value.strftime('%d.%m.%Y')

def get_month_days(year, month):
    cal = calendar.Calendar()
    return list(cal.itermonthdates(year, month))


@app.route('/')
def index():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    selected_calendars = request.args.getlist('calendar')
    today = datetime.today()

    if not year:
        year = today.year
    if not month:
        month = today.month
    if not selected_calendars:
        selected_calendars = list(EVENTS.keys())

    active_calendar = selected_calendars[0] if selected_calendars else None
    days = get_month_days(year, month)
    month_name = calendar.month_name[month].capitalize()

    # Подготовка словаря событий на каждый день
    events = {d.strftime('%Y-%m-%d'): [] for d in days}

    for cal_id in selected_calendars:
        cal_events = EVENTS.get(cal_id, {})
        for date_str, evlist in cal_events.items():
            for event in evlist:
                start_str = event.get('start')
                end_str = event.get('end')
                if not start_str or not end_str:
                    continue

                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
                end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")

                repeat = event.get('repeat', 'none')
                event_copy = event.copy()
                event_copy['calendar_id'] = cal_id

                # Многодневные события: добавим в каждый день диапазона
                delta_days = (end_dt.date() - start_dt.date()).days
                for i in range(delta_days + 1):
                    day = start_dt.date() + timedelta(days=i)
                    day_key = day.strftime('%Y-%m-%d')
                    if day_key in events:
                        repeated = event.copy()
                        repeated['calendar_id'] = cal_id
                        events[day_key].append(repeated)

                # Повторяющиеся события (однодневные)
                if repeat != 'none':
                    for d in days:
                        d_key = d.strftime('%Y-%m-%d')
                        if d_key == start_dt.strftime('%Y-%m-%d'):
                            continue

                        add_event = False
                        if repeat == 'daily' and d >= start_dt.date():
                            add_event = True
                        elif repeat == 'weekly' and d >= start_dt.date() and d.weekday() == start_dt.weekday():
                            add_event = True
                        elif repeat == 'monthly' and d >= start_dt.date() and d.day == start_dt.day:
                            add_event = True
                        elif repeat == 'yearly' and d >= start_dt.date() and d.day == start_dt.day and d.month == start_dt.month:
                            add_event = True

                        if add_event and d_key in events:
                            repeated = event.copy()
                            repeated['calendar_id'] = cal_id
                            events[d_key].append(repeated)

    # Многодневные события с координатами
    multiday_events = []
    multiday_day_levels = defaultdict(int)

    for cal_id in selected_calendars:
        cal_events = EVENTS.get(cal_id, {})
        for evlist in cal_events.values():
            for e in evlist:
                if 'start' in e and 'end' in e:
                    start_dt = datetime.strptime(e['start'], "%Y-%m-%dT%H:%M")
                    end_dt = datetime.strptime(e['end'], "%Y-%m-%dT%H:%M")
                    if (end_dt.date() - start_dt.date()).days < 1:
                        continue

                    # только дни, попавшие в отображаемый месяц
                    span_days = [d for d in days if start_dt.date() <= d <= end_dt.date()]
                    if not span_days:
                        continue

                    # разбиваем на недели
                    week_spans = defaultdict(list)
                    for d in span_days:
                        week = floor(days.index(d) / 7)
                        week_spans[week].append(d)

                    for week_index, week_days in week_spans.items():
                        first_day = week_days[0]
                        last_day = week_days[-1]

                        grid_column = (first_day.weekday() + 1) if first_day.weekday() < 6 else 7
                        span = len(week_days)
                        grid_row = week_index + 2  # +1 за заголовки, +1 для base-индексации

                        level = multiday_day_levels[first_day]
                        multiday_day_levels[first_day] += 1

                        multiday_events.append({
                            'title': e['title'],
                            'calendar_id': cal_id,
                            'start': e['start'],
                            'end': e['end'],
                            'grid_start': grid_column,
                            'grid_row': grid_row,
                            'span': span,
                            'level': level
                        })

    return render_template('index.html',
                           days=days,
                           month=month,
                           year=year,
                           current_date=today.date(),
                           month_name=month_name,
                           events=events,
                           calendars=CALENDARS,
                           active_calendar=active_calendar,
                           selected_calendars=selected_calendars,
                           calendar_colors=CALENDAR_COLORS,
                           multiday_events=multiday_events,
                           datetime=datetime)



@app.route('/add', methods=['POST'])
def add_event():
    calendar_id = request.form['calendar']
    title = request.form['title']
    start_dt = request.form['start_datetime']
    end_dt = request.form['end_datetime']
    location = request.form.get('location', '')
    description = request.form.get('description', '')
    reminder = request.form.get('reminder')  # в минутах
    url = request.form.get('url', '')
    repeat = request.form.get('repeat', 'none')

    start_date = start_dt.split("T")[0]

    event = {
        'uid': f'{uuid4()}@findtime.local',
        'title': title,
        'start': start_dt,
        'end': end_dt,
        'location': location,
        'description': description,
        'reminder': reminder,
        'url': url,
        'repeat': repeat,
        'type': 'task',  # 👈 новое поле
        'status': 'todo'  # 👈 новое поле для Kanban
    }

    EVENTS.setdefault(calendar_id, {}).setdefault(start_date, []).append(event)

    dt = datetime.strptime(start_date, '%Y-%m-%d')
    return redirect(url_for('index', year=dt.year, month=dt.month, calendar=calendar_id))


@app.route('/delete', methods=['POST'])
def delete_event():
    uid = request.form.get('event_uid')
    calendar_id = request.form.get('calendar', 'work')

    found = False
    for date, evlist in EVENTS.get(calendar_id, {}).items():
        for idx, event in enumerate(evlist):
            if event.get('uid') == uid:
                evlist.pop(idx)
                if not evlist:
                    del EVENTS[calendar_id][date]
                found = True
                dt = datetime.strptime(date, '%Y-%m-%d')
                break
        if found:
            break

    if not found:
        dt = datetime.today()

    return redirect(url_for('index', year=dt.year, month=dt.month, calendar=calendar_id))


@app.route('/edit', methods=['POST'])
def edit_event():
    uid = request.form.get('event_uid')
    calendar_id = request.form.get('calendar', 'work')

    # Поиск события по uid
    found = False
    for date, evlist in EVENTS.get(calendar_id, {}).items():
        for idx, event in enumerate(evlist):
            if event.get('uid') == uid:
                # Обновление полей
                event['title'] = request.form.get('title')
                event['description'] = request.form.get('description', '')
                start = request.form.get('start_datetime')
                end = request.form.get('end_datetime')
                if start: event['start'] = start
                if end: event['end'] = end

                found = True
                dt = datetime.strptime(date, '%Y-%m-%d')
                break
        if found:
            break

    if not found:
        dt = datetime.today()

    return redirect(url_for('index', year=dt.year, month=dt.month, calendar=calendar_id))


def generate_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//FindTime Calendar//RU",
        "CALSCALE:GREGORIAN"
    ]

    for date, items in events.items():
        for e in items:
            # Автогенерация UID, если нет
            uid = e.get('uid') or f"{uuid4()}@findtime.local"

            # Если есть start/end — используем их
            start = e.get('start')
            end = e.get('end')

            # Если нет — генерируем из date + time
            if not start and 'time' in e:
                start_time = datetime.strptime(f"{date} {e['time']}", "%Y-%m-%d %H:%M")
                end_time = start_time + timedelta(hours=1)
                start = start_time.strftime("%Y%m%dT%H%M%S")
                end = end_time.strftime("%Y%m%dT%H%M%S")
            elif start and end:
                start = start.replace("-", "").replace(":", "")
                end = end.replace("-", "").replace(":", "")

            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART:{start}",
                f"DTEND:{end}",
                f"SUMMARY:{e['title']}",
                f"DESCRIPTION:{e.get('description', '')}",
                "END:VEVENT"
            ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)

@app.route('/export.ics')
def export_ics():
    ics_content = generate_ics(EVENTS)
    return Response(ics_content, mimetype="text/calendar", headers={
        "Content-Disposition": "attachment; filename=calendar.ics"
    })

@app.route('/create_calendar', methods=['POST'])
def create_calendar():
    name = request.form.get('calendar_name')
    color = request.form.get('calendar_color', '#0d6efd')

    if not name:
        return redirect(url_for('index'))

    calendar_id = slugify(name.lower()).replace('-', '_')
    if calendar_id in CALENDARS:
        # имя уже существует — просто выбираем его
        pass
    else:
        CALENDARS[calendar_id] = name
        CALENDAR_COLORS[calendar_id] = color
        EVENTS[calendar_id] = {}

    return redirect(url_for('index', calendar=calendar_id))

@app.route('/edit_calendar', methods=['POST'])
def edit_calendar():
    calendar_id = request.form.get('calendar_id')
    new_name = request.form.get('calendar_name')
    new_color = request.form.get('calendar_color')
    selected_calendars = request.form.getlist('calendar')

    if calendar_id and calendar_id in CALENDARS:
        if new_name:
            CALENDARS[calendar_id] = new_name
        if new_color:
            CALENDAR_COLORS[calendar_id] = new_color

    # month/year можно взять как query или по умолчанию
    today = datetime.today()
    year = request.args.get('year', type=int, default=today.year)
    month = request.args.get('month', type=int, default=today.month)

    return redirect(url_for('index', year=year, month=month, calendar=selected_calendars))

@app.route('/kanban')
def kanban_view():
    selected_calendars = request.args.getlist('calendar') or list(EVENTS.keys())
    tasks = []

    for cal_id in selected_calendars:
        for date, evlist in EVENTS.get(cal_id, {}).items():
            for e in evlist:
                if e.get('type') == 'task':
                    e_copy = e.copy()
                    e_copy['calendar_id'] = cal_id
                    e_copy['date'] = date
                    tasks.append(e_copy)

    return render_template('kanban.html', tasks=tasks, calendars=CALENDARS,
                           selected_calendars=selected_calendars,
                           calendar_colors=CALENDAR_COLORS)

@app.route('/gantt')
def gantt_view():
    selected_calendars = request.args.getlist('calendar') or list(EVENTS.keys())
    gantt_events = []

    for cal_id in selected_calendars:
        for date, evlist in EVENTS.get(cal_id, {}).items():
            for e in evlist:
                start_str = e.get('start') or f"{date}T{e.get('time', '00:00')}"
                end_str = e.get('end') or start_str

                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
                end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")

                gantt_events.append({
                    'uid': e.get('uid'),
                    'title': e['title'],
                    'start': start_dt,
                    'end': end_dt,
                    'calendar_id': cal_id
                })

    # Определим минимальную дату для выравнивания
    if gantt_events:
        min_start = min(ev['start'] for ev in gantt_events)
    else:
        min_start = datetime.today()

    return render_template('gantt.html',
                           events=gantt_events,
                           calendars=CALENDARS,
                           selected_calendars=selected_calendars,
                           calendar_colors=CALENDAR_COLORS,
                           min_start=min_start)




if __name__ == '__main__':
    app.run(debug=True)
