from drowsiness_processor.main import DrowsinessDetectionSystem

class DetectionBridge:
    def __init__(self):
        self.detector = DrowsinessDetectionSystem()

    def run(self, frame, camera_id: str):
        _, sketch, report = self.detector.frame_processing(frame, camera_id)
        return sketch, report
