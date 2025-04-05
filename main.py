import logging
import os
import time

import flet as ft
import requests

from routes import setup_routes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}"}


def verificar_status_usuario(page):
    retries = 5
    delay = 5
    max_delay = 32
    for attempt in range(retries):
        try:
            user_id = page.client_storage.get("user_id")
            if not user_id or page.route in ["/login", "/register"]:
                return
            cached_status = page.client_storage.get("user_status")
            last_checked = page.client_storage.get("last_checked") or 0
            if cached_status and time.time() - last_checked < 60:  # alterei para 60 segundos
                if cached_status == "inativo":
                    page.client_storage.clear()
                    page.go("/login")
                return
            user_data = requests.get(f"{SUPABASE_URL_USERS}/rest/v1/users_debt?id=eq.{user_id}", headers=headers).json()
            status = user_data[0]["status"] if user_data else "inativo"
            page.client_storage.set("user_status", status)
            page.client_storage.set("last_checked", time.time())
            if status != "ativo":
                page.client_storage.clear()
                page.go("/login")
            break
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            time.sleep(min(delay, max_delay))
            delay *= 2


def main(page: ft.Page):
    # page.client_storage.clear()
    cores_light = {"primary": "#3B82F6", "on_primary": "#FFFFFF",
                   "primary_container": "#DBEAFE", "on_surface": "#111827", "surface": "#F9FAFB"}
    cores_dark = {"primary": "#60A5FA", "on_primary": "#1E3A8A",
                  "primary_container": "#1E3A8A", "on_surface": "#FFFFFF", "surface": "#111827"}
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_light))
    page.dark_theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_dark))
    theme_mode = page.client_storage.get("theme_mode") or "DARK"
    page.theme_mode = ft.ThemeMode.DARK if theme_mode == "DARK" else ft.ThemeMode.LIGHT

    def handle_lifecycle_change(e: ft.AppLifecycleStateChangeEvent):
        if e.data == "inactive":
            logger.info("Aplicação em segundo plano")
            page.session.set("app_in_background", True)
        elif e.data == "active":
            logger.info("Aplicação voltou ao primeiro plano")
            page.session.set("app_in_background", False)
            verificar_status_usuario(page)
            page.update()

    company_data = {
        "name": "DebtManager",
        "logo": "https://picsum.photos/150",
        "contact_email": "example@email.com",
        "contact_phone": "(11) 99999-9999",
        "secret_key": os.getenv("MY_APP_SECRET_KEY")
    }

    app_state = {}

    # Configura as rotas
    setup_routes(page, None, None, app_state, company_data)
    page.on_app_lifecycle_state_change = handle_lifecycle_change

    verificar_status_usuario(page)
    if not page.client_storage.get("user_id") and page.route not in ["/login", "/register"]:
        page.go("/login")

    page.update()


if __name__ == "__main__":
    os.environ["FLET_LOG_LEVEL"] = "info"
    ft.app(target=main, assets_dir="assets", upload_dir="uploads")
