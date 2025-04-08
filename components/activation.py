import logging
import os
from datetime import datetime, timedelta, timezone
from time import sleep
import flet as ft
import flet_lottie as fl
from utils.supabase_utils import (fetch_plan_data, fetch_user_data,
                                  fetch_user_id, update_user_status,
                                  validate_user)

logger = logging.getLogger(__name__)


def ActivationPage(page: ft.Page):
    lottie_url = os.getenv("LOTTIE_ACTIVATION")
    terms_checkbox_ref = ft.Ref[ft.Checkbox]()
    activate_button_ref = ft.Ref[ft.ElevatedButton]()
    activation_lottie = fl.Lottie(
        src=lottie_url,
        width=400,
        height=400,
        repeat=True,
        animate=True,
        background_loading=True,
        filter_quality=ft.FilterQuality.HIGH,
        fit=ft.ImageFit.CONTAIN,
    )

    welcome_text = ft.Text(
        "Ative sua conta e comece agora!",
        size=18,
        color=ft.Colors.BLUE_GREY_700,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    username_field = ft.TextField(
        label="Usuário",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
    )
    activation_code_field = ft.TextField(
        label="Código",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        password=True,
        can_reveal_password=True,
    )
    status_text = ft.Text("", color=ft.Colors.RED_400, size=14, italic=True)
    terms_checkbox = ft.Checkbox(
        label="Reafirmo que li e aceito os Termos de Uso e a Política de Privacidade",
        value=False,
        check_color=ft.Colors.BLUE_400,
        ref=terms_checkbox_ref
    )
    terms_link = ft.TextButton(
        "Leia aqui",
        style=ft.ButtonStyle(color=ft.Colors.BLUE_700),
        on_click=lambda _: page.go("/terms")
    )
    terms_row = ft.Column([terms_checkbox, terms_link], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
    activate_button = ft.ElevatedButton(
        "Ativar",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_400,
            color=ft.Colors.WHITE,            elevation={"pressed": 2, "": 5},
            animation_duration=300,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        width=320,
        height=50,
        disabled=True,
        ref=activate_button_ref,
    )

    login_row = ft.Row(
        [
            ft.Text("Já ativou sua conta?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Acesse aqui",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/login")
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    prefix = os.getenv("PREFIX")

    def show_success_and_redirect(route, message="Sucesso!"):
        success_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN_400),
                        ft.Text(message, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
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
            content=ft.Container(content=ft.ProgressRing(color=ft.Colors.BLUE_400), alignment=ft.alignment.center),
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

    def update_button(e):
        if terms_checkbox.value:
            activate_button_ref.current.disabled = False
            activate_button_ref.current.bgcolor = ft.Colors.BLUE
            activate_button_ref.current.color = ft.Colors.WHITE
            activate_button_ref.current.update()
        else:
            activate_button_ref.current.disabled = True
            activate_button_ref.current.bgcolor = ft.Colors.GREY_400
            activate_button_ref.current.color = ft.Colors.WHITE
            activate_button_ref.current.update()
        page.update()

    terms_checkbox.on_change = update_button

    def activate(e):
        if not terms_checkbox.value:
            status_text.value = "Você precisa aceitar os Termos de Uso e a Política de Privacidade!"
            page.update()
            return

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
            data_expiracao = now + timedelta(days=30)
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
            page.client_storage.set(f"{prefix}data_expiracao", data_expiracao.isoformat()
                                    )
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
    layout_activation = ft.ResponsiveRow(
        controls=[
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    activation_lottie,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    welcome_text,
                    ft.Container(height=20),
                    username_field,
                    activation_code_field,
                    terms_row, 
                    status_text,
                    activate_button,
                    ft.Container(height=15),
                    login_row,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        columns=12,
    )

    page.update()

    return layout_activation
