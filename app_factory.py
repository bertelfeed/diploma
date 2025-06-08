from flask import Flask
from database import Database
from dotenv import load_dotenv
import os

db = None

def create_app():
    global db
    app = Flask(__name__)

    # Загрузка переменных окружения
    load_dotenv()

    # Секретный ключ для сессий
    app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

    # Инициализация подключения к PostgreSQL
    db = Database(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    # Регистрация маршрутов (Blueprints)
    from routes.calendar import calendar_bp
    from routes.eisenhower import eisenhower_bp
    # from routes.gantt import gantt_bp
    # from routes.kanban import kanban_bp

    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    app.register_blueprint(calendar_bp)
    app.register_blueprint(eisenhower_bp)
    # app.register_blueprint(gantt_bp)
    # app.register_blueprint(kanban_bp)

    return app
