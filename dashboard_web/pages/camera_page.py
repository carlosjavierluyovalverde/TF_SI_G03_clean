import flet as ft
import threading
import websocket
import json
import time
import requests
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

        self.events_list = ft.ListView(
            spacing=6,
            height=220,
            auto_scroll=True,
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
            ft.Container(
                content=ft.Column([
                    ft.Text("Eventos recientes", size=18, weight="bold"),
                    self.events_list,
                ], tight=True, spacing=10),
                padding=10,
                bgcolor="#111",
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
        self.load_recent_events()
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

                        if data_camera_id != self.camera_id_canonical:
                            continue

                        self.page.call_from_thread(self._handle_new_event, data)

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

    def _handle_new_event(self, data: dict):
        txt = self.format_report(data)
        self.detect_text.value = txt
        self._append_event_entry(data)
        self.page.update()

    def _append_event_entry(self, report: dict, fallback_ts: str = "-"):
        summary = self._summarize_events(report)
        if not summary:
            return

        ts = report.get("timestamp") or fallback_ts
        row = ft.Row([
            ft.Text(ts, width=140, color="white"),
            ft.Text(summary, expand=True, color="white"),
        ], spacing=10)

        self.events_list.controls.insert(0, row)
        self.events_list.controls = self.events_list.controls[:100]

    def _summarize_events(self, rep: dict) -> str:
        events = rep.get("events", {}) if isinstance(rep, dict) else {}
        active = [k for k, v in events.items() if v]
        labels = {
            "eye_rub": "👋 Frotado de ojos",
            "flicker": "⚡ Parpadeo excesivo",
            "micro_sleep": "💤 Microsueño",
            "pitch": "📐 Inclinación",
            "yawn": "😮 Bostezo",
        }

        return ", ".join(labels.get(a, a) for a in active)

    def load_recent_events(self):
        try:
            resp = requests.get(
                "http://127.0.0.1:8000/admin/events",
                params={
                    "camera_id": self.camera_id,
                    "limit": 100,
                },
                timeout=5,
            )

            if resp.status_code != 200:
                return

            payload = resp.json()
            events = payload.get("events", []) if isinstance(payload, dict) else []

            for ev in events:
                report = ev.get("report", {}) if isinstance(ev, dict) else {}
                if str(ev.get("camera_id", "")).strip().lower() != self.camera_id_canonical:
                    continue
                self._append_event_entry(report, fallback_ts=str(ev.get("timestamp", "-")))

            self.page.update()
        except Exception:
            return
