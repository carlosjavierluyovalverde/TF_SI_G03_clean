import flet as ft


class OverviewPage(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page

        self.controls = [
            ft.Text("Dashboard Administrativo", size=30, weight="bold"),
            ft.Divider(),

            ft.ElevatedButton(
                "Ver monitoreo en tiempo real",
                on_click=lambda e: page.go("/realtime"),
                width=300
            ),

            ft.ElevatedButton(
                "Vista Multicámara (A/B)",
                on_click=lambda e: page.go("/multi"),
                width=300
            ),

            ft.ElevatedButton(
                "Cámara A",
                on_click=lambda e: page.go("/camera/camA"),
                width=200
            ),
            ft.ElevatedButton(
                "Cámara B",
                on_click=lambda e: page.go("/camera/camB"),
                width=200
            ),
        ]
