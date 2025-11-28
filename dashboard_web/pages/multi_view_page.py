import flet as ft
from components.video_box import VideoBox


class MultiViewPage(ft.Column):

    def __init__(self, page):
        super().__init__()
        self.page = page

        # camA → WebSocket
        # camB → MJPEG directo
        # camC → WebSocket (si existe)
        self.boxA = VideoBox("camA", page)
        self.boxB = VideoBox("camB", page)
        self.boxC = VideoBox("camC", page)

        self.controls = [
            ft.Row([self.boxA, self.boxB]),
            ft.Row([self.boxC])
        ]

    def did_mount(self):
        print("⭐ MultiView montado — iniciando sockets/MJPEG")
        self.boxA.did_mount()
        self.boxB.did_mount()
        self.boxC.did_mount()

    def will_unmount(self):
        self.boxA.will_unmount()
        self.boxB.will_unmount()
        self.boxC.will_unmount()
