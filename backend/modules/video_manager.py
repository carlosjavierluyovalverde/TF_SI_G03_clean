import asyncio


class VideoWebSocketManager:
    def __init__(self):
        self.active = {
            "camA": [],
            "camB": [],
        }
        self.loops = {
            "camA": [],
            "camB": [],
        }

    async def connect(self, websocket, camera_id):
        await websocket.accept()
        loop = asyncio.get_running_loop()
        self.active[camera_id].append(websocket)
        self.loops[camera_id].append(loop)

    def disconnect(self, websocket, camera_id):
        if websocket in self.active[camera_id]:
            idx = self.active[camera_id].index(websocket)
            self.active[camera_id].pop(idx)
            try:
                self.loops[camera_id].pop(idx)
            except Exception:
                pass

    def broadcast_frame_threadsafe(self, camera_id, frame_b64):
        for ws, loop in list(zip(self.active[camera_id], self.loops[camera_id])):
            try:
                asyncio.run_coroutine_threadsafe(ws.send_text(frame_b64), loop)
            except Exception:
                self.disconnect(ws, camera_id)
