import sqlite3
import json


class AdminDatabase:
    def __init__(self, db_path="events.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        q = """
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            report_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.conn.execute(q)
        self.conn.commit()

    def save_event(self, camera_id, report):
        q = "INSERT INTO events(camera_id, report_json) VALUES (?, ?)"
        self.conn.execute(q, (camera_id, json.dumps(report)))
        self.conn.commit()
