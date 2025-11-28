import cv2
import asyncio
import websockets
import json
import base64
import threading
import subprocess
import numpy as np
import time

SERVER_URL = "ws://127.0.0.1:8000/ws"

CAMS = {
    "camA": {"type": "webcam", "source": 1},
    "camB": {"type": "rtsp", "source": "rtsp://192.168.101.3:8080/h264_pcm.sdp"}
}

async def connect_ws():
    while True:
        try:
            ws = await websockets.connect(
                SERVER_URL,
                max_size=6_000_000,
                ping_interval=None
            )
            return ws
        except:
            await asyncio.sleep(1)

async def send_frame(ws, cam, frame):
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    if not ok:
        return True

    frame64 = base64.b64encode(buffer).decode("utf-8")
    msg = json.dumps({"camera_id": cam, "frame": frame64})

    try:
        await ws.send(msg)
        try:
            await ws.recv()
        except:
            pass
        return True
    except:
        return False

def start_webcam(cam, src):
    asyncio.run(webcam_loop(cam, src))

async def webcam_loop(cam, src):
    ws = await connect_ws()

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"No se pudo abrir {cam}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        if not await send_frame(ws, cam, frame):
            ws = await connect_ws()

        await asyncio.sleep(0.03)

def start_rtsp(cam, url):
    asyncio.run(rtsp_loop(cam, url))

async def rtsp_loop(cam, url):
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", url,
        "-vf", "scale=640:360",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-"
    ]

    ws = await connect_ws()

    while True:
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            buffer = b""

            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk
                a = buffer.find(b"\xff\xd8")
                b = buffer.find(b"\xff\xd9")

                if a != -1 and b != -1:
                    jpg = buffer[a:b+2]
                    buffer = buffer[b+2:]

                    frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    if not await send_frame(ws, cam, frame):
                        ws = await connect_ws()

        except:
            await asyncio.sleep(1)

if __name__ == "__main__":
    print("Iniciando cámaras…")

    for cam, cfg in CAMS.items():
        if cfg["type"] == "webcam":
            threading.Thread(target=start_webcam, args=(cam, cfg["source"]), daemon=True).start()
        elif cfg["type"] == "rtsp":
            threading.Thread(target=start_rtsp, args=(cam, cfg["source"]), daemon=True).start()

    while True:
        time.sleep(1)
