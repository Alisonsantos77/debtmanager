import flet as ft
import logging
import requests
import os
import smtplib
import random
import string
from flet.security import encrypt
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")

logger = logging.getLogger(__name__)


def generate_random_password(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def generate_activation_code(length=6):
    return ''.join(random.choice(string.digits) for _ in range(length))


def send_verification_email(username, email, code, password):
    msg = MIMEText(
        f"Novo registro:\nUsuário: {username}\nEmail: {email}\nCódigo de ativação: {code}\nSenha: {password}")
    msg['Subject'] = "Novo Registro no DebtManager"
    msg['From'] = EMAIL_SENDER
    msg['To'] = "Alisondev77@hotmail.com"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email de verificação enviado para Alisondev77@hotmail.com para o usuário {username}")
    except Exception as e:
        logger.error(f"Erro ao enviar email para Alison: {e}")

    user_msg = MIMEText(f"Seu código de ativação para o DebtManager é: {code}")
    user_msg['Subject'] = "Código de Ativação - DebtManager"
    user_msg['From'] = EMAIL_SENDER
    user_msg['To'] = email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(user_msg)
        logger.info(f"Código de ativação enviado para {email}")
    except Exception as e:
        logger.error(f"Erro ao enviar email ao usuário {email}: {e}")


def create_register_page(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300)
    email_field = ft.TextField(label="Email", width=300)
    error_text = ft.Text("", color=ft.Colors.RED)
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

    def register(e):
        username = username_field.value.strip()
        email = email_field.value.strip()
        if not all([username, email]):
            error_text.value = "Preencha usuário e email!"
            page.update()
            return

        if not SUPABASE_URL_USERS or not SUPABASE_KEY_USERS or not SECRET_KEY:
            error_text.value = "Erro de configuração do servidor. Contate o suporte."
            logger.error("Variáveis de ambiente não configuradas.")
            page.update()
            return

        progress_ring.visible = True
        page.update()

        generated_password = generate_random_password()
        activation_code = generate_activation_code()
        encrypted_code = encrypt(activation_code, SECRET_KEY)

        headers = {
            "apikey": SUPABASE_KEY_USERS,
            "Authorization": f"Bearer {SUPABASE_KEY_USERS}",
            "Content-Type": "application/json"
        }
        data = {
            "username": username,
            "password_hash": encrypt(generated_password, SECRET_KEY),
            "email": email,
            "last_login": None,
            "data_expiracao": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "pendente",
            "activation_code": encrypted_code
        }
        try:
            response = requests.post(f"{SUPABASE_URL_USERS}/rest/v1/users_debt", headers=headers, json=data)
            response.raise_for_status()
            send_verification_email(username, email, activation_code, generated_password)
            page.client_storage.set("pending_username", username)
            progress_ring.visible = False
            page.snack_bar = ft.SnackBar(
                ft.Text("Registro concluído! Verifique seu email para o código."), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True
            page.go("/login")
            logger.info(f"Usuário {username} registrado com sucesso.")
        except requests.RequestException as e:
            progress_ring.visible = False
            error_text.value = "Erro ao registrar. Tente novamente."
            logger.error(f"Erro ao registrar {username}: {e}")
            page.update()

    return ft.Column([
        ft.Text("Registro", size=24, weight=ft.FontWeight.BOLD),
        username_field,
        email_field,
        error_text,
        ft.Row([ft.ElevatedButton("Registrar", on_click=register, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE), progress_ring]),
        ft.TextButton("Já tem conta? Login", on_click=lambda _: page.go("/login"))
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
