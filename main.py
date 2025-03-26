import logging
import os
import flet as ft
from components.app_layout import create_app_layout
from routes import setup_routes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
logger.info('Iniciando aplicação...')


def main(page: ft.Page):
    cores_light = {
        "primary": "#3B82F6",
        "on_primary": "#FFFFFF",
        "primary_container": "#DBEAFE",
        "on_surface": "#111827",
        "surface": "#F9FAFB",
    }
    cores_dark = {
        "primary": "#60A5FA",
        "on_primary": "#1E3A8A",
        "primary_container": "#1E3A8A",
        "on_surface": "#FFFFFF",
        "surface": "#111827",
    }
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_light))
    page.dark_theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_dark))
    page.theme_mode = ft.ThemeMode.DARK

    def handle_lifecycle_change(e: ft.AppLifecycleStateChangeEvent):
        if e.data == "inactive":
            logger.info("Aplicação em segundo plano")
            page.session.set("app_in_background", True)
        elif e.data == "active":
            logger.info("Aplicação voltou ao primeiro plano")
            page.session.set("app_in_background", False)
            page.update()

    layout, app_state = create_app_layout(page)
    company_data = {
        "name": "DebtManager",
        "logo": "https://picsum.photos/150",
        "contact_email": "example@email.com",
        "contact_phone": "(11) 99999-9999",
        "secret_key": os.getenv("MY_APP_SECRET_KEY")
    }

    usage_tracker = app_state["usage_tracker"]
    usage_tracker.usage["messages_sent"] = page.client_storage.get("debtmanager.messages_sent") or 0

    setup_routes(page, layout, app_state, app_state, company_data)
    page.on_app_lifecycle_state_change = handle_lifecycle_change


if __name__ == "__main__":
    os.environ["FLET_LOG_LEVEL"] = "info"
    os.environ["FLET_LOG_TO_FILE"] = "true"
    ft.app(target=main)
