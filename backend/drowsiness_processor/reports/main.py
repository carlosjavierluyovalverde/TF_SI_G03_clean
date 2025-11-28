import json
from datetime import datetime


class DrowsinessReports:
    def __init__(self):
        # Aquí NO hacemos logs masivos
        pass

    def save(self, camera_id: str, rep: dict):
        """
        Guarda SOLO eventos reales en la DB.
        """
        from database import Database

        if not self._has_real_event(rep):
            return  # NO GUARDAR basura

        db = Database()
        db.insert_event(
            camera_id=camera_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=json.dumps(rep)
        )

    def generate_json_report(self, rep: dict, camera_id: str) -> str:
        """
        Genera un JSON legible SOLO SI hay evento real.
        """
        if not self._has_real_event(rep):
            return json.dumps({})  # NO ENVIAR NADA

        return json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "camera_id": camera_id,
            "report": self._simplify(rep)
        })

    # --------- NUEVO: FILTRO DE EVENTOS REALES ----------
    def _has_real_event(self, rep: dict) -> bool:
        if rep.get("eye_rub_first_hand", {}).get("eye_rub_report"):
            return True
        if rep.get("eye_rub_second_hand", {}).get("eye_rub_report"):
            return True

        fm = rep.get("flicker_and_micro_sleep", {})
        if fm.get("flicker_report") or fm.get("micro_sleep_report"):
            return True

        if rep.get("pitch", {}).get("pitch_report"):
            return True
        if rep.get("yawn", {}).get("yawn_report"):
            return True
        return False

    def _simplify(self, rep: dict) -> dict:
        """
        Solo envía los campos necesarios a Flet.
        """
        return {
            "eye_rub_first_hand": {
                "eye_rub_report": rep["eye_rub_first_hand"]["eye_rub_report"]
            },
            "eye_rub_second_hand": {
                "eye_rub_report": rep["eye_rub_second_hand"]["eye_rub_report"]
            },
            "flicker_and_micro_sleep": {
                "flicker_report": rep["flicker_and_micro_sleep"]["flicker_report"],
                "micro_sleep_report": rep["flicker_and_micro_sleep"]["micro_sleep_report"]
            },
            "pitch": {
                "pitch_report": rep["pitch"]["pitch_report"]
            },
            "yawn": {
                "yawn_report": rep["yawn"]["yawn_report"]
            }
        }
    