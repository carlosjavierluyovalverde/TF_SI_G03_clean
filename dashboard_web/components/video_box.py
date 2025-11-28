import flet as ft
import base64
from components.video_socket_manager import VideoSocketManager
import threading
import time
import requests

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

        if camera_id == "camB":
            self.mjpeg_url = "http://192.168.101.3:8080/video"
        else:
            self.ws_manager = VideoSocketManager(
                camera_id,
                f"ws://127.0.0.1:8000/ws/admin/video?camera_id={camera_id}"
            )

    def did_mount(self):
        if self.started:
            return
        self.started = True

        if self.camera_id == "camB":
            self.start_mjpeg()
        else:
            self.ws_manager.add_listener(self.update_image)

    def will_unmount(self):
        self.stop = True

        if self.camera_id != "camB":
            self.ws_manager.remove_listener(self.update_image)

    def update_image(self, b64img):
        self.img.src_base64 = b64img
        self.page.update()

    def start_mjpeg(self):
        def _run():
            buf = b""
            while not self.stop:
                try:
                    r = requests.get(self.mjpeg_url, stream=True, timeout=5)
                    if r.status_code != 200:
                        time.sleep(1)
                        continue

                    for chunk in r.iter_content(1024):
                        if self.stop:
                            break

                        buf += chunk
                        a = buf.find(b"\xff\xd8")
                        b = buf.find(b"\xff\xd9")

                        if a != -1 and b != -1:
                            jpg = buf[a:b+2]
                            buf = buf[b+2:]

                            b64 = base64.b64encode(jpg).decode()
                            self.update_image(b64)

                except Exception as e:
                    print("MJPEG error:", e)
                    time.sleep(1)

        threading.Thread(target=_run, daemon=True).start()
