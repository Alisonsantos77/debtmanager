import logging
import os
import flet as ft
import flet_lottie as fl
from dotenv import load_dotenv
import random
import smtplib
from email.mime.text import MIMEText
from time import sleep
from flet.security import encrypt

from utils.supabase_utils import write_supabase

load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SUPPORT_EMAIL = "Alisondev77@hotmail.com"
SECRET_KEY = os.getenv("MY_APP_SECRET_KEY")
LOTTIE_REGISTER = os.getenv("LOTTIE_REGISTER")
logger = logging.getLogger(__name__)


class PlanCard(ft.Card):
    def __init__(self, plan_name: str, messages: str, pdfs: str, price: str, description: str, bgcolor: str, letter: str):
        super().__init__(
            content=ft.Container(
                content=ft.Column([
                    ft.CircleAvatar(content=ft.Text(letter), bgcolor=bgcolor, color=ft.Colors.WHITE),
                    ft.Text(plan_name, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(messages),
                    ft.Text(pdfs),
                    ft.Text(f"R$ {price}", size=16, color=ft.Colors.GREEN),
                    ft.Text(description, italic=True)
                ],
                    alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20),
            elevation=5,
            col={"xs": 12, "sm": 6, "md": 4}
        )


def RegisterPage(page: ft.Page):
    page.scroll = ft.ScrollMode.HIDDEN
    register_btn = ft.Ref[ft.ElevatedButton]()

    username_field = ft.TextField(
        label="Username",
        width=300,
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE,
        border_radius=10,
    )
    email_field = ft.TextField(
        label="Email",
        width=300,
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE,
        border_radius=10,
        keyboard_type="email",
        prefix_icon=ft.icons.EMAIL,
    )
    plan_dropdown = ft.Dropdown(
        label="Escolher Plano",
        options=[
            ft.dropdown.Option("basic"),
            ft.dropdown.Option("pro"),
            ft.dropdown.Option("enterprise")
        ],
        value="basic",
        width=300,
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE_400
    )
    status_text = ft.Text("", color=ft.Colors.RED)
    # Checkbox para Termos
    terms_checkbox = ft.Checkbox(
        label="Li e aceito os Termos de Uso e a Política de Privacidade",
        value=False,
    )
    terms_link = ft.TextButton(
        "Leia aqui",
        style=ft.ButtonStyle(color=ft.Colors.BLUE_700),
        on_click=lambda _: page.go("/terms")
    )
    terms_row = ft.Column([terms_checkbox, terms_link], alignment=ft.MainAxisAlignment.CENTER,
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
    register_button = ft.ElevatedButton(
        "Registrar",
        bgcolor=ft.Colors.GREY_400,
        color=ft.Colors.WHITE,
        width=300,
        height=50,
        style=ft.ButtonStyle(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        disabled=True,
        ref=register_btn
    )

    plans_data = {
        "basic": {"id": 1, "message_limit": 100, "pdf_limit": 5, "price": "150.00"},
        "pro": {"id": 2, "message_limit": 200, "pdf_limit": 15, "price": "250.00"},
        "enterprise": {"id": 3, "message_limit": 500, "pdf_limit": 30, "price": "400.00"}
    }

    def show_success_and_redirect(route, message="Sucesso!"):
        success_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN),
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

    def update_button(e):
        if terms_checkbox.value:
            register_btn.current.disabled = False
            register_btn.current.bgcolor = ft.Colors.BLUE
            register_btn.current.color = ft.Colors.WHITE
        else:
            register_btn.current.disabled = True
            register_btn.current.bgcolor = ft.Colors.GREY_400
            register_btn.current.color = ft.Colors.WHITE
        page.update()

    terms_checkbox.on_change = update_button

    def register_user(e):
        if not terms_checkbox.value:
            status_text.value = "Você precisa aceitar os Termos de Uso e a Política de Privacidade!"
            page.update()
            return

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
                "pdfs_processed": 0,
                "accepted_terms": True
            }
        ):
            page.client_storage.set("username", username)
            page.client_storage.set("plan_id", plans_data[plan]["id"])
            hide_loading(loading_dialog)
            show_success_and_redirect(
                "/activation", f"Registro enviado! Aguarde ativação pelo suporte.")
        else:
            hide_loading(loading_dialog)
            status_text.value = "Erro ao registrar."
            page.update()

    register_button.on_click = register_user

    lottie_container = ft.Container(
        content=fl.Lottie(
            src=LOTTIE_REGISTER,
            background_loading=True,
            filter_quality=ft.FilterQuality.HIGH,
            repeat=True,
        ),
        width=400,
        height=350,
        alignment=ft.alignment.center
    )

    form_container = ft.Column(
        [
            ft.Text("Registrar Novo Usuário", size=24, weight=ft.FontWeight.BOLD),
            username_field,
            email_field,
            plan_dropdown,
            terms_row,
            register_button,
            status_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        width=400
    )

    top_row = ft.Row(
        [
            lottie_container,
            form_container
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30
    )

    plan_cards = ft.ResponsiveRow(
        [
            PlanCard("Básico", "100 mensagens/mês", "5 PDFs/mês", "150,00",
                     "Ideal para iniciantes!", ft.Colors.BLUE_700, "B"),
            PlanCard("Pro", "200 mensagens/mês", "15 PDFs/mês", "250,00",
                     "Mais poder para crescer!", ft.Colors.PURPLE_700, "P"),
            PlanCard("Enterprise", "500 mensagens/mês", "30 PDFs/mês", "400,00",
                     "Domine suas notificações!", ft.Colors.RED_700, "E")
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    return ft.Container(
        content=ft.Column(
            [
                top_row,
                ft.Divider(),
                ft.Text("Escolha seu Plano", size=20, weight=ft.FontWeight.BOLD),
                plan_cards
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        ),
        padding=20
    )
