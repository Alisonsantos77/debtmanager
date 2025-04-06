import logging
import os
from datetime import datetime, timedelta, timezone
from time import sleep

import flet as ft
import flet_lottie as fl

from utils.supabase_utils import (fetch_plan_data, fetch_user_data,
                                  fetch_user_id, validate_user)

logger = logging.getLogger(__name__)


def LoginPage(page: ft.Page):
    lottie_url = os.getenv("LOTTIE_LOGIN")
    
    login_lottie = fl.Lottie(
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
        "Bora organizar as finanças e mandar ver nas cobranças!",
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
    password_field = ft.TextField(
        label="Senha/Code",
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

    login_button = ft.ElevatedButton(
        "Entrar",
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.HOVERED: ft.Colors.BLUE_500,
                ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
            },
            color=ft.Colors.WHITE,
            elevation={"pressed": 2, "": 5},
            animation_duration=300,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=320,
        height=50,
    )

    register_row = ft.Row(
        [
            ft.Text("Ainda não possui uma conta?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Registre aqui",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/register")
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    activate_row = ft.Row(
        [
            ft.Text("Já tem conta, mas não ativou?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Ative aqui",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/activation")
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

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
                prefix = os.getenv("PREFIX")
                user_data = fetch_user_data(user_id, page)
                plan_id = user_data.get("plan_id", 1)
                plan_data = fetch_plan_data(plan_id, page) or {"name": "basic"}
                page.client_storage.set(f"{prefix}username", username)
                page.client_storage.set(f"{prefix}user_id", user_id)
                page.client_storage.set(f"{prefix}session_expiry", (datetime.now(
                    timezone.utc) + timedelta(hours=24)).isoformat())
                page.client_storage.set(f"{prefix}user_plan", plan_data.get("name", "basic"))
                page.client_storage.set(f"{prefix}messages_sent", user_data.get("messages_sent", 0))
                page.client_storage.set(f"{prefix}pdfs_processed", user_data.get("pdfs_processed", 0))
                logger.info(f"Login bem-sucedido para {username}. Dados salvos no client_storage.")
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
    layout_login = ft.ResponsiveRow(
        controls=[
            ft.Row(
                controls=[welcome_text],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            # Lado esquerdo: Lottie
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},  
                controls=[
                    login_lottie,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            # Lado direito: Formulário de login
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    ft.Container(height=20),
                    username_field,
                    password_field,
                    status_text,
                    login_button,
                    ft.Container(height=15),
                    register_row,
                    activate_row,
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

    return layout_login
