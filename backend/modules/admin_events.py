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

    async def broadcast_event(self, camera_id, report):
        if isinstance(report, str):
            try:
                report = json.loads(report)
            except:
                report = {}

        if not isinstance(report, dict):
            report = {}

        msg = json.dumps({
            "camera_id": camera_id,
            "report": report
        })

        for ws in list(self.connections):
            try:
                await ws.send_text(msg)
            except:
                self.disconnect(ws)
