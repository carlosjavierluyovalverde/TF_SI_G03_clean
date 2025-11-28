from drowsiness_processor.drowsiness_features.processor import DrowsinessProcessor
from drowsiness_processor.drowsiness_features.eye_rub.processing import EyeRubEstimator
from drowsiness_processor.drowsiness_features.flicker_and_microsleep.processing import FlickerEstimator
from drowsiness_processor.drowsiness_features.pitch.processing import PitchEstimator
from drowsiness_processor.drowsiness_features.yawn.processing import YawnEstimator


class FeaturesDrowsinessProcessing:
    def __init__(self):
        self.features_drowsiness: dict[str, DrowsinessProcessor] = {
            'eye_rub_first_hand': EyeRubEstimator(),
            'eye_rub_second_hand': EyeRubEstimator(),
            'flicker_and_micro_sleep': FlickerEstimator(),
            'pitch': PitchEstimator(),
            'yawn': YawnEstimator(),
        }
        self.processed_feature: dict = {
            'eye_rub_first_hand': None,
            'eye_rub_second_hand': None,
            'flicker_and_micro_sleep': None,
            'pitch': None,
            'yawn': None
        }

    def main(self, distances: dict):
        self.processed_feature['eye_rub_first_hand'] = None
        self.processed_feature['eye_rub_second_hand'] = None
        if 'first_hand' in distances:
            self.processed_feature['eye_rub_first_hand'] = (self.features_drowsiness['eye_rub_first_hand'].process(distances['first_hand']))
        else:
            self.processed_feature['eye_rub_first_hand'] = self.features_drowsiness['eye_rub_first_hand'].process({})

        if 'second_hand' in distances:
            self.processed_feature['eye_rub_second_hand'] = (self.features_drowsiness['eye_rub_second_hand'].process(distances['second_hand']))
        else:
            self.processed_feature['eye_rub_second_hand'] = self.features_drowsiness['eye_rub_second_hand'].process({})

        self.processed_feature['flicker_and_micro_sleep'] = (self.features_drowsiness['flicker_and_micro_sleep'].process
                                                             (distances.get('eyes', {})))
        self.processed_feature['pitch'] = self.features_drowsiness['pitch'].process(distances.get('head', {}))
        self.processed_feature['yawn'] = self.features_drowsiness['yawn'].process(distances.get('mouth', {}))
        return self.processed_feature

    def extract_event_flags(self, processed_feature: dict) -> dict:
        """Return a normalized map of boolean events expected by the rest of the system."""
        flicker_data = processed_feature.get('flicker_and_micro_sleep', {}) or {}

        return {
            "eye_rub": bool(
                (processed_feature.get('eye_rub_first_hand') or {}).get('eye_rub_report') or
                (processed_feature.get('eye_rub_second_hand') or {}).get('eye_rub_report')
            ),
            "flicker": bool(flicker_data.get('flicker_report')),
            "micro_sleep": bool(flicker_data.get('micro_sleep_report')),
            "pitch": bool((processed_feature.get('pitch') or {}).get('pitch_report')),
            "yawn": bool((processed_feature.get('yawn') or {}).get('yawn_report')),
        }
