import flet as ft
import logging
import requests
from flet.security import decrypt
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
from time import sleep

load_dotenv()
SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}
logger = logging.getLogger(__name__)


def show_loading(page, message="Processando..."):
    loading_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text(message, size=18, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
        ),
        bgcolor=ft.colors.TRANSPARENT,
        modal=True,
        disabled=True,
    )
    page.open(loading_dialog)
    page.update()
    sleep(1)


def show_success_and_redirect(page, route, message="Sucesso!"):
    success_dialog = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.CHECK_CIRCLE, size=50, color=ft.colors.GREEN),
                    ft.Text(message, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
        ),
        bgcolor=ft.colors.TRANSPARENT,
        modal=True,
        disabled=True,
    )
    page.open(success_dialog)
    page.update()
    sleep(3)
    page.close(success_dialog)
    page.go(route)


def create_login_page(page: ft.Page):
    username_field = ft.TextField(label="USER", width=300, border_color=ft.colors.BLUE)
    activation_code_field = ft.TextField(label="CODE", width=300, border_color=ft.colors.BLUE)
    status_text = ft.Text("", color=ft.colors.RED)
    activate_button = ft.ElevatedButton("ATIVA", bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    login_button = ft.ElevatedButton("ACESSA", visible=False, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    register_button = ft.TextButton("REGISTRA", on_click=lambda _: page.go("/register"))

    def render_form():
        page.clean()
        form_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("LOGIN", size=24, weight=ft.FontWeight.BOLD),
                        username_field,
                        activation_code_field,
                        status_text,
                        ft.Row(
                            controls=[login_button, activate_button],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        register_button
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center,
            ),
            elevation=8,
            width=350
        )
        page.add(ft.Container(content=form_card, alignment=ft.alignment.center, expand=True))
        page.update()

    def show_login_form():
        activate_button.visible = False
        login_button.visible = True
        status_text.value = ""
        render_form()

    def activate(e):
        username = username_field.value.strip()
        code = activation_code_field.value.strip()
        if not all([username, code]):
            status_text.value = "Preencha usuário e código!"
            page.update()
            return
        show_loading(page, "Ativando...")
        user_data = requests.get(
            f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}", headers=headers).json()
        user = user_data[0] if user_data else None
        if user and decrypt(user["activation_code"], SECRET_KEY) == code and user["status"] == "pendente":
            now = datetime.now(timezone.utc)
            requests.patch(f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}",
                           headers=headers, json={
                               "status": "ativo",
                               "data_expiracao": (now + timedelta(days=30)).isoformat()
            })
            page.client_storage.set("username", username)
            page.client_storage.set("user_id", user["id"])
            show_success_and_redirect(page, "/clients", "Bem-vindo!")
        else:
            page.clean()
            status_text.value = "Código inválido ou usuário já ativo."
            show_login_form()

    def login(e):
        username = username_field.value.strip()
        code = activation_code_field.value.strip()
        if not all([username, code]):
            status_text.value = "Preencha usuário e código!"
            page.update()
            return
        show_loading(page, "Entrando...")
        user_data = requests.get(
            f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}", headers=headers).json()
        user = user_data[0] if user_data else None
        if user and decrypt(user["activation_code"], SECRET_KEY) == code and user["status"] == "ativo":
            now = datetime.now(timezone.utc)
            requests.patch(f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}",
                           headers=headers, json={"last_login": now.isoformat()})
            page.client_storage.set("username", username)
            page.client_storage.set("user_id", user["id"])
            show_success_and_redirect(page, "/clients", "Login concluído!")
        else:
            page.clean()
            render_form()
            status_text.value = "Código inválido, expirado ou usuário inativo."
            page.update()

    activate_button.on_click = activate
    login_button.on_click = login

    pending_username = page.client_storage.get("pending_username")
    if not pending_username:
        username_field.value = page.client_storage.get("username") or ""
        show_login_form()
    else:
        username_field.value = pending_username
        login_button.visible = False
        render_form()

    return ft.Column(
        controls=[
            ft.Text("LOGIN", size=24, weight=ft.FontWeight.BOLD),
            username_field,
            activation_code_field,
            status_text,
            ft.Row([activate_button], alignment=ft.MainAxisAlignment.CENTER),
            login_button,
            register_button
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
