import flet as ft

SEVERITY_COLORS = {
    "low": ft.Colors.GREEN,
    "medium": ft.Colors.AMBER,
    "high": ft.Colors.RED,
}

class AlertBox(ft.Container):
    def __init__(self):
        super().__init__()

        self.text = ft.Text("Sin alertas", size=20, weight="bold")
        self.bgcolor = ft.Colors.GREY_200
        self.padding = 15
        self.border_radius = 10
        self.animate = ft.animation.Animation(300, ft.AnimationCurve.EASE)

        self.content = self.text

    def update_alert(self, report):
        """
        report ejemplo:
        {"global_state": "medium", "blink": {...}, ...}
        """

        state = report.get("global_state", "low")
        color = SEVERITY_COLORS.get(state, ft.Colors.GREY)

        self.bgcolor = color
        self.text.value = f"Estado actual: {state.upper()}"

        self.update()
