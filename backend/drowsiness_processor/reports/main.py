import json
from datetime import datetime


class DrowsinessReports:
    def __init__(self):
        # Normalizador central de eventos
        pass

    def generate_json_report(self, events: dict, camera_id: str) -> str:
        """
        Genera un JSON legible SOLO SI hay evento real usando el formato unificado.
        """
        normalized_events = self._normalize_events(events)

        if not self._has_real_event(normalized_events):
            return json.dumps({})  # NO ENVIAR NADA

        payload = {
            "camera_id": camera_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "events": normalized_events
        }

        return json.dumps(payload)

    def _has_real_event(self, events: dict) -> bool:
        return any(events.values()) if isinstance(events, dict) else False

    def _normalize_events(self, events: dict) -> dict:
        template = {
            "eye_rub": False,
            "flicker": False,
            "micro_sleep": False,
            "pitch": False,
            "yawn": False,
        }

        if not isinstance(events, dict):
            return template

        for key in template.keys():
            template[key] = bool(events.get(key, False))

        return template
    