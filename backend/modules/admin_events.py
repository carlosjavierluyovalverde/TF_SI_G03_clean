import asyncio
import json


class AdminEventsManager:
    VALID_CAMERA_IDS = {"cama", "camb"}

    def __init__(self):
        self.connections = []
        self.loops = []

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)
        self.loops.append(asyncio.get_running_loop())

    def disconnect(self, websocket):
        if websocket in self.connections:
            idx = self.connections.index(websocket)
            self.connections.pop(idx)
            try:
                self.loops.pop(idx)
            except Exception:
                pass

    async def broadcast_event(self, report: dict):
        payload = self._normalize_report(report)

        if not payload:
            return

        await self._send_payload(payload)

    def broadcast_event_threadsafe(self, report: dict):
        payload = self._normalize_report(report)
        if not payload:
            return

        msg = json.dumps(payload)

        for ws, loop in list(zip(self.connections, self.loops)):
            try:
                print(
                    "[WS SEND]",
                    "cam=", payload.get("camera_id"),
                    "payload=", payload,
                )
                asyncio.run_coroutine_threadsafe(ws.send_text(msg), loop)
            except Exception:
                self.disconnect(ws)

    async def _send_payload(self, payload: dict):
        msg = json.dumps(payload)

        for ws in list(self.connections):
            try:
                print(
                    "[WS SEND]",
                    "cam=", payload.get("camera_id"),
                    "payload=", payload,
                )
                await ws.send_text(msg)
            except Exception:
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
