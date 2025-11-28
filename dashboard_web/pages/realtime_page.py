import flet as ft


class RealTimePage(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()

        self.controls = [
            ft.Text("Monitoreo en tiempo real (próximamente)", size=24),
            ft.ElevatedButton("Volver", on_click=lambda e: page.go("/"))
        ]
