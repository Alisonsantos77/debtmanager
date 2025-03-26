from datetime import datetime
from time import sleep
import flet as ft
import logging
import requests
from utils.auth import validate_user, update_user_last_login, verificar_status_usuario
from flet.security import decrypt
from dotenv import load_dotenv
import os
from animations import loading_animation, success_animation

load_dotenv()
SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")

logger = logging.getLogger(__name__)

def create_login_page(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300, border_color=ft.colors.BLUE)
    activation_code_field = ft.TextField(label="Código de Ativação", width=300, border_color=ft.colors.BLUE)
    password_field = ft.TextField(label="Senha", password=True, width=300, visible=False, border_color=ft.colors.BLUE)
    
    status_text = ft.Text("", color=ft.colors.RED)
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

    activate_button = ft.ElevatedButton("Ativar", bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    access_button = ft.ElevatedButton("Acessar", visible=False, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    login_button = ft.ElevatedButton("Entrar", visible=False, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    register_button = ft.TextButton("Registrar", on_click=lambda _: page.go("/register"), visible=False)

    def update_status(username, new_status):
        headers = {
            "apikey": SUPABASE_KEY_USERS,
            "Authorization": f"Bearer {SUPABASE_KEY_USERS}",
            "Content-Type": "application/json"
        }
        url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}"
        data = {"status": new_status, "activation_code": None}
        try:
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"Status de {username} atualizado para {new_status}")
        except requests.RequestException as e:
            logger.error(f"Erro ao atualizar status de {username}: {e}")

    def render_form():
        page.clean()
        form_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                        username_field,
                        activation_code_field,
                        password_field,
                        status_text,
                        ft.Row(
                            controls=[login_button, activate_button, access_button, progress_ring],
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
        activation_code_field.visible = False
        activate_button.visible = False
        access_button.visible = False
        password_field.visible = True
        login_button.visible = True
        register_button.visible = True
        status_text.value = ""
        progress_ring.visible = False
        render_form()

    def show_loading(message="Processando..."):
        page.clean()
        anim = loading_animation(message)
        page.add(anim)
        page.update()

    def show_success_and_redirect(username, user_id, email):
        page.clean()
        anim = success_animation("Ativação concluída com sucesso!")
        page.add(anim)
        page.update()
        page.client_storage.set("user_id", user_id)
        page.client_storage.set("username", username)
        page.client_storage.set("email", email)
        sleep(3)
        page.go("/clients")
        page.update()

    def activate(e):
        username = username_field.value.strip()
        code = activation_code_field.value.strip()
        if not all([username, code]):
            status_text.value = "Preencha usuário e código!"
            page.update()
            return

        show_loading("Ativando...")

        headers = {
            "apikey": SUPABASE_KEY_USERS,
            "Authorization": f"Bearer {SUPABASE_KEY_USERS}"
        }
        url = f"{SUPABASE_URL_USERS}/rest/v1/users_debt?username=eq.{username}&select=activation_code,status,id,email"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            if not user_data:
                page.clean()
                render_form()
                status_text.value = "Usuário não encontrado."
                page.update()
                return
            user = user_data[0]
            if user["status"] != "pendente":
                page.clean()
                render_form()
                status_text.value = "Usuário já ativado ou inativo."
                page.update()
                return

            decrypted_code = decrypt(user["activation_code"], SECRET_KEY)
            if decrypted_code == code:
                update_status(username, "ativo")
                show_success_and_redirect(username, user["id"], user["email"])
                logger.info(f"Usuário {username} ativado e logado com sucesso.")
            else:
                page.clean()
                render_form()
                status_text.value = "Código inválido. Tente novamente."
                page.update()
        except Exception as ex:
            page.clean()
            render_form()
            status_text.value = "Erro ao ativar. Tente novamente."
            logger.error(f"Erro ao ativar {username}: {ex}")
            page.update()

    def access(e):
        page.clean()
        username_field.value = ""
        password_field.visible = True
        login_button.visible = True
        register_button.visible = True
        activation_code_field.visible = False
        activate_button.visible = False
        access_button.visible = False
        progress_ring.visible = False
        render_form()

    def login(e):
        username = username_field.value.strip()
        password = password_field.value.strip()
        if not all([username, password]):
            status_text.value = "Preencha todos os campos!"
            page.update()
            return
        show_loading("Entrando...")
        status, user = validate_user(username, password)
        if status == "success":
            page.client_storage.set("user_id", user["id"])
            page.client_storage.set("username", username)
            page.client_storage.set("email", user.get("email", ""))
            update_user_last_login(str(user["id"]), datetime.now().isoformat())
            page.go("/clients")
            logger.info(f"Usuário {username} logado com sucesso.")
        elif status == "inactive":
            page.clean()
            render_form()
            status_text.value = "Conta inativa. Contate o suporte."
            page.update()
        else:
            page.clean()
            render_form()
            status_text.value = "Usuário ou senha inválidos."
            page.update()

    # Associação dos eventos aos botões
    activate_button.on_click = activate
    access_button.on_click = access
    login_button.on_click = login

    pending_username = page.client_storage.get("pending_username")
    if not pending_username:
        show_login_form()
    else:
        activation_code_field.visible = True
        activate_button.visible = True
        password_field.visible = False
        login_button.visible = False
        register_button.visible = False
        render_form()

    return ft.Column(
        controls=[
            ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
            username_field,
            activation_code_field,
            password_field,
            status_text,
            ft.Row([activate_button, access_button, progress_ring], alignment=ft.MainAxisAlignment.CENTER),
            login_button,
            register_button
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

