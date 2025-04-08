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
prefix = os.getenv("PREFIX")


def verificar_status_usuario(page):
    """
    Verifica o status do usuário realizando até 5 tentativas com backoff exponencial.
    Utiliza um cache válido por 10 minutos para evitar requisições desnecessárias.
    Caso o usuário não esteja ativo, o clientStorage é limpo e o usuário é redirecionado para /login.
    """
    retries = 5
    initial_delay = 5
    max_delay = 32
    delay = initial_delay

    for attempt in range(retries):
        logger.info(f"Tentativa {attempt + 1} de {retries} para verificar status do usuário.")
        try:
            user_id = page.client_storage.get(f"{prefix}user_id")

            # Redireciona se não houver user_id e o usuário estiver fora da tela de login ou cadastro
            if not user_id and page.route not in ["/login", "/register", "/terms", "/activation"]:
                logger.warning("Usuário não autenticado e fora das rotas de autenticação. Redirecionando para a página de login...")
                page.client_storage.clear()
                page.go("/login")
                return

            # Se estiver nas telas públicas, apenas sai da verificação
            if page.route in ["/login", "/register", "/terms", "/activation"]:
                logger.info("Rota pública. Não verificando status do usuário.")
                return

            # Verifica se há status armazenado em cache (válido por 10 minutos)
            cached_status = page.client_storage.get("user_status")
            last_checked = page.client_storage.get("last_checked") or 0
            current_time = time.time()

            if cached_status and current_time - last_checked < 600:
                logger.info(f"Status do usuário obtido do cache: {cached_status}")
                if cached_status == "inativo":
                    logger.warning("Usuário inativo. Limpando armazenamento e redirecionando para login.")
                    page.client_storage.clear()
                    page.go("/login")
                return

            # Consulta o status do usuário no Supabase
            logger.info("Buscando status do usuário no Supabase.")
            response = requests.get(
                f"{os.getenv('SUPABASE_URL_USERS')}/rest/v1/users_debt?id=eq.{user_id}",
                headers={
                    "apikey": os.getenv("SUPABASE_KEY_USERS"),
                    "Authorization": f"Bearer {os.getenv('SUPABASE_KEY_USERS')}"
                }
            )
            user_data = response.json()
            status = user_data[0]["status"] if user_data else "inativo"
            logger.info(f"Status do usuário obtido: {status}")

            # Armazena o status e o momento da verificação no cache
            page.client_storage.set("user_status", status)
            page.client_storage.set("last_checked", current_time)

            if status != "ativo":
                logger.warning("Status do usuário não é ativo. Limpando armazenamento e redirecionando para login.")
                page.client_storage.clear()
                page.go("/login")
            break

        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            time.sleep(min(delay, max_delay))
            delay *= 2
            logger.info(f"Aguardando {min(delay, max_delay)} segundos antes da próxima tentativa.")


def main(page: ft.Page):
    page.window.icon = "icon.png"
    page.window.height = 720.0
    page.window.min_height = 960.0
    page.window.max_height = 1080.0
    page.window.min_width = 1280.0
    page.window.width = 1280.0
    def page_resized(e):
        print("New page size:", page.window.width, page.window.height)

    page.on_resized = page_resized    # Campos do formulário

    cores_light = {"primary": "#3B82F6", "on_primary": "#FFFFFF",
                   "primary_container": "#DBEAFE", "on_surface": "#111827", "surface": "#F9FAFB"}
    cores_dark = {"primary": "#60A5FA", "on_primary": "#1E3A8A",
                  "primary_container": "#1E3A8A", "on_surface": "#FFFFFF", "surface": "#111827"}
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_light))
    page.dark_theme = ft.Theme(color_scheme=ft.ColorScheme(**cores_dark))
    theme_mode = page.client_storage.get("theme_mode") or "DARK"
    page.theme_mode = ft.ThemeMode.LIGHT if theme_mode == "LIGHT" else ft.ThemeMode.DARK

    def handle_lifecycle_change(e: ft.AppLifecycleStateChangeEvent):
        if e.data == "inactive":
            logger.info("Aplicação em segundo plano")
            page.session.set("app_in_background", True)
            verificar_status_usuario(page)
        elif e.data == "active":
            logger.info("Aplicação voltou ao primeiro plano")
            page.session.set("app_in_background", False)
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

    page.update()


if __name__ == "__main__":
    os.environ["FLET_LOG_LEVEL"] = "info"
    ft.app(target=main, assets_dir="assets", upload_dir="uploads")
