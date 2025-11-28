import json

class AdminEventsManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast_event(self, report: dict):
        payload = self._normalize_report(report)

        if not payload:
            return

        msg = json.dumps(payload)

        for ws in list(self.connections):
            try:
                await ws.send_text(msg)
            except:
                self.disconnect(ws)

    def _normalize_report(self, report: dict) -> dict:
        if not isinstance(report, dict):
            return {}

        camera_id = report.get("camera_id")
        events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}

        if not camera_id or not any(events.values()):
            return {}

        return {
            "camera_id": camera_id,
            "timestamp": report.get("timestamp"),
            "events": {k: bool(v) for k, v in events.items()}
        }
