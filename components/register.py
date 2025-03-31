import flet as ft
import logging
from utils.supabase_utils import write_supabase
from flet.security import encrypt
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from time import sleep
import random

load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SUPPORT_EMAIL = "Alisondev77@hotmail.com"
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")

logger = logging.getLogger(__name__)


def RegisterPage(page: ft.Page):
    username_field = ft.TextField(label="Username", width=300, border_color=ft.Colors.BLUE)
    email_field = ft.TextField(label="Email", width=300, border_color=ft.Colors.BLUE)
    plan_dropdown = ft.Dropdown(
        label="Escolher Plano",
        options=[
            ft.dropdown.Option("basic"),
            ft.dropdown.Option("pro"),
            ft.dropdown.Option("enterprise")
        ],
        value="basic",
        width=300
    )
    status_text = ft.Text("", color=ft.Colors.RED)
    register_button = ft.ElevatedButton("Registrar", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)

    plans_data = {
        "basic": {"id": 1, "message_limit": 100, "pdf_limit": 5, "price": "150.00"},
        "pro": {"id": 2, "message_limit": 200, "pdf_limit": 15, "price": "250.00"},
        "enterprise": {"id": 3, "message_limit": 500, "pdf_limit": 30, "price": "400.00"}
    }

    plan_details = ft.Column([
        ft.Text("Detalhes dos Planos:", size=16, weight=ft.FontWeight.BOLD),
        ft.Text("Básico: 100 mensagens/mês, 5 PDFs/mês, R$ 150,00", size=14),
        ft.Text("Pro: 200 mensagens/mês, 15 PDFs/mês, R$ 250,00", size=14),
        ft.Text("Enterprise: 500 mensagens/mês, 30 PDFs/mês, R$ 400,00", size=14)
    ], spacing=5)

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

    def register_user(e):
        username = username_field.value.strip()
        email = email_field.value.strip()
        plan = plan_dropdown.value
        if not username or not email or not plan:
            status_text.value = "Preencha todos os campos!"
            page.update()
            return

        loading_dialog = show_loading()
        activation_code = str(random.randint(100000, 999999))
        encrypted_code = encrypt(activation_code, SECRET_KEY)
        plan_info = plans_data[plan]
        try:
            msg = MIMEText(
                f"Solicitação de Registro e Ativação:\n"
                f"Usuário: {username}\n"
                f"Email: {email}\n"
                f"Plano Escolhido: {plan}\n"
                f"Limites: {plan_info['message_limit']} mensagens/mês, {plan_info['pdf_limit']} PDFs/mês\n"
                f"Preço: R$ {plan_info['price']}\n"
                f"Código de Ativação: {activation_code}"
            )
            msg['Subject'] = "Solicitação de Registro - DebtManager"
            msg['From'] = EMAIL_SENDER
            msg['To'] = SUPPORT_EMAIL
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email de registro enviado para {SUPPORT_EMAIL}")
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            hide_loading(loading_dialog)
            status_text.value = "Erro ao enviar solicitação."
            page.update()
            return

        if write_supabase(
            "users_debt",
            {
                "username": username,
                "email": email,
                "status": "pendente",
                "activation_code": encrypted_code,
                "plan_id": plans_data[plan]["id"],
                "messages_sent": 0,
                "pdfs_processed": 0
            }
        ):
            page.client_storage.set("username", username)
            page.client_storage.set("plan_id", plans_data[plan]["id"])  # Armazena plan_id no client_storage
            hide_loading(loading_dialog)
            show_success_and_redirect(
                "/activation", f"Registro enviado! Código: {activation_code}\nAguarde ativação pelo suporte.")
        else:
            hide_loading(loading_dialog)
            status_text.value = "Erro ao registrar."
            page.update()

    register_button.on_click = register_user

    return ft.Column(
        [
            ft.Text("Registrar Novo Usuário", size=24, weight=ft.FontWeight.BOLD),
            username_field,
            email_field,
            plan_dropdown,
            plan_details,
            register_button,
            status_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
    )
