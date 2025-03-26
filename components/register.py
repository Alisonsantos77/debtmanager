import flet as ft
import logging
import requests
import os
import smtplib
from flet.security import encrypt
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime
from animations import loading_animation, success_animation
from time import sleep
import random
import string

load_dotenv()
SUPABASE_KEY_USERS = os.getenv("SUPABASE_KEY_USERS")
SUPABASE_URL_USERS = os.getenv("SUPABASE_URL_USERS")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
headers = {"apikey": SUPABASE_KEY_USERS, "Authorization": f"Bearer {SUPABASE_KEY_USERS}", "Content-Type": "application/json"}
logger = logging.getLogger(__name__)


def generate_activation_code(length=6):
    return ''.join(random.choice(string.digits) for _ in range(length))


def send_verification_email(username, email, code):
    msg = MIMEText(f"Novo registro:\nUsuário: {username}\nEmail: {email}\nCódigo de ativação: {code}")
    msg['Subject'] = "Novo Registro no DebtManager"
    msg['From'] = EMAIL_SENDER
    msg['To'] = "Alisondev77@hotmail.com"
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    logger.info(f"Email de verificação enviado para Alisondev77@hotmail.com para o usuário {username}")


def show_loading(page, message="Processando..."):
    page.clean()
    page.add(loading_animation(message))
    page.update()


def show_success_and_redirect(page, route, message="Sucesso!"):
    page.clean()
    page.add(success_animation(message))
    page.update()
    sleep(2)
    page.go(route)


def create_register_page(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300)
    email_field = ft.TextField(label="Email", width=300)
    error_text = ft.Text("", color=ft.Colors.RED)

    def register(e):
        username = username_field.value.strip()
        email = email_field.value.strip()
        if not all([username, email]):
            error_text.value = "Preencha usuário e email!"
            page.update()
            return
        show_loading(page, "Registrando...")
        activation_code = generate_activation_code()
        encrypted_code = encrypt(activation_code, SECRET_KEY)
        data = {
            "username": username,
            "email": email,
            "activation_code": encrypted_code,
            "status": "pendente"
        }
        response = requests.post(f"{SUPABASE_URL_USERS}/rest/v1/users_debt", headers=headers, json=data)
        if response.ok:
            send_verification_email(username, email, activation_code)
            page.client_storage.set("pending_username", username)
            show_success_and_redirect(page, "/login", "Registro concluído! Código enviado ao suporte.")
        else:
            page.clean()
            render_form()
            error_text.value = "Erro ao registrar."
            page.update()

    def render_form():
        page.clean()
        form_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Registro", size=24, weight=ft.FontWeight.BOLD),
                        username_field,
                        email_field,
                        error_text,
                        ft.ElevatedButton("Registrar", on_click=register,
                                          bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                        ft.TextButton("Já tem conta? Login", on_click=lambda _: page.go("/login"))
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

    render_form()

    return ft.Column([
        ft.Text("Registro", size=24, weight=ft.FontWeight.BOLD),
        username_field,
        email_field,
        error_text,
        ft.ElevatedButton("Registrar", on_click=register, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
        ft.TextButton("Já tem conta? Login", on_click=lambda _: page.go("/login"))
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
