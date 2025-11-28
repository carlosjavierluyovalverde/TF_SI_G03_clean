import flet as ft
from pages.overview_page import OverviewPage
from pages.realtime_page import RealTimePage
from pages.camera_page import CameraPage
from pages.multi_view_page import MultiViewPage


def main(page: ft.Page):
    page.title = "Driver Fatigue – Dashboard Admin"
    page.window.width = 1400
    page.window.height = 850
    page.padding = 0
    page.scroll = "auto"

    def route_change(route):
        page.views.clear()

        if page.route == "/":
            page.views.append(ft.View("/", [OverviewPage(page)]))

        elif page.route == "/realtime":
            page.views.append(ft.View("/realtime", [RealTimePage(page)]))

        elif "/camera/" in page.route:
            cid = page.route.split("/")[-1]
            page.views.append(ft.View(page.route, [CameraPage(page, cid)]))

        elif page.route == "/multi":
            page.views.append(ft.View("/multi", [MultiViewPage(page)]))

        page.update()

    def view_pop(v):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


ft.app(target=main, view=ft.WEB_BROWSER)
