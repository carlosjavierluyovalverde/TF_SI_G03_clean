import flet as ft
import threading
import websocket
import json
import time
from components.video_box import VideoBox

class CameraPage(ft.Column):

    def __init__(self, page: ft.Page, camera_id: str):
        super().__init__()

        self.page = page
        self.camera_id = camera_id
        self.camera_id_canonical = str(camera_id).strip().lower()

        self.video_box = VideoBox(camera_id, page)

        self.detect_text = ft.Text(
            "Sin actividad detectada",
            size=20,
            weight="bold",
            color="white"
        )

        self.controls = [
            ft.Text(f"Cámara {camera_id}", size=28, weight="bold"),
            self.video_box,
            ft.Container(
                content=self.detect_text,
                padding=10,
                bgcolor="#222",
                border_radius=10,
                width=480
            ),
            ft.ElevatedButton("Volver", on_click=lambda e: page.go("/"))
        ]

        self.stop = False
        self.ws = None
        self.thread = None

    def did_mount(self):
        self.stop = False
        self.start_event_socket()
        self.video_box.did_mount()

    def will_unmount(self):
        self.stop = True
        try:
            if self.ws:
                self.ws.close()
        except:
            pass
        self.video_box.will_unmount()

    def start_event_socket(self):

        def _run():
            url = "ws://127.0.0.1:8000/ws/admin/events"

            while not self.stop:
                try:
                    self.ws = websocket.WebSocket()
                    self.ws.connect(url)

                    while not self.stop:
                        msg = self.ws.recv()
                        if not msg:
                            continue

                        data = json.loads(msg)

                        data_camera_id = str(data.get("camera_id", "")).strip().lower()
                        print(f"[DEBUG] Mensaje recibido para camera_id={data_camera_id}")  # TODO: quitar tras depuración

                        if data_camera_id != self.camera_id_canonical:
                            continue

                        txt = self.format_report(data)

                        self.detect_text.value = txt
                        self.page.update()

                except:
                    time.sleep(1)
                    continue

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()

    def format_report(self, rep: dict) -> str:
        events = rep.get("events", {}) if isinstance(rep, dict) else {}

        lines = []

        if events.get("eye_rub"):
            lines.append("👋 Frotado de ojos")

        if events.get("flicker"):
            lines.append("⚡ Parpadeo excesivo")

        if events.get("micro_sleep"):
            lines.append("💤 Microsueño detectado")

        if events.get("pitch"):
            lines.append("📐 Inclinación peligrosa")

        if events.get("yawn"):
            lines.append("😮 Bostezo detectado")

        if not lines:
            return "Sin actividad detectada"

        if rep.get("timestamp"):
            lines.append(f"⏱ {rep['timestamp']}")

        return "\n".join(lines)
