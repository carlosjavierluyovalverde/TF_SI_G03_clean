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

    def frame_processing(self, face_image: np.ndarray, camera_id: str):
        key_points, control_process, sketch = self.points_extractor.process(face_image)

        if control_process:
            points_processed = self.points_processing.main(key_points)
            features = self.features_processing.main(points_processed)

            # Visual overlay
            sketch = self.visualizer.visualize_all_reports(sketch, features)

            # FILTRO DE EVENTO REAL
            if self.reports._has_real_event(features):
                self.reports.save(camera_id, features)

                json_str = self.reports.generate_json_report(features, camera_id)
                self.json_report = json.loads(json_str)
            else:
                # Nada que enviar si no hay evento
                self.json_report = {}

        return face_image, sketch, self.json_report
