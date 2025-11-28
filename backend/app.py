import cv2
import base64
import json
import numpy as np
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from modules.video_manager import VideoWebSocketManager
from modules.admin_events import AdminEventsManager
from modules.admin_database import AdminDatabase
from modules.detection_bridge import DetectionBridge

app = FastAPI()

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Backend FastAPI en ejecución",
        "endpoints": {
            "websocket": "/ws",
            "admin_video": "/ws/admin/video",
            "admin_events": "/ws/admin/events",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

video_manager = VideoWebSocketManager()
admin_events = AdminEventsManager()
db = AdminDatabase()
detector = DetectionBridge()


def has_real_event(report: dict) -> bool:
    if not isinstance(report, dict):
        return False

    events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
    return any(events.values())

@app.websocket("/ws")
async def ws_client(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            cam = data.get("camera_id")
            frame_b64 = data.get("frame")

            if cam not in ["camA", "camB"]:
                continue

            if not frame_b64:
                continue

            img_bytes = base64.b64decode(frame_b64)
            img_np = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

            await video_manager.broadcast_frame(cam, frame_b64)

            sketch, report = detector.run(image, cam)

            if has_real_event(report):
                db.save_event(cam, report)
                print("REPORT ENVIADO A FLET:", report)
                await admin_events.broadcast_event(report)

            await websocket.send_text("ok")

    except WebSocketDisconnect:
        print("Cámara desconectada")
    except Exception as e:
        print("Error ws_client:", e)

@app.websocket("/ws/admin/video")
async def ws_admin_video(websocket: WebSocket):
    camera = websocket.query_params.get("camera_id")

    if camera not in ["camA"]:
        await websocket.close()
        return

    await video_manager.connect(websocket, camera)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        video_manager.disconnect(websocket, camera)

@app.websocket("/ws/admin/events")
async def ws_admin_events(websocket: WebSocket):
    await admin_events.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        admin_events.disconnect(websocket)


@app.get("/admin/events")
async def list_admin_events(camera_id: Optional[str] = None, since: Optional[str] = None, limit: int = 100):
    if camera_id and camera_id.lower() not in admin_events.VALID_CAMERA_IDS:
        return {"events": []}

    events = db.get_events(camera_id=camera_id, since=since, limit=limit)
    return {"events": events}
