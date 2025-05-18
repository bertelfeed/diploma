from flask import Flask, Response, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import calendar
from uuid import uuid4
from slugify import slugify

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

                # добавляем многодневные события
                delta_days = (end_dt.date() - start_dt.date()).days
                for i in range(delta_days + 1):
                    day = start_dt.date() + timedelta(days=i)
                    day_key = day.strftime('%Y-%m-%d')
                    if day_key in events:
                        repeated = event.copy()
                        repeated['calendar_id'] = cal_id
                        events[day_key].append(repeated)

                # Повторяющиеся события (однодневные, многодневные не повторяем для простоты)
                if repeat != 'none':
                    for d in days:
                        d_key = d.strftime('%Y-%m-%d')
                        if d_key == start_dt.strftime('%Y-%m-%d'):
                            continue

                        add_event = False
                        if repeat == 'daily' and d >= start_dt.date():
                            add_event = True
                        elif repeat == 'weekly' and d >= start_dt.date():
                            if d.weekday() == start_dt.weekday():
                                add_event = True
                        elif repeat == 'monthly' and d >= start_dt.date():
                            if d.day == start_dt.day:
                                add_event = True
                        elif repeat == 'yearly' and d >= start_dt.date():
                            if d.day == start_dt.day and d.month == start_dt.month:
                                add_event = True

                        if add_event and d_key in events:
                            repeated = event.copy()
                            repeated['calendar_id'] = cal_id
                            events[d_key].append(repeated)

    multiday_events = []

    for cal_id in selected_calendars:
        cal_events = EVENTS.get(cal_id, {})
        for evlist in cal_events.values():
            for e in evlist:
                if 'start' in e and 'end' in e:
                    start_dt = datetime.strptime(e['start'], "%Y-%m-%dT%H:%M")
                    end_dt = datetime.strptime(e['end'], "%Y-%m-%dT%H:%M")
                    if (end_dt.date() - start_dt.date()).days < 1:
                        continue

                    try:
                        day_index = days.index(start_dt.date())
                    except ValueError:
                        continue  # дата не в пределах видимой сетки

                    grid_column = (day_index % 7) + 1
                    grid_row = (day_index // 7) + 2

                    print("INDEX:", day_index, "→ grid_row:", grid_row)

                    # длина полосы
                    span = sum(1 for d in days if start_dt.date() <= d <= end_dt.date())

                    multiday_events.append({
                        'title': e['title'],
                        'calendar_id': cal_id,
                        'start': e['start'],  # 👈 обязательно добавляем
                        'end': e['end'],
                        'grid_start': grid_column,
                        'grid_row': grid_row,
                        'span': span
                    })

    print("MULTIDAY:", multiday_events)

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
        'repeat': repeat
    }

    EVENTS.setdefault(calendar_id, {}).setdefault(start_date, []).append(event)

    dt = datetime.strptime(start_date, '%Y-%m-%d')
    return redirect(url_for('index', year=dt.year, month=dt.month, calendar=calendar_id))



@app.route('/delete', methods=['POST'])
def delete_event():
    date = request.form.get('event_date')
    index = int(request.form.get('event_index'))
    calendar_id = request.form.get('calendar', 'work')

    if (calendar_id in EVENTS and
            date in EVENTS[calendar_id] and
            0 <= index < len(EVENTS[calendar_id][date])):

        EVENTS[calendar_id][date].pop(index)
        # Удаляем ключ даты, если больше нет событий
        if not EVENTS[calendar_id][date]:
            del EVENTS[calendar_id][date]

    dt = datetime.strptime(date, '%Y-%m-%d')
    return redirect(url_for('index', year=dt.year, month=dt.month, calendar=calendar_id))

@app.route('/edit', methods=['POST'])
def edit_event():
    date = request.form.get('event_date')
    index = int(request.form.get('event_index'))
    title = request.form.get('title')
    time = request.form.get('time')
    calendar_id = request.form.get('calendar', 'work')

    if (calendar_id in EVENTS and
            date in EVENTS[calendar_id] and
            0 <= index < len(EVENTS[calendar_id][date])):
        EVENTS[calendar_id][date][index]['title'] = title
        EVENTS[calendar_id][date][index]['time'] = time

    dt = datetime.strptime(date, '%Y-%m-%d')
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

    calendar_id = slugify(name.lower(), separator="_")
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


if __name__ == '__main__':
    app.run(debug=True)
