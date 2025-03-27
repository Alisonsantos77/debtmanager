import flet as ft
from time import sleep
import random
import string
from utils.supabase_utils import write_supabase
from flet.security import encrypt
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")


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


def create_register_page(page: ft.Page):
    username_field = ft.TextField(label="Usuário", width=300)
    email_field = ft.TextField(label="Email", width=300)
    error_text = ft.Text("", color=ft.Colors.RED)

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

    def register(e):
        username = username_field.value.strip()
        email = email_field.value.strip()
        if not all([username, email]):
            error_text.value = "Preencha usuário e email!"
            page.update()
            return
        loading_dialog = show_loading()
        activation_code = generate_activation_code()
        encrypted_code = encrypt(activation_code, SECRET_KEY)
        data = {
            "username": username,
            "email": email,
            "activation_code": encrypted_code,
            "status": "pendente"
        }
        if write_supabase("users_debt", data):
            send_verification_email(username, email, activation_code)
            # Salvar username e activation_code no client_storage
            page.client_storage.set("pending_username", username)
            page.client_storage.set("activation_code", activation_code)
            page.client_storage.set("username", username)  # Salvar também como username para consistência
            hide_loading(loading_dialog)
            show_success_and_redirect("/login", "Registro concluído! Código enviado ao suporte.")
        else:
            hide_loading(loading_dialog)
            render_form()
            error_text.value = "Erro ao registrar."

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
