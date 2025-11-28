class VideoWebSocketManager:
    def __init__(self):
        self.active = {
            "camA": [],
            "camB": [],
        }

    async def connect(self, websocket, camera_id):
        await websocket.accept()
        self.active[camera_id].append(websocket)

    def disconnect(self, websocket, camera_id):
        if websocket in self.active[camera_id]:
            self.active[camera_id].remove(websocket)

    async def broadcast_frame(self, camera_id, frame_b64):
        for ws in list(self.active[camera_id]):
            try:
                await ws.send_text(frame_b64)
            except:
                self.disconnect(ws, camera_id)
