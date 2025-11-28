import sqlite3
import json
from pathlib import Path


class AdminDatabase:
    def __init__(self, db_path="events.db"):
        self.db_path = Path(db_path)
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
        if not self._has_real_event(report):
            return

        q = "INSERT INTO events(camera_id, report_json) VALUES (?, ?)"
        self.conn.execute(q, (camera_id.lower(), json.dumps(report)))
        self.conn.commit()

    def _has_real_event(self, report: dict) -> bool:
        if not isinstance(report, dict):
            return False

        events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
        return any(events.values())

    def get_events(self, camera_id=None, since=None, limit: int = 100):
        q = "SELECT id, camera_id, report_json, timestamp FROM events WHERE 1=1"
        params = []

        if camera_id:
            q += " AND lower(camera_id) = lower(?)"
            params.append(camera_id)

        if since:
            q += " AND timestamp >= ?"
            params.append(since)

        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(q, params)
        rows = cur.fetchall()

        results = []
        for row in rows:
            _, cam, report_json, ts = row
            try:
                report = json.loads(report_json)
            except Exception:
                report = {}

            results.append({
                "camera_id": cam,
                "timestamp": ts,
                "report": report
            })

        return results
