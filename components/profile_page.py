import logging
import os
import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from secrets import token_urlsafe
from time import sleep

import flet as ft
from dotenv import load_dotenv

from components.app_layout import get_usage_data
from utils.supabase_utils import read_supabase, write_supabase
from utils.theme_utils import get_current_color_scheme

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
                content=ft.Column([ft.CircleAvatar(content=ft.Text(letter), bgcolor=bgcolor, color=ft.Colors.WHITE),
                                   ft.Text(plan_name, size=18, weight=ft.FontWeight.BOLD), ft.Text(messages),
                                   ft.Text(pdfs), ft.Text(f"R$ {price}", size=16, color=ft.Colors.GREEN),
                                   ft.Text(description, italic=True)],
                                  alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20), elevation=5, col={"xs": 12, "sm": 6, "md": 4})


def ProfilePage(page: ft.Page, company_data: dict, app_state: dict):
    current_color_scheme = get_current_color_scheme(page)
    avatar_img = ft.Ref[ft.CircleAvatar]()
    prefix = os.getenv("PREFIX")
    username = page.client_storage.get(f"{prefix}username") or "Debt Manager"
    user_id = page.client_storage.get(f"{prefix}user_id")
    saved_avatar = page.client_storage.get(f"{prefix}avatar")

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

    if not username or not user_id:
        logger.warning("Username ou user_id não encontrados no client_storage. Redirecionando para login.")
        page.open(ft.SnackBar(ft.Text(f"Você não está logado!"), bgcolor=ft.Colors.ERROR))
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
    available_plans = [p["name"] for p in plans_data]
    plan_dropdown = ft.Dropdown(label="Escolher Novo Plano", options=[
                                ft.dropdown.Option(plan) for plan in available_plans], width=200)
    upgrade_code_field = ft.TextField(label="Código de Mudança", width=200)
    feedback_text = ft.Text("", color=ft.Colors.GREEN)

    avatar = ft.Stack([
        ft.CircleAvatar(foreground_image_src=saved_avatar if saved_avatar else f"{URL_DICEBEAR}seed={username}",
                        width=80, height=80, ref=avatar_img),
        ft.Container(content=ft.CircleAvatar(bgcolor=ft.Colors.GREEN, radius=5), alignment=ft.alignment.bottom_left),
    ], width=50, height=50)

    def mudar_perfil(e):
        avatar_aleatorio = f"{URL_DICEBEAR}seed={random.randint(1000, 9999)}"
        novo_avatar = avatar_aleatorio if avatar_aleatorio else f"{URL_DICEBEAR}seed={username}"
        avatar_img.current.foreground_image_src = novo_avatar
        avatar_img.current.update()
        page.client_storage.set(f"{prefix}avatar", novo_avatar)
        logger.info(f"Avatar alterado para {novo_avatar} pelo usuário {username}")


        page.open(ft.SnackBar(ft.Text(f"Avatar atualizado!"), bgcolor=ft.Colors.GREEN))  
        page.update()

    def send_plan_change_request(username, email, current_plan, new_plan, code, is_renewal=False):
        loading_dialog = show_loading()
        current_info = next(p for p in plans_data if p["name"] == current_plan)
        new_info = next(p for p in plans_data if p["name"] == new_plan)
        action = "Renovação" if is_renewal else "Mudança de Plano"
        try:
            msg = MIMEText(
                f"Solicitação de {action}:\nUsuário: {username}\nEmail: {email}\n"
                f"De: {current_plan} (Limites: {current_info['message_limit']} mensagens/mês, {current_info['pdf_limit']} PDFs/mês, Preço: R$ {current_info['price']})\n"
                f"Para: {new_plan} (Limites: {new_info['message_limit']} mensagens/mês, {new_info['pdf_limit']} PDFs/mês, Preço: R$ {new_info['price']})\n"
                f"Código: {code}")
            msg['Subject'] = f"Solicitação de {action} - DebtManager"
            msg['From'] = EMAIL_SENDER
            msg['To'] = SUPPORT_EMAIL
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email de {action.lower()} enviado para {SUPPORT_EMAIL} por {username}")
            hide_loading(loading_dialog)
            return True
        except Exception as e:
            hide_loading(loading_dialog)
            logger.error(f"Erro ao enviar email de {action.lower()} para {username}: {e}")
            return False

    def request_plan_change(e, is_renewal=False):
        loading_dialog = show_loading()
        new_plan = current_plan["name"] if is_renewal else plan_dropdown.value
        if not new_plan and not is_renewal:
            logger.warning(f"Usuário {username} tentou mudar plano sem selecionar um")
            page.open(ft.SnackBar(ft.Text(f"Escolha um plano!")))
            page.update()
            return
        change_code = token_urlsafe(16)
        action = "renovação" if is_renewal else "mudança de plano"
        logger.info(f"Gerando solicitação de {action} para {username}: plano {new_plan}, código {change_code}")
        if write_supabase("upgrade_requests",
                          {"user_id": user_id, "plan_id": next(p["id"] for p in plans_data if p["name"] == new_plan),
                           "code": change_code, "status": "pending"}, page=page):
            if send_plan_change_request(username, current_email, current_plan["name"], new_plan, change_code, is_renewal):
                hide_loading(loading_dialog)
                feedback_text.value = "Pedido enviado! Aguarde confirmação do suporte."
                page.open(ft.SnackBar(ft.Text(f"Solicitação de {action} enviada!"), bgcolor=ft.Colors.GREEN))
                logger.info(f"Solicitação de {action} salva e email enviado para {username}")
            else:
                hide_loading(loading_dialog)
                feedback_text.value = f"Deu ruim no email de {action}. Tenta de novo!"
                page.open(ft.SnackBar(ft.Text(f"Erro ao enviar email de {action}. Tenta novamente!"), bgcolor=ft.Colors.ERROR))
                logger.error(f"Falha ao enviar email de {action} para {username}")
        else:
            hide_loading(loading_dialog)
            feedback_text.value = f"Erro ao salvar o pedido de {action}. Tenta de novo!"
            page.open(ft.SnackBar(ft.Text(f"Falha ao salvar solicitação de {action}. Tenta novamente!"), bgcolor=ft.Colors.ERROR))
            logger.error(f"Falha ao salvar solicitação de {action} no Supabase para {username}")
        page.update()

    def apply_plan_change(e):
        loading_dialog = show_loading()
        code = upgrade_code_field.value.strip()
        if not code:
            logger.warning(f"Usuário {username} tentou aplicar mudança sem código")
            feedback_text.value = "Insira o código"
            page.open(ft.SnackBar(ft.Text(f"Código não pode ser vazio!")))
            page.update()
            return
        logger.info(f"Tentando aplicar mudança para {username} com código {code}")
        request = read_supabase("upgrade_requests", f"?user_id=eq.{user_id}&code=eq.{code}&status=eq.pending", page)

        if isinstance(request, dict):
            request_list = [request]
        elif isinstance(request, list):
            request_list = request
        else:
            request_list = []

        if request_list and len(request_list) > 0:
            plan_id = request_list[0].get("plan_id")
            selected_plan = next((p for p in plans_data if p["id"] == plan_id), None)
            if selected_plan:
                logger.info(f"Mudança válida encontrada: plano {selected_plan['name']} para {username}")
                if write_supabase(f"users_debt?id=eq.{user_id}", {
                    "plan_id": selected_plan["id"], "messages_sent": 0, "pdfs_processed": 0,
                    "data_expiracao": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                }, method="patch", page=page):
                    if write_supabase(f"upgrade_requests?id=eq.{request_list[0]['id']}", {"status": "approved"}, method="patch", page=page):
                        page.client_storage.set(f"{prefix}messages_sent", 0)
                        page.client_storage.set(f"{prefix}pdfs_processed", 0)
                        page.client_storage.set(f"{prefix}user_plan", selected_plan["name"])
                        app_state["user_plan"] = selected_plan["name"]
                        action = "renovado" if selected_plan["name"] == current_plan["name"] else "atualizado"
                        feedback_text.value = f"Plano {action} para {selected_plan['name']}! "
                        page.open(ft.SnackBar(ft.Text(f"Plano {action} com sucesso!"), bgcolor=ft.Colors.GREEN))
                        logger.info(f"Mudança aplicada com sucesso para {username}: plano {selected_plan['name']}")
                        hide_loading(loading_dialog)
                        show_success_and_redirect("/clients", f"Plano {action} com sucesso! Redirecionando para a página de clientes...")
                        logger.info(f"Redirecionando {username} para a página de clientes após mudança de plano")
                        page.update()
                    else:
                        hide_loading(loading_dialog)
                        feedback_text.value = "Erro ao aprovar o pedido. Tenta de novo!"
                        page.open(ft.SnackBar(ft.Text("Erro ao aprovar o pedido. Tenta novamente!"), bgcolor=ft.Colors.ERROR))
                        logger.error(
                            f"Falha ao atualizar status da mudança para 'approved' no Supabase para {username}")
                else:
                    hide_loading(loading_dialog)
                    feedback_text.value = "Erro ao atualizar o plano. Tenta de novo!"
                    page.open(ft.SnackBar(ft.Text("Erro ao atualizar o plano. Tenta novamente!"), bgcolor=ft.Colors.ERROR))
                    logger.error(f"Falha ao atualizar users_debt no Supabase para {username}")
            else:
                hide_loading(loading_dialog)
                feedback_text.value = "Plano não encontrado."
                page.open(ft.SnackBar(ft.Text("Plano não encontrado!"), bgcolor=ft.Colors.ERROR))
                logger.error(f"Plano com ID {plan_id} não encontrado em plans_data para {username}")
        else:
            hide_loading(loading_dialog)
            feedback_text.value = "Código inválido ou solicitação não encontrada."
            page.open(ft.SnackBar(ft.Text("Código inválido ou solicitação não encontrada!"), bgcolor=ft.Colors.ERROR))
            logger.error(f"Requisição inválida ou não encontrada para código {code} do usuário {username}")
        page.update()

    plan_cards = ft.ResponsiveRow([
        PlanCard("Básico", "100 mensagens/mês", "5 PDFs/mês", "150,00",
                 "Ideal para iniciantes!", ft.Colors.BLUE_700, "B"),
        PlanCard("Pro", "200 mensagens/mês", "15 PDFs/mês", "250,00",
                 "Mais poder para crescer!", ft.Colors.PURPLE_700, "P"),
        PlanCard("Enterprise", "500 mensagens/mês", "30 PDFs/mês", "400,00",
                 "Domine suas notificações!", ft.Colors.RED_700, "E")
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    def handle_close(e):
        page.close(dlg_modal)
        page.add(ft.Text(f"Modal dialog closed with action: {e.control.text}"))
    
    dlg_modal = ft.AlertDialog(
        title=ft.Text("Confirmação de Mudança de Plano", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Text(f"Você tem certeza que deseja mudar seu plano", size=16),
        actions=[
            ft.TextButton("Não", on_click=handle_close),
            ft.TextButton("Sim", on_click=request_plan_change),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: page.add(
            ft.Text("Modal dialog dismissed"),
        ),
    )
    
    dlg_renova = ft.AlertDialog(
        title=ft.Text("Confirmação de Renovação de Plano", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Text(f"Você tem certeza que deseja renovar seu plano atual?", size=16),
        actions=[
            ft.TextButton("Não", on_click=lambda e: page.close(dlg_renova)),
            ft.TextButton("Sim", on_click=lambda e: request_plan_change(e, is_renewal=True)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: page.add(
            ft.Text("Modal dialog dismissed"),
        ),
    )

    social_icons = ft.Row(controls=[
        ft.IconButton(content=ft.Image(src="images/contact/icons8-whatsapp-48.png", width=40, height=40),
                      icon_color=ft.Colors.GREEN, tooltip="Abrir WhatsApp", url="https://wa.link/oebrg2",
                      style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.GREEN})),
        ft.IconButton(content=ft.Image(src="images/contact/outlook-logo.png", width=40, height=40),
                      icon_color=ft.Colors.PRIMARY, tooltip="Enviar Email",
                      url="mailto:Alisondev77@hotmail.com?subject=Feedback%20-%20DebtManager&body=Olá, gostaria de fornecer feedback.",
                      style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.BLUE})),
        ft.IconButton(content=ft.Image(src="images/contact/icons8-linkedin-48.png", width=40, height=40),
                      tooltip="Acessar LinkedIn", url="https://www.linkedin.com/in/alisonsantosdev",
                      style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.BLUE})),
        ft.IconButton(content=ft.Image(src="images/contact/icons8-github-64.png", width=40, height=40),
                      icon_color=ft.Colors.PRIMARY, tooltip="Acessar GitHub", url="https://github.com/Alisonsantos77",
                      style=ft.ButtonStyle(overlay_color={"": ft.Colors.TRANSPARENT, "hovered": ft.Colors.GREY}))
    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

    profile_content = ft.Column([
        ft.Row([avatar, ft.Column([ft.Text(f"Bem-vindo, {username}!", size=24, weight=ft.FontWeight.BOLD),
                                   ft.ElevatedButton("Mudar avatar", on_click=mudar_perfil, style=ft.ButtonStyle(
                                       elevation=2,
                                       shape=ft.RoundedRectangleBorder(radius=5),
                                   ),)], spacing=10)], alignment=ft.MainAxisAlignment.START),
        ft.Text(f"Email: {current_email}", size=16),
        ft.Text(f"Plano Atual: {current_plan['name']}", size=16),
        ft.Text(f"Consumo: {usage_data['messages_sent']}/{current_plan['message_limit']} mensagens | {usage_data['pdfs_processed']}/{current_plan['pdf_limit']} PDFs",
                size=14, color=current_color_scheme.on_surface),
        ft.Divider(),
        ft.Text("Escolha ou Renove seu Plano", size=20, weight=ft.FontWeight.BOLD),
        plan_cards,
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[plan_dropdown,
                      ft.ElevatedButton("Mudar Plano", on_click=lambda e: page.open(dlg_modal), style=ft.ButtonStyle(
                          elevation=2,
                          shape=ft.RoundedRectangleBorder(radius=5),
                      )),
                      ft.ElevatedButton("Renovar Plano Atual", on_click=lambda e: page.open(dlg_renova), style=ft.ButtonStyle(
                          elevation=2,
                          shape=ft.RoundedRectangleBorder(radius=5),
                      ))
                      ]),
        ft.Row(alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER,
               controls=[upgrade_code_field, ft.ElevatedButton("Aplicar Mudança", on_click=apply_plan_change, style=ft.ButtonStyle(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=5),
        ))]),
        feedback_text,
        ft.Divider(),
        ft.Text("Contato", size=20, weight=ft.FontWeight.BOLD),
        social_icons,
    ], spacing=20, scroll=ft.ScrollMode.AUTO)

    return ft.Container(content=profile_content, padding=20)
