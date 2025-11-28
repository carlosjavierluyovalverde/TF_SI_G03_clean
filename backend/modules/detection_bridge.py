from drowsiness_processor.main import DrowsinessDetectionSystem

class DetectionBridge:
    def __init__(self):
        self.detectors: dict[str, DrowsinessDetectionSystem] = {}

    def _get_detector(self, camera_id: str) -> DrowsinessDetectionSystem:
        if camera_id not in self.detectors:
            self.detectors[camera_id] = DrowsinessDetectionSystem()
        return self.detectors[camera_id]

    def run(self, frame, camera_id: str):
        detector = self._get_detector(camera_id)
        _, sketch, report = detector.frame_processing(frame, camera_id)
        return sketch, report
