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
        self.session_file = self.db_path.with_name(".session_start")
        self.create_table()
        self.session_start = self._init_session()

    def _init_session(self) -> str:
        """Create a fresh session marker on backend start and persist it."""

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # New backend start: wipe previous temporary events and persist marker
        try:
            self._reset_events()
        except Exception:
            # If deletion fails, continue with current data but log via comment
            # to make the missing cleanup explicit.
            pass

        try:
            self.session_file.write_text(now)
        except Exception:
            pass

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

    def _reset_events(self):
        self.conn.execute("DELETE FROM events")
        self.conn.commit()

    def save_event(self, camera_id, report):
        if not self._has_real_event(report):
            return

        q = "INSERT INTO events(camera_id, report_json) VALUES (?, ?)"
        self.conn.execute(q, (camera_id.lower(), json.dumps(report)))
        self.conn.commit()
        print(
            "[EVENT STORED]",
            "camera=", camera_id,
            "timestamp=", report.get("timestamp"),
            "payload=", report,
        )

    def _has_real_event(self, report: dict) -> bool:
        if not isinstance(report, dict):
            return False

        events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
        return any(events.values())

    def get_events(self, camera_id=None, since=None, limit: int = 100):
        q = "SELECT id, camera_id, report_json, timestamp FROM events WHERE 1=1"
        params = []

        effective_since = since or self.session_start

        if camera_id:
            q += " AND lower(camera_id) = lower(?)"
            params.append(camera_id)

        if effective_since:
            q += " AND timestamp >= ?"
            params.append(effective_since)

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
