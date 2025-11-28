import json
import threading
import time
import websocket


class EventSocketManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventSocketManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return

        self.initialized = True
        self.ws = None
        self.stop = False
        self.listeners = []
        self.events = []

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def add_listener(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def get_events(self):
        return list(self.events)

    def _notify(self, event_data: dict):
        for cb in list(self.listeners):
            try:
                cb(event_data)
            except Exception:
                pass

    def _normalize_event(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return {}

        camera_id = str(data.get("camera_id", "")).strip().lower()
        events = data.get("events", {}) if isinstance(data.get("events", {}), dict) else {}
        active = {k: bool(v) for k, v in events.items() if bool(v)}

        if not camera_id or not active:
            return {}

        return {
            "camera_id": camera_id,
            "timestamp": data.get("timestamp", "-"),
            "events": active,
        }

    def _run(self):
        url = "ws://127.0.0.1:8000/ws/admin/events"
        print("[WS OPEN]", "cam=all")

        while not self.stop:
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect(url)

                while not self.stop:
                    msg = self.ws.recv()
                    if not msg:
                        continue

                    try:
                        data = json.loads(msg)
                    except Exception:
                        continue

                    event = self._normalize_event(data)
                    if not event:
                        continue

                    print("[WS MESSAGE RECEIVED]", "cam=", event.get("camera_id"), "payload=", event)
                    self.events.insert(0, event)
                    self.events = self.events[:50]
                    self._notify(event)

            except Exception:
                time.sleep(1)
                continue

    def close(self):
        self.stop = True
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
