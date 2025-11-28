import sqlite3
import json
from datetime import datetime
from pathlib import Path


class AdminDatabase:
    def __init__(self, db_path="events.db"):
        self.db_path = Path(db_path)
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.session_meta = self.db_path.with_suffix(".session.json")
        self.create_table()
        self.session_start = self._load_session_start()

    def _load_session_start(self) -> str:
        """Persist a session marker so history survives restarts."""

        if self.session_meta.exists():
            try:
                data = json.loads(self.session_meta.read_text())
                ts = data.get("session_start")
                if ts:
                    return ts
            except Exception:
                pass

        earliest = self._get_earliest_timestamp()
        now = earliest or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.session_meta.write_text(json.dumps({"session_start": now}))
        except Exception:
            pass

        return now

    def _get_earliest_timestamp(self) -> str:
        try:
            cur = self.conn.execute("SELECT timestamp FROM events ORDER BY timestamp ASC LIMIT 1")
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
        except Exception:
            return ""
        return ""

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
