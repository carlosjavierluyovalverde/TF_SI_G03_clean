import cv2
import base64
import json
import asyncio
import websockets

SERVER_URL = "ws://127.0.0.1:8000/ws"
CAMERA_ID = "camA"


async def send_camera():
    print(f"🔄 Conectando al backend: {SERVER_URL}")

    async with websockets.connect(SERVER_URL) as websocket:
        print("🟢 Conexión WebSocket establecida.")

        cap = cv2.VideoCapture(1    )

        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara.")
            return

        print("🎥 Cámara abierta correctamente. Enviando frames...")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠ No se pudo leer frame.")
                continue

            # Encode JPG → base64
            _, buffer = cv2.imencode(".jpg", frame)
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            # Payload para backend
            payload = {
                "camera_id": CAMERA_ID,
                "frame": frame_b64
            }

            # Enviar frame
            await websocket.send(json.dumps(payload))
            print("📤 Frame enviado.")

            # 🔵 YA NO ESPERAMOS RESPUESTA DEL BACKEND
            # Solo intentamos leer sin bloquear
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                print("📥 Respuesta opcional:", msg[:60])
            except asyncio.TimeoutError:
                # No llegó respuesta → esto es perfectamente normal
                pass

        cap.release()


asyncio.run(send_camera())
