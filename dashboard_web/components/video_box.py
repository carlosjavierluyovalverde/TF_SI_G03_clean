import flet as ft
from components.video_socket_manager import VideoSocketManager

class VideoBox(ft.Container):

    def __init__(self, camera_id: str, page: ft.Page):
        super().__init__(
            width=480, height=360,
            bgcolor="#000", border_radius=10
        )

        self.camera_id = camera_id
        self.page = page
        self.img = ft.Image(src="", width=480, height=360)
        self.content = self.img

        self.started = False
        self.stop = False

        self.ws_manager = VideoSocketManager(
            camera_id,
            f"ws://127.0.0.1:8000/ws/admin/video?camera_id={camera_id}"
        )

    def did_mount(self):
        if self.started:
            return
        self.started = True

        self.ws_manager.add_listener(self.update_image)

    def will_unmount(self):
        self.stop = True

        self.ws_manager.remove_listener(self.update_image)

    def update_image(self, b64img):
        self.img.src_base64 = b64img
        self.page.update()

