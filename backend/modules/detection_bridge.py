import cv2
from drowsiness_processor.main import DrowsinessDetectionSystem

class DetectionBridge:
    def __init__(self):
        self.detector = DrowsinessDetectionSystem()

    def run(self, frame, camera_id: str):
        if frame is None:
            print("[DETECTOR INPUT INVALID]", camera_id, "frame=None")
            return None, {}

        if not hasattr(frame, "shape") or frame.size == 0:
            print("[DETECTOR INPUT INVALID]", camera_id, "empty frame")
            return None, {}

        try:
            # Normalizamos a BGR asegurando 3 canales antes de entrar al detector.
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print("[DETECTOR INPUT INVALID]", camera_id, e)
            return None, {}

        print(
            "[DETECTOR INPUT]",
            camera_id,
            "shape=", frame.shape,
            "mean=", round(float(frame.mean()), 2),
        )

        _, sketch, report = self.detector.frame_processing(frame, camera_id)
        print("[DETECTOR REPORT]", camera_id, report)
        return sketch, report
