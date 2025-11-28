import flet as ft
import json
import threading
import time
import websocket
from components.event_socket_manager import EventSocketManager


class RealTimePage(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()

        self.page = page
        self.ws = None
        self.stop = False
        self.thread = None
        self.reports = []
        self.event_manager = EventSocketManager()

        self.camera_filter = ft.Dropdown(
            label="Cámara",
            value="all",
            options=[
                ft.dropdown.Option("all", "Todas"),
                ft.dropdown.Option("cama", "camA"),
                ft.dropdown.Option("camb", "camB"),
            ],
            on_change=lambda e: self.refresh_rows(),
            width=160,
        )

        self.critical_only = ft.Checkbox(
            label="Sólo eventos críticos (microsueño/inclinación)",
            value=False,
            on_change=lambda e: self.refresh_rows(),
        )

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Hora")),
                ft.DataColumn(ft.Text("Cámara")),
                ft.DataColumn(ft.Text("Eventos detectados")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.1, ft.colors.WHITE),
        )

        self.controls = [
            ft.Text("Monitoreo en tiempo real", size=28, weight="bold"),
            ft.Text("Eventos recibidos desde las cámaras en vivo", size=16),
            ft.Row([
                self.camera_filter,
                self.critical_only,
                ft.ElevatedButton("Volver", on_click=lambda e: page.go("/")),
            ], wrap=True, spacing=16),
            ft.Divider(),
            ft.Container(
                content=ft.Column([
                    ft.Text("Bitácora de eventos", size=20, weight="bold"),
                    self.table,
                ], tight=True, spacing=10),
                bgcolor="#111",
                padding=16,
                border_radius=10,
                width=900,
            ),
        ]

    def did_mount(self):
        self.stop = False
        self.start_event_socket()

    def will_unmount(self):
        self.stop = True
        self.event_manager.remove_listener(self._handle_event)

    def start_event_socket(self):

        for ev in self.event_manager.get_events():
            formatted = self._prepare_report(ev, ev.get("camera_id"))
            if formatted:
                self.reports.append(formatted)

        self.refresh_rows()

        self.event_manager.add_listener(self._handle_event)

    def _handle_event(self, event_data: dict):
        def _apply():
            formatted = self._prepare_report(event_data, event_data.get("camera_id"))
            if not formatted:
                return
            self.reports.insert(0, formatted)
            self.reports = self.reports[:50]
            self.refresh_rows()

        try:
            self.page.call_from_thread(_apply)
        except Exception:
            _apply()

    def _prepare_report(self, data: dict, camera_id: str) -> dict:
        events = data.get("events", {}) if isinstance(data, dict) else {}
        if not isinstance(events, dict):
            return {}

        active_events = [k for k, v in events.items() if v]
        if not active_events:
            return {}

        important_labels = {
            "eye_rub": "👋 Frotado de ojos",
            "flicker": "⚡ Parpadeo excesivo",
            "micro_sleep": "💤 Microsueño",
            "pitch": "📐 Inclinación",
            "yawn": "😮 Bostezo",
        }

        summary = ", ".join(important_labels.get(e, e) for e in active_events)

        return {
            "camera_id": camera_id,
            "timestamp": data.get("timestamp", "-"),
            "summary": summary,
            "critical": any(ev in {"micro_sleep", "pitch"} for ev in active_events),
        }

    def refresh_rows(self):
        selected_camera = self.camera_filter.value
        only_critical = self.critical_only.value

        rows = []
        for rep in self.reports:
            if selected_camera != "all" and rep["camera_id"] != selected_camera:
                continue
            if only_critical and not rep["critical"]:
                continue

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(rep.get("timestamp", "-")))),
                        ft.DataCell(ft.Text(rep.get("camera_id", "-").upper())),
                        ft.DataCell(ft.Text(rep.get("summary", "-"))),
                    ],
                    color=ft.colors.with_opacity(0.05, ft.colors.RED) if rep.get("critical") else None,
                )
            )

        self.table.rows = rows
        self.page.update()
