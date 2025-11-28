import json

class AdminEventsManager:
    VALID_CAMERA_IDS = {"cama", "camb"}

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
                print(
                    "[WEBSOCKET SEND]",
                    "cam=", payload.get("camera_id"),
                    "event=", payload,
                )
                await ws.send_text(msg)
            except:
                self.disconnect(ws)

    def _normalize_report(self, report: dict) -> dict:
        if not isinstance(report, dict):
            return {}

        camera_id = str(report.get("camera_id", "")).strip().lower()
        events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
        normalized_events = {k: bool(v) for k, v in events.items()}

        has_real_events = any(normalized_events.values())
        is_valid_camera = camera_id in self.VALID_CAMERA_IDS

        if not is_valid_camera or not has_real_events:
            return {}

        return {
            "camera_id": camera_id,
            "timestamp": report.get("timestamp"),
            "events": normalized_events
        }
