import base64
import cv2
import threading
import time
from datetime import datetime


class BaseCameraThread(threading.Thread):
    def __init__(self, camera_id, detector, video_manager, admin_events, db):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.detector = detector
        self.video_manager = video_manager
        self.admin_events = admin_events
        self.db = db
        self._stop_event = threading.Event()
        self.last_frame_ts = 0.0
        self.frame_count = 0

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def _process_frame(self, frame):
        try:
            ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if not ok:
                return
            frame64 = base64.b64encode(buffer).decode("utf-8")
            print("[FRAME RECEIVED]", self.camera_id)
            self.video_manager.broadcast_frame_threadsafe(self.camera_id, frame64)
        except Exception as e:
            print("[FRAME ERROR]", self.camera_id, e)

        try:
            _, report = self.detector.run(frame, self.camera_id)
        except Exception as e:
            print("[DETECTOR ERROR]", self.camera_id, e)
            return

        if not isinstance(report, dict):
            return

        events = report.get("events", {}) if isinstance(report.get("events", {}), dict) else {}
        if not any(events.values()):
            return

        report = dict(report)
        report["camera_id"] = self.camera_id.lower()
        if not report.get("timestamp"):
            report["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        print("[EVENT DETECTED]", self.camera_id, "ts=", report.get("timestamp"), "payload=", report)
        self.db.save_event(self.camera_id, report)
        print("[EVENT STORED]", self.camera_id, "ts=", report.get("timestamp"))
        self.admin_events.broadcast_event_threadsafe(report)
        print("[WS SEND] cam=", self.camera_id, "event=", report)


class WebcamThread(BaseCameraThread):
    def __init__(self, detector, video_manager, admin_events, db, source=0):
        super().__init__("camA", detector, video_manager, admin_events, db)
        self.source = source
        print("[THREAD CREATE] camA")

    def run(self):
        print("[THREAD START] camA")
        cap = cv2.VideoCapture(self.source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        while not self.stopped():
            grabbed = cap.grab()
            if not grabbed:
                time.sleep(0.001)
                continue

            ret, frame = cap.retrieve()
            if not ret:
                time.sleep(0.001)
                continue

            now = time.time()
            if self.last_frame_ts and now - self.last_frame_ts > 0.3:
                print("[DELAY WARNING] cam=camA delay=", round(now - self.last_frame_ts, 3))
            self.last_frame_ts = now
            self.frame_count += 1
            print("[FRAME OK] cam=camA ts=", now)

            if self.frame_count % 2 == 0:
                self._process_frame(frame)

        try:
            cap.release()
        except Exception:
            pass
        print("[THREAD STOP] camA")


class RTSPThread(BaseCameraThread):
    def __init__(self, detector, video_manager, admin_events, db, url):
        super().__init__("camB", detector, video_manager, admin_events, db)
        self.url = url
        print("[THREAD CREATE] camB")

    def run(self):
        print("[THREAD START] camB")
        while not self.stopped():
            cap = cv2.VideoCapture(self.url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                print("[RTSP RECONNECT] camB no se pudo abrir, reintentando…")
                cap.release()
                time.sleep(1)
                continue

            consecutive_failures = 0

            while not self.stopped():
                grabbed = cap.grab()
                if not grabbed:
                    consecutive_failures += 1
                    if consecutive_failures >= 5:
                        print("[RTSP RECONNECT] camB señal perdida, reintentando…")
                        break
                    time.sleep(0.01)
                    continue

                ret, frame = cap.retrieve()
                if not ret:
                    time.sleep(0.01)
                    continue

                consecutive_failures = 0
                now = time.time()
                if self.last_frame_ts and now - self.last_frame_ts > 0.3:
                    print("[DELAY WARNING] cam=camB delay=", round(now - self.last_frame_ts, 3))
                self.last_frame_ts = now
                self.frame_count += 1
                print("[FRAME OK] cam=camB ts=", now)

                if self.frame_count % 2 == 0:
                    self._process_frame(frame)

            try:
                cap.release()
            except Exception:
                pass

            if not self.stopped():
                time.sleep(1)

        print("[THREAD STOP] camB")


class VideoThreadManager:
    def __init__(self, detector, video_manager, admin_events, db, rtsp_url):
        self.detector = detector
        self.video_manager = video_manager
        self.admin_events = admin_events
        self.db = db
        self.rtsp_url = rtsp_url
        self.camA_thread = None
        self.camB_thread = None
        self.lock = threading.Lock()

    def start_camA(self):
        with self.lock:
            if self.camA_thread and self.camA_thread.is_alive():
                print("[THREAD EXISTS] camA")
                return
            self.stop_camA()
            self.camA_thread = WebcamThread(self.detector, self.video_manager, self.admin_events, self.db, source=0)
            self.camA_thread.start()

    def start_camB(self):
        with self.lock:
            if self.camB_thread and self.camB_thread.is_alive():
                print("[THREAD EXISTS] camB")
                return
            self.stop_camB()
            self.camB_thread = RTSPThread(self.detector, self.video_manager, self.admin_events, self.db, url=self.rtsp_url)
            self.camB_thread.start()

    def start_multi(self):
        self.start_camA()
        self.start_camB()

    def stop_camA(self):
        if self.camA_thread:
            print("[THREAD STOP] camA")
            self.camA_thread.stop()
            self.camA_thread.join(timeout=2)
            self.camA_thread = None

    def stop_camB(self):
        if self.camB_thread:
            print("[THREAD STOP] camB")
            self.camB_thread.stop()
            self.camB_thread.join(timeout=2)
            self.camB_thread = None

    def stop_all(self):
        with self.lock:
            self.stop_camA()
            self.stop_camB()
