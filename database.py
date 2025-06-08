import psycopg2
import psycopg2.extras
from werkzeug.security import check_password_hash, generate_password_hash
import os


class Database:
    def __init__(self, dbname, user, password, host, port):
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }

    def _connect(self):
        return psycopg2.connect(**self.conn_params)

    def get_calendars(self, user_id):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM fn_get_calendars(%s)", (user_id,))
                result = cur.fetchall()
        return {row['id']: row['name'] for row in result}

    def get_calendar_colors(self, user_id):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM fn_get_calendar_colors(%s)", (user_id,))
                result = cur.fetchall()
        return {row['id']: row['color'] for row in result}

    def get_events(self, user_id, calendar_ids):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM fn_get_events(%s)", (user_id,))
                events = cur.fetchall()
        if calendar_ids:
            events = [e for e in events if str(e['calendar_id']) in calendar_ids]
        return events

    def add_event(self, event):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_add_event(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (
                                event['uid'], event['title'], event['description'], event['start'], event['end'],
                                event['location'], event['url'], event['reminder'], event['repeat'], event['status'],
                                event['type'], event['calendar_id']
                            ))
            conn.commit()

    def edit_event(self, uid, updated):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_edit_event(%s, %s, %s, %s, %s)",
                            (uid, updated['title'], updated['description'], updated['start'], updated['end']))
            conn.commit()

    def delete_event(self, uid):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_delete_event(%s)", (uid,))
            conn.commit()

    def create_calendar(self, user_id, name, color):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CALL sp_create_calendar(%s, %s, %s)",
                    (user_id, name, color)
                )
            conn.commit()

    def edit_calendar(self, calendar_id, name, color):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_edit_calendar(%s, %s, %s)", (calendar_id, name, color))
            conn.commit()

    def create_user(self, username, password):
        password_hash = generate_password_hash(password)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_create_user(%s, %s)", (username, password_hash))
            conn.commit()

    def get_user_by_username(self, username):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM fn_get_user_by_username(%s)", (username,))
                return cur.fetchone()

    def verify_user(self, username, password):
        user = self.get_user_by_username(username)
        if user:
            print(f"[DEBUG] Введённый пароль: {password}")
            print(f"[DEBUG] Хеш из базы: {user['password_hash']}")
            if check_password_hash(user['password_hash'], password):
                print("[DEBUG] password match: OK")
                return user
            else:
                print("[DEBUG] password match: FAILED")
        return None

    def create_eisenhower_task(self, user_id, title, description, deadline, quadrant):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_create_eisenhower_task(%s, %s, %s, %s, %s)",
                            (user_id, title, description, deadline, quadrant))
            conn.commit()

    def get_eisenhower_tasks(self, user_id):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM fn_get_eisenhower_tasks(%s)", (user_id,))
                return cur.fetchall()

    def update_eisenhower_task(self, task_id, title, description, deadline, quadrant, completed):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_update_eisenhower_task(%s, %s, %s, %s, %s, %s)",
                            (task_id, title, description, deadline, quadrant, completed))
            conn.commit()

    def delete_eisenhower_task(self, task_id):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_delete_eisenhower_task(%s)", (task_id,))
            conn.commit()

    def get_achievements(self, user_id):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM achievements WHERE user_id = %s", (user_id,))
                return cur.fetchall()

    def update_calendar(self, calendar_id, name, color):
        with self._connect() as conn:
            with conn.cursor() as cur:
                calendar_id = str(calendar_id)
                cur.execute(
                    "CALL sp_update_calendar(%s, %s, %s)",
                    (calendar_id, name, color)
                )
            conn.commit()
