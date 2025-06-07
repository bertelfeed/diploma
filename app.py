from flask import Flask
from database import Database
from routes import Routes

app = Flask(__name__)
db = Database(dbname='findtime', user='postgres', password='your_password')
routes = Routes(db)

# Подключаем маршруты
app.add_url_rule('/', 'index', routes.index)
app.add_url_rule('/add', 'add_event', routes.add_event, methods=['POST'])
app.add_url_rule('/edit', 'edit_event', routes.edit_event, methods=['POST'])
app.add_url_rule('/delete', 'delete_event', routes.delete_event, methods=['POST'])

# Остальные маршруты
app.add_url_rule('/gantt', 'gantt_view', routes.gantt_view)
app.add_url_rule('/kanban', 'kanban_view', routes.kanban_view)
app.add_url_rule('/create_calendar', 'create_calendar', routes.create_calendar, methods=['POST'])
app.add_url_rule('/edit_calendar', 'edit_calendar', routes.edit_calendar, methods=['POST'])
app.add_url_rule('/export.ics', 'export_ics', routes.export_ics)


if __name__ == '__main__':
    app.run(debug=True)
