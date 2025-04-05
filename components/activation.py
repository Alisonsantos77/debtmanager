from time import sleep
import flet as ft
import logging
from utils.supabase_utils import validate_user, update_user_status, fetch_user_id, fetch_user_data, fetch_plan_data
from datetime import datetime, timezone, timedelta
import os
logger = logging.getLogger(__name__)


def ActivationPage(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300, border_color=ft.Colors.BLUE)
    activation_code_field = ft.TextField(label="Código", width=300, border_color=ft.Colors.BLUE, password=True)
    status_text = ft.Text("", color=ft.Colors.RED)
    activate_button = ft.ElevatedButton("Ativar", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
    login_button = ft.TextButton("Acessar", on_click=lambda _: page.go("/login"))
    prefix = os.getenv("PREFIX")

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

    def activate(e):
        username = username_field.value.strip()
        code = activation_code_field.value.strip()
        if not username or not code:
            status_text.value = "Preencha todos os campos!"
            page.update()
            return

        loading_dialog = show_loading()
        status, user = validate_user(username, code, encrypted=True, page=page)
        if status == "pendente" and user:
            now = datetime.now(timezone.utc)
            session_expiry = now + timedelta(hours=24)
            update_user_status(username, "ativo", {"data_expiracao": (now + timedelta(days=30)).isoformat()}, page)
            user_id = fetch_user_id(username, page)
            user_data = fetch_user_data(user_id, page)
            plan_id = user_data.get("plan_id", 1)
            plan_data = fetch_plan_data(plan_id, page) or {"name": "basic"}
        
            page.client_storage.set(f"{prefix}username", username)
            page.client_storage.set(f"{prefix}user_id", user_id)
            page.client_storage.set(f"{prefix}session_expiry", session_expiry.isoformat())
            page.client_storage.set(f"{prefix}user_plan", plan_data.get("name", "basic"))
            page.client_storage.set(f"{prefix}messages_sent", user_data.get("messages_sent", 0))
            page.client_storage.set(f"{prefix}pdfs_processed", user_data.get("pdfs_processed", 0))
            logger.info(f"Conta ativada para {username}. Dados salvos no client_storage.")
            hide_loading(loading_dialog)
            show_success_and_redirect("/clients", "Conta ativada! Bem-vindo!")
        elif status == "ativo" and user:
            hide_loading(loading_dialog)
            status_text.value = "Conta já ativada."
            show_success_and_redirect("/login", "Redirecionando para login...")
        else:
            hide_loading(loading_dialog)
            status_text.value = "Usuário não encontrado ou código inválido."
            logger.warning(f"Falha na ativação para {username}: status={status}")
            page.update()

    activate_button.on_click = activate

    page.clean()
    form_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Ativação", size=24, weight=ft.FontWeight.BOLD),
                    username_field,
                    activation_code_field,
                    status_text,
                    activate_button,
                    login_button,
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
