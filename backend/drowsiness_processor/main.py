import numpy as np
import json

from drowsiness_processor.extract_points.point_extractor import PointsExtractor
from drowsiness_processor.data_processing.main import PointsProcessing
from drowsiness_processor.drowsiness_features.processing import FeaturesDrowsinessProcessing
from drowsiness_processor.visualization.main import ReportVisualizer
from drowsiness_processor.reports.main import DrowsinessReports


class DrowsinessDetectionSystem:
    def __init__(self):
        self.points_extractor = PointsExtractor()
        self.points_processing = PointsProcessing()
        self.features_processing = FeaturesDrowsinessProcessing()
        self.visualizer = ReportVisualizer()
        self.reports = DrowsinessReports()
        self.json_report = {}
        self.face_mesh_failures = 0

    def frame_processing(self, face_image: np.ndarray, camera_id: str):
        brightness = float(np.mean(face_image))
        if brightness < 25:
            self.json_report = {}
            return face_image, face_image, self.json_report

        key_points, control_process, sketch = self.points_extractor.process(face_image)

        if self.points_extractor.last_mesh_success:
            self.face_mesh_failures = 0
        else:
            self.face_mesh_failures += 1

        if self.face_mesh_failures > 3 or (
            self.points_extractor.last_mesh_success and self.points_extractor.last_eye_distance < 12
        ):
            control_process = False

        if control_process:
            points_processed = self.points_processing.main(key_points)
            features = self.features_processing.main(points_processed)

            event_flags = self.features_processing.extract_event_flags(features)

            # Visual overlay
            sketch = self.visualizer.visualize_all_reports(sketch, features)

            json_str = self.reports.generate_json_report(event_flags, camera_id)
            try:
                self.json_report = json.loads(json_str)
            except json.JSONDecodeError:
                self.json_report = {}

        else:
            self.json_report = {}

        return face_image, sketch, self.json_report
