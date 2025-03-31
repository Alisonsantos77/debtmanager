from time import sleep
import flet as ft
import logging
from utils.supabase_utils import validate_user, fetch_user_id
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def LoginPage(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300, border_color=ft.Colors.BLUE)
    password_field = ft.TextField(label="Senha", width=300, border_color=ft.Colors.BLUE, password=True)
    status_text = ft.Text("", color=ft.Colors.RED)
    login_button = ft.ElevatedButton("Entrar", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
    register_button = ft.TextButton("Cadastrar", on_click=lambda _: page.go("/register"))
    activate_button = ft.TextButton("Ativar Conta", on_click=lambda _: page.go("/activate"))

    def show_success_and_redirect(route, message="Sucesso!"):
        success_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN),
                        ft.Text(message, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        sleep(2)
        page.close(success_dialog)
        page.go(route)
        page.update()

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()

    def login(e):
        username = username_field.value.strip()
        password = password_field.value.strip()
        if not username or not password:
            status_text.value = "Preencha usuário e senha!"
            page.update()
            return

        loading_dialog = show_loading()
        status, user = validate_user(username, password, encrypted=True, page=page)
        logger.info(f"Resultado da validação para {username}: status={status}")

        if status == "ativo" and user:
            user_id = fetch_user_id(username, page)
            if user_id:
                page.client_storage.set("username", username)
                page.client_storage.set("user_id", user_id)
                page.client_storage.set("session_expiry", (datetime.now(
                    timezone.utc) + timedelta(hours=24)).isoformat())
                logger.info(f"Login bem-sucedido para {username}. Username e user_id salvos no client_storage.")
                hide_loading(loading_dialog)
                show_success_and_redirect("/clients", "Bem-vindo de volta!")
            else:
                hide_loading(loading_dialog)
                status_text.value = "Erro ao pegar seu ID. Tenta de novo!"
                page.update()
        elif status == "pendente":
            hide_loading(loading_dialog)
            status_text.value = "Conta não ativada. Ative primeiro!"
            page.update()
        else:
            hide_loading(loading_dialog)
            status_text.value = "Usuário ou senha inválidos. Tenta novamente!"
            logger.warning(f"Falha no login para {username}: status={status}")
            page.update()

    login_button.on_click = login

    page.clean()
    form_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                    username_field,
                    password_field,
                    status_text,
                    login_button,
                    ft.Row([register_button, activate_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
        ),
        elevation=8,
        width=350,
    )
    page.update()

    return ft.Container(content=form_card, alignment=ft.alignment.center, expand=True)
