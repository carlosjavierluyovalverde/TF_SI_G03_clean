import cv2
import base64
import json
import numpy as np
import asyncio
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from modules.video_manager import VideoWebSocketManager
from modules.admin_events import AdminEventsManager
from modules.admin_database import AdminDatabase
from modules.detection_bridge import DetectionBridge
from modules.video_threads import VideoThreadManager

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
db = AdminDatabase(db_path="data/events.db")
detector = DetectionBridge()
active_mode = "none"
thread_manager = VideoThreadManager(
    detector=detector,
    video_manager=video_manager,
    admin_events=admin_events,
    db=db,
    rtsp_url="rtsp://192.168.101.3:8080/h264_pcm.sdp",
)
thread_manager.stop_all()


def has_real_event(report: dict) -> bool:
    if not isinstance(report, dict):
        return False

    events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
    return any(events.values())


def switch_mode(new_mode: str):
    global active_mode
    if new_mode == active_mode:
        return {"mode": active_mode}

    print("[MODE SWITCH]", "from=", active_mode, "to=", new_mode)

    if new_mode == "camA":
        thread_manager.start_camA()
        thread_manager.stop_camB()
    elif new_mode == "camB":
        thread_manager.start_camB()
        thread_manager.stop_camA()
    elif new_mode == "multi":
        thread_manager.start_multi()
    else:
        thread_manager.stop_all()
        new_mode = "none"

    active_mode = new_mode
    return {"mode": active_mode}

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
                report = dict(report)
                report["camera_id"] = cam.lower()
                if not report.get("timestamp"):
                    report = dict(report)
                    report["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                print(
                    "[CAMERA EVENT RECEIVED]",
                    "cam=", cam,
                    "payload=", report,
                )
                db.save_event(cam, report)
                await admin_events.broadcast_event(report)

            await websocket.send_text("ok")

    except WebSocketDisconnect:
        print("Cámara desconectada")
    except Exception as e:
        print("Error ws_client:", e)

@app.websocket("/ws/admin/video")
async def ws_admin_video(websocket: WebSocket):
    camera = websocket.query_params.get("camera_id")

    if camera not in ["camA", "camB"]:
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

    effective_since = since or db.session_start
    camera_lower = camera_id.lower() if camera_id else None
    print(
        "[QUERY EVENTS]",
        "camera=", camera_id,
        "since=", effective_since,
        "limit=", limit,
    )

    events = db.get_events(camera_id=camera_lower, since=effective_since, limit=limit)
    return {"events": events, "session_start": db.session_start}


@app.get("/events/recent")
async def recent_events(camera_id: Optional[str] = None, limit: int = 100):
    effective_camera = camera_id.lower() if camera_id else None
    if effective_camera and effective_camera not in admin_events.VALID_CAMERA_IDS:
        return {"events": [], "session_start": db.session_start}

    events = db.get_events(camera_id=effective_camera, since=db.session_start, limit=limit)
    return {"events": events, "session_start": db.session_start}


@app.post("/mode")
async def set_mode(payload: dict):
    mode = str(payload.get("mode", "none")).strip()
    return switch_mode(mode)


@app.get("/mode")
async def get_mode():
    return {"mode": active_mode}
