import flet as ft
import requests
from components.video_box import VideoBox
from components.event_socket_manager import EventSocketManager


class MultiViewPage(ft.Column):

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.event_manager = EventSocketManager()
        print("[PAGE INIT] Multi")

        # camA → WebSocket
        # camB → MJPEG directo
        self.boxA = VideoBox("camA", page)
        self.boxB = VideoBox("camB", page)

        self.status_labels = {
            "cama": ft.Text("camA · Sin actividad", color="white"),
            "camb": ft.Text("camB · Sin actividad", color="white"),
        }

        self.controls = [
            ft.Row([self.boxA, self.boxB]),
            ft.Container(
                content=ft.Column([
                    ft.Text("Estado en vivo", size=18, weight="bold"),
                    ft.Column(list(self.status_labels.values()), spacing=6),
                ], tight=True, spacing=8),
                bgcolor="#111",
                padding=12,
                border_radius=10,
                width=960,
            ),
        ]

    def did_mount(self):
        self._switch_backend_mode("multi")
        for ev in self.event_manager.get_events():
            self._apply_event(ev)
        self.event_manager.add_listener(self._handle_event)
        self.boxA.did_mount()
        self.boxB.did_mount()

    def will_unmount(self):
        self.boxA.will_unmount()
        self.boxB.will_unmount()
        self.event_manager.remove_listener(self._handle_event)
        self._switch_backend_mode("none")

    def _summarize_events(self, events: dict) -> str:
        labels = {
            "eye_rub": "👋 Frotado de ojos",
            "flicker": "⚡ Parpadeo excesivo",
            "micro_sleep": "💤 Microsueño",
            "pitch": "📐 Inclinación",
            "yawn": "😮 Bostezo",
        }
        active = [labels.get(k, k) for k, v in events.items() if v]
        return ", ".join(active)

    def _apply_event(self, event_data: dict):
        cam = str(event_data.get("camera_id", "")).strip().lower()
        if cam not in self.status_labels:
            return

        summary = self._summarize_events(event_data.get("events", {}))
        ts = event_data.get("timestamp", "-")

        label_txt = summary or "Sin actividad"
        self.status_labels[cam].value = f"{cam.upper()} · {label_txt} · {ts}"

    def _handle_event(self, event_data: dict):
        try:
            self.page.call_from_thread(lambda: self._apply_and_update(event_data))
        except Exception:
            self._apply_and_update(event_data)

    def _apply_and_update(self, event_data: dict):
        print("[WS MESSAGE RECEIVED]", "cam=", event_data.get("camera_id"))
        self._apply_event(event_data)
        self.page.update()

    def _switch_backend_mode(self, mode: str):
        try:
            requests.post("http://127.0.0.1:8000/mode", json={"mode": mode}, timeout=2)
        except Exception:
            pass
