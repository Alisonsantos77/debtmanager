import os
import flet as ft
import smtplib
from email.mime.text import MIMEText
from utils.supabase_utils import read_supabase, write_supabase
from utils.theme_utils import get_current_color_scheme
from secrets import token_urlsafe
import logging
import random
from dotenv import load_dotenv
import base64
from components.app_layout import get_usage_data  # Importa pra usar o Client Storage

load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SUPPORT_EMAIL = "Alisondev77@hotmail.com"
URL_DICEBEAR = os.getenv("URL_DICEBEAR")
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
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20
            ),
            elevation=5,
            col={"xs": 12, "sm": 6, "md": 4}
        )


def ProfilePage(page: ft.Page, company_data: dict, app_state: dict):
    current_color_scheme = get_current_color_scheme(page)
    avatar_img = ft.Ref[ft.CircleAvatar]()

    prefix = os.getenv("PREFIX")
    username = page.client_storage.get(f"{prefix}username") or "Debt Manager"
    user_id = page.client_storage.get(f"{prefix}user_id")
    saved_avatar = page.client_storage.get(f"{prefix}avatar")
    if not username or not user_id:
        logger.warning("Username ou user_id não encontrados no client_storage. Redirecionando para login.")
        page.overlay.append(ft.SnackBar(
            ft.Text("Parece que você não tá logado. Vamos pro login!"), bgcolor=ft.Colors.RED))
        page.go("/login")
        page.update()
        return ft.Container()

    user_data = read_supabase("users_debt", f"?id=eq.{user_id}", page)
    current_email = user_data.get("email", "Alisondev77@hotmail.com") if user_data else "Alisondev77@hotmail.com"
    current_plan_id = user_data.get("plan_id", 1) if user_data else 1
    usage_data = get_usage_data(page)

    plans_data = [
        {"id": 1, "name": "basic", "message_limit": 100, "pdf_limit": 5, "price": "150.00"},
        {"id": 2, "name": "pro", "message_limit": 200, "pdf_limit": 15, "price": "250.00"},
        {"id": 3, "name": "enterprise", "message_limit": 500, "pdf_limit": 30, "price": "400.00"}
    ]
    current_plan = next((p for p in plans_data if p["id"] == current_plan_id), plans_data[0])

    # Filtra opções de upgrade com base no plano atual
    available_plans = [p["name"] for p in plans_data if p["id"] > current_plan["id"]]
    plan_dropdown = ft.Dropdown(
        label="Escolher Novo Plano",
        options=[ft.dropdown.Option(plan) for plan in available_plans],
        width=200
    )
    upgrade_code_field = ft.TextField(label="Código de Upgrade", width=200)
    feedback_text = ft.Text("", color=ft.Colors.GREEN)

    avatar = ft.Stack(
        [
            ft.CircleAvatar(
                foreground_image_src=saved_avatar if saved_avatar else f"{URL_DICEBEAR}seed={username}",
                width=80,
                height=80,
                ref=avatar_img,
            ),
            ft.Container(
                content=ft.CircleAvatar(bgcolor=ft.Colors.GREEN, radius=5),
                alignment=ft.alignment.bottom_left,
            ),
        ],
        width=50,
        height=50,
    )

    def mudar_perfil(e):
        avatar_aleatorio = f"{URL_DICEBEAR}seed={random.randint(1000, 9999)}"
        novo_avatar = avatar_aleatorio if avatar_aleatorio else f"{URL_DICEBEAR}seed={username}"
        avatar_img.current.foreground_image_src = novo_avatar
        avatar_img.current.update()
        page.client_storage.set(f"{prefix}avatar", novo_avatar)
        page.update()



    def send_upgrade_request(username, email, current_plan, new_plan, code):
        current_info = next(p for p in plans_data if p["name"] == current_plan)
        new_info = next(p for p in plans_data if p["name"] == new_plan)
        try:
            msg = MIMEText(
                f"Solicitação de Upgrade:\n"
                f"Usuário: {username}\n"
                f"Email: {email}\n"
                f"De: {current_plan} (Limites: {current_info['message_limit']} mensagens/mês, {current_info['pdf_limit']} PDFs/mês, Preço: R$ {current_info['price']})\n"
                f"Para: {new_plan} (Limites: {new_info['message_limit']} mensagens/mês, {new_info['pdf_limit']} PDFs/mês, Preço: R$ {new_info['price']})\n"
                f"Código de Upgrade: {code}"
            )
            msg['Subject'] = "Solicitação de Upgrade - DebtManager"
            msg['From'] = EMAIL_SENDER
            msg['To'] = SUPPORT_EMAIL
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email de upgrade enviado para {SUPPORT_EMAIL}")
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            feedback_text.value = "Erro ao enviar solicitação."
            page.update()

    def request_upgrade(e):
        new_plan = plan_dropdown.value
        if not new_plan:
            page.open(ft.SnackBar(ft.Text("Selecione um plano!"), bgcolor=ft.Colors.RED))
            return
        upgrade_code = token_urlsafe(16)
        write_supabase(
            "upgrade_requests",
            {"user_id": user_id, "plan_id": next(p["id"] for p in plans_data if p["name"] == new_plan),
             "code": upgrade_code, "status": "pending"},
            page=page
        )
        send_upgrade_request(username, current_email, current_plan["name"], new_plan, upgrade_code)
        feedback_text.value = f"Pedido enviado! Código: {upgrade_code}"
        page.update()

    def apply_upgrade(e):
        code = upgrade_code_field.value.strip()
        logger.info(f"Tentando aplicar código: {code}")
        if not code:
            feedback_text.value = "Insira o código de upgrade!"
            page.open(ft.SnackBar(ft.Text("Insira o código de upgrade!"), bgcolor=ft.Colors.RED))
            page.update()
            return
        request = read_supabase("upgrade_requests", f"?user_id=eq.{user_id}&code=eq.{code}&status=eq.pending", page)
        logger.info(f"Resultado da consulta ao Supabase: {request}")
        if request and isinstance(request, list) and len(request) > 0:
            plan_id = request[0].get("plan_id")
            logger.info(f"Plan ID encontrado: {plan_id}")
            selected_plan = next((p for p in plans_data if p["id"] == plan_id), None)
            if selected_plan:
                logger.info(f"Plano selecionado: {selected_plan['name']}")
                page.client_storage.set(f"{prefix}messages_sent", 0)
                page.client_storage.set(f"{prefix}pdfs_processed", 0)
                write_supabase(f"users_debt?id=eq.{user_id}", {
                    "plan_id": selected_plan["id"], "messages_sent": 0, "pdfs_processed": 0
                }, method="patch", page=page)
                write_supabase(f"upgrade_requests?id=eq.{request[0]['id']}", {
                    "status": "approved"
                }, method="patch", page=page)
                page.client_storage.set(f"{prefix}user_plan", selected_plan["name"])
                app_state["user_plan"] = selected_plan["name"]
                feedback_text.value = f"Plano atualizado para {selected_plan['name']}!"
            else:
                logger.error(f"Plano com ID {plan_id} não encontrado em plans_data")
                feedback_text.value = "Plano não encontrado."
        else:
            logger.error(f"Requisição inválida ou não encontrada para código {code}")
            feedback_text.value = "Código inválido ou solicitação não encontrada."
        page.update()

    plan_cards = ft.ResponsiveRow([
        PlanCard("Básico", "100 mensagens/mês", "5 PDFs/mês", "150,00",
                 "Ideal para iniciantes!", ft.Colors.BLUE_700, "B"),
        PlanCard("Pro", "200 mensagens/mês", "15 PDFs/mês", "250,00",
                 "Mais poder para crescer!", ft.Colors.PURPLE_700, "P"),
        PlanCard("Enterprise", "500 mensagens/mês", "30 PDFs/mês", "400,00",
                 "Domine suas notificações!", ft.Colors.RED_700, "E")
    ], alignment=ft.MainAxisAlignment.CENTER)

    social_icons = ft.Row(
        controls=[
            ft.IconButton(content=ft.Image(src="images/contact/icons8-whatsapp-48.png", width=40, height=40),
                          icon_color=ft.Colors.GREEN, tooltip="Abrir WhatsApp",
                          url="https://wa.link/oebrg2",
                          style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.GREEN})),
            ft.IconButton(content=ft.Image(src="images/contact/outlook-logo.png", width=40, height=40),
                          icon_color=ft.Colors.PRIMARY, tooltip="Enviar Email",
                          url="mailto:Alisondev77@hotmail.com?subject=Feedback%20-%20DebtManager&body=Olá, gostaria de fornecer feedback.",
                          style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.BLUE})),
            ft.IconButton(content=ft.Image(src="images/contact/icons8-linkedin-48.png", width=40, height=40),
                          tooltip="Acessar LinkedIn",
                          url="https://www.linkedin.com/in/alisonsantosdev",
                          style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.BLUE})),
            ft.IconButton(content=ft.Image(src="images/contact/icons8-github-64.png", width=40, height=40),
                          icon_color=ft.Colors.PRIMARY, tooltip="Acessar GitHub",
                          url="https://github.com/Alisonsantos77",
                          style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.GREY})),
        ],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
    )

    profile_content = ft.Column([
        ft.Row([
            avatar,
            ft.Column([
                ft.Text(f"Bem-vindo, {username}!", size=24, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Mudar avatar", on_click=mudar_perfil)
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text(f"Email: {current_email}", size=16),
        ft.Text(f"Plano Atual: {current_plan['name']}", size=16),
        ft.Text(
            f"Consumo: {usage_data['messages_sent']}/{current_plan['message_limit']} mensagens | {usage_data['pdfs_processed']}/{current_plan['pdf_limit']} PDFs",
            size=14, color=current_color_scheme.on_surface
        ),
        ft.Divider(),
        ft.Text("Escolha seu Novo Plano", size=20, weight=ft.FontWeight.BOLD),
        plan_cards,
        ft.Row([plan_dropdown, ft.ElevatedButton("Solicitar Upgrade", on_click=request_upgrade)]),
        ft.Row([upgrade_code_field, ft.ElevatedButton("Aplicar Upgrade", on_click=apply_upgrade)]),
        feedback_text,
        ft.Divider(),
        ft.Text("Contato", size=20, weight=ft.FontWeight.BOLD),
        social_icons,
        ft.Divider(),
        ft.Text("Termos de Uso e Política de Privacidade", size=20, weight=ft.FontWeight.BOLD),
        ft.Text("Bem-vindo ao DebtManager!", size=16, weight=ft.FontWeight.BOLD),
        ft.Text("O DebtManager é uma ferramenta de automação para envio de notificações de dívidas, projetada para otimizar a gestão financeira de empresas e usuários individuais. Ao utilizar este aplicativo, você concorda com os seguintes termos:"),
        ft.Text("1. Uso Responsável: O DebtManager deve ser utilizado exclusivamente para fins legítimos e legais, como o envio de notificações de dívidas válidas. Qualquer uso indevido, incluindo spam ou assédio, resultará na suspensão da conta."),
        ft.Text("2. Privacidade e Segurança: Seus dados pessoais e financeiros são protegidos conforme a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018). Utilizamos criptografia para armazenar informações sensíveis e não compartilhamos seus dados com terceiros sem consentimento explícito."),
        ft.Text("3. Limites de Uso: Cada plano possui limites de mensagens e PDFs processados. Exceder esses limites requer upgrade de plano. Tentativas de burlar essas restrições podem levar ao bloqueio da conta."),
        ft.Text("4. Pagamento e Upgrades: Os planos são pagos e os upgrades requerem validação manual via código enviado ao suporte. Não há reembolsos após a ativação do plano."),
        ft.Text("5. Suporte e Responsabilidade: Oferecemos suporte técnico via email e WhatsApp. Não nos responsabilizamos por falhas causadas por uso incorreto do aplicativo ou por interrupções em serviços de terceiros (e.g., Twilio, Supabase)."),
        ft.Text("6. Atualizações e Disponibilidade: O DebtManager pode receber atualizações que modifiquem funcionalidades. Reservamo-nos o direito de suspender o serviço para manutenção sem aviso prévio."),
        ft.Text("Para dúvidas, entre em contato com nosso suporte em Alisondev77@hotmail.com ou via WhatsApp.")
    ], spacing=20, scroll=ft.ScrollMode.AUTO)

    return ft.Container(content=profile_content, padding=20)
