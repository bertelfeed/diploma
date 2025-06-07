import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


class Database:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.conn_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }

    def _connect(self):
        return psycopg2.connect(**self.conn_params)

    def get_calendars(self):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM sp_get_calendars()")
                rows = cur.fetchall()
                return {row['id']: row['name'] for row in rows}

    def get_calendar_colors(self):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM sp_get_calendar_colors()")
                rows = cur.fetchall()
                return {row['id']: row['color'] for row in rows}

    def get_events(self, calendar_ids):
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM sp_get_events(%s)", (calendar_ids,))
                return cur.fetchall()

    def add_event(self, data):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CALL sp_add_event(
                        %(uid)s, %(title)s, %(description)s,
                        %(start)s, %(end)s, %(location)s,
                        %(url)s, %(reminder)s, %(repeat)s,
                        %(status)s, %(type)s, %(calendar_id)s
                    )
                """, data)
                conn.commit()

    def edit_event(self, uid, data):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CALL sp_edit_event(
                        %(uid)s, %(title)s, %(description)s,
                        %(start)s, %(end)s
                    )
                """, {
                    'uid': uid,
                    'title': data['title'],
                    'description': data.get('description', ''),
                    'start': data['start'],
                    'end': data['end']
                })
                conn.commit()

    def delete_event(self, uid):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_delete_event(%s)", (uid,))
                conn.commit()

    def create_calendar(self, calendar_id, name, color):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_create_calendar(%s, %s, %s)", (calendar_id, name, color))
                conn.commit()

    def edit_calendar(self, calendar_id, name, color):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL sp_edit_calendar(%s, %s, %s)", (calendar_id, name, color))
                conn.commit()
