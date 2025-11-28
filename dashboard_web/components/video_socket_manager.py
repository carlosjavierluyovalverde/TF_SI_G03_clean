import threading
import websocket
import time

class VideoSocketManager:
    _instances = {}

    def __new__(cls, camera_id, url):
        if camera_id not in cls._instances:
            cls._instances[camera_id] = super(VideoSocketManager, cls).__new__(cls)
        return cls._instances[camera_id]

    def __init__(self, camera_id, url):
        if hasattr(self, "initialized"):
            return

        self.initialized = True
        self.camera_id = camera_id
        self.url = url

        self.ws = None
        self.stop = False
        self.listeners = []

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def add_listener(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notify(self, frame_b64):
        for cb in list(self.listeners):
            try:
                cb(frame_b64)
            except:
                pass

    def _run(self):
        while not self.stop:
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect(self.url)

                while not self.stop:
                    frame = self.ws.recv()
                    if frame:
                        self._notify(frame)

            except:
                time.sleep(1)
                continue

    def close(self):
        self.stop = True
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
