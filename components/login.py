import flet as ft
from datetime import datetime, timezone, timedelta
from time import sleep
from utils.supabase_utils import validate_user, update_user_status


def create_login_page(page: ft.Page):
    username_field = ft.TextField(label="USER", width=300, border_color=ft.colors.BLUE)
    activation_code_field = ft.TextField(label="CODE", width=300, border_color=ft.colors.BLUE)
    status_text = ft.Text("", color=ft.colors.RED)
    activate_button = ft.ElevatedButton("ATIVA", bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
    login_button = ft.ElevatedButton("ACESSA", bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, visible=False)
    register_button = ft.TextButton("REGISTRA", on_click=lambda _: page.go("/register"))

    def show_success_and_redirect(route, message="Sucesso!"):
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

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()

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
                        ft.Row(controls=[login_button if login_button.visible else activate_button],
                               alignment=ft.MainAxisAlignment.CENTER),
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
        loading_dialog = show_loading()
        status, user = validate_user(username, code)
        if status == "pendente" and user:
            now = datetime.now(timezone.utc)
            update_user_status(username, "ativo", {"data_expiracao": (now + timedelta(days=30)).isoformat()})
            page.client_storage.set("username", username)
            page.client_storage.set("user_id", user["id"])
            hide_loading(loading_dialog)
            show_success_and_redirect("/clients", "Bem-vindo!")
            show_login_form()  # Após ativação, mudar para botão "ACESSA"
        elif status == "ativo" and user:
            hide_loading(loading_dialog)
            show_login_form()  # Se já ativo, exibir "ACESSA"
            status_text.value = "Usuário já ativado. Use 'ACESSA'."
        else:
            hide_loading(loading_dialog)
            render_form()
            status_text.value = "Código inválido."

    def login(e):
        username = username_field.value.strip()
        code = activation_code_field.value.strip()
        if not all([username, code]):
            status_text.value = "Preencha usuário e código!"
            page.update()
            return
        loading_dialog = show_loading()
        status, user = validate_user(username, code)
        if status == "ativo" and user:
            now = datetime.now(timezone.utc)
            update_user_status(username, "ativo", {"last_login": now.isoformat()})
            page.client_storage.set("username", username)
            page.client_storage.set("user_id", user["id"])
            hide_loading(loading_dialog)
            show_success_and_redirect("/clients", "Login concluído!")
        else:
            hide_loading(loading_dialog)
            render_form()
            status_text.value = "Código inválido, expirado ou usuário inativo."

    activate_button.on_click = activate
    login_button.on_click = login

    # Verificar status inicial do usuário
    pending_username = page.client_storage.get("pending_username")
    saved_username = page.client_storage.get("username")
    saved_code = page.client_storage.get("activation_code")  # Assumindo que o código pode estar salvo
    if saved_username and saved_code:
        status, _ = validate_user(saved_username, saved_code)
        if status == "ativo":
            show_login_form()  # Mostrar "ACESSA" se já ativo
        else:
            render_form()  # Mostrar "ATIVA" se não ativo
    elif pending_username:
        username_field.value = pending_username
        render_form()
    else:
        username_field.value = saved_username or ""
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
