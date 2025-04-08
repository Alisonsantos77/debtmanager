import asyncio
import datetime
import logging
import os

import flet as ft
from dotenv import load_dotenv
from twilio.rest import Client

from components.clients import create_clients_page
from components.dialogs import create_dialogs
from services.message_manager import MessageManager
from services.pdf_extractor import PDFExtractor
from utils.message_templates import MessageTemplates
from utils.supabase_utils import (fetch_plan_data, fetch_user_data,
                                  fetch_user_id, update_usage_data)
from utils.theme_utils import get_current_color_scheme

load_dotenv()
logger = logging.getLogger(__name__)


class ClientListTile(ft.ListTile):
    def __init__(self, client, on_click, on_info_click, page: ft.Page):
        current_color_scheme = get_current_color_scheme(page)
        super().__init__(
            leading=ft.CircleAvatar(content=ft.Text(client.name[0]), bgcolor=current_color_scheme.primary),
            title=ft.Text(client.name, color=current_color_scheme.primary),
            subtitle=ft.Text(f"Valor: {client.debt_amount} | Vencimento: {client.due_date}",
                             color=current_color_scheme.on_surface),
            trailing=ft.IconButton(icon=ft.Icons.INFO, icon_color=current_color_scheme.primary, on_click=on_info_click),
            content_padding=ft.padding.symmetric(horizontal=10),
            on_click=lambda e: on_click(client),
            bgcolor=ft.Colors.TRANSPARENT
        )
        self.client = client


class CustomSnackBar(ft.SnackBar):
    def __init__(self, message: str, bgcolor=None, duration=3000):
        super().__init__(
            content=ft.Text(message, size=16),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=20,
            show_close_icon=True,
            elevation=5,
            duration=duration,
            bgcolor=bgcolor if bgcolor else None
        )

    def show(self, page: ft.Page):
        page.overlay.append(self)
        self.open = True
        page.update()


def get_usage_data(page):
    prefix = os.getenv("PREFIX")
    return {
        "messages_sent": page.client_storage.get(f"{prefix}messages_sent") or 0,
        "pdfs_processed": page.client_storage.get(f"{prefix}pdfs_processed") or 0
    }


def create_app_layout(page: ft.Page):
    current_color_scheme = get_current_color_scheme(page)
    clients_list = []
    filtered_clients = []
    clients_per_page = 5
    current_page = 0
    client_list_view = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
    messages_view = ft.Column(expand=True, spacing=20, auto_scroll=True)
    message_manager = MessageManager()
    last_sent = None
    selected_client = None

    prefix = "debtmanager."
    username = page.client_storage.get(f"{prefix}username")
    if not username:
        logger.warning("Username não encontrado no client_storage. Redirecionando para login.")
        CustomSnackBar("Parece que você não tá logado. Vamos pro login!", bgcolor=ft.colors.ERROR).show(page)
        page.go("/login")
        return None, {"toggle_theme": lambda: None, "dialogs": {}, "clients_list": [], "filtered_clients": [], "update_client_list": lambda: None, "history": []}

    user_id = fetch_user_id(username, page)
    if not user_id:
        logger.error(f"User_id não encontrado para {username}. Redirecionando para login.")
        CustomSnackBar("Não achei seu ID. Vamos tentar o login de novo?", bgcolor=ft.colors.ERROR).show(page)
        page.go("/login")
        return None, {"toggle_theme": lambda: None, "dialogs": {}, "clients_list": [], "filtered_clients": [], "update_client_list": lambda: None, "history": []}

    user_data = fetch_user_data(user_id, page)
    if not user_data:
        logger.error(f"Dados do usuário não carregados para {user_id}. Redirecionando para login.")
        CustomSnackBar("Não consegui pegar seus dados. Tenta relogar?", bgcolor=ft.colors.ERROR).show(page)
        page.go("/login")
        return None, {"toggle_theme": lambda: None, "dialogs": {}, "clients_list": [], "filtered_clients": [], "update_client_list": lambda: None, "history": []}

    plan_id = user_data.get("plan_id", 1)
    plan_data = fetch_plan_data(plan_id, page) or {"name": "basic", "message_limit": 100, "pdf_limit": 5}
    user_plan = page.client_storage.get(f"{prefix}user_plan") or plan_data.get("name", "basic")
    message_limit = plan_data.get("message_limit", 100)
    pdf_limit = plan_data.get("pdf_limit", 5)

    usage_data = get_usage_data(page)
    local_messages_sent = usage_data["messages_sent"]
    local_pdfs_processed = usage_data["pdfs_processed"]

    if usage_data["messages_sent"] != user_data.get("messages_sent", 0) or usage_data["pdfs_processed"] != user_data.get("pdfs_processed", 0):
        page.client_storage.set(f"{prefix}messages_sent", user_data.get("messages_sent", 0))
        page.client_storage.set(f"{prefix}pdfs_processed", user_data.get("pdfs_processed", 0))
        local_messages_sent = user_data.get("messages_sent", 0)
        local_pdfs_processed = user_data.get("pdfs_processed", 0)

    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    support_number = os.getenv("SUPPORT_PHONE")
    if not page.session.contains_key("notified_clients"):
        page.session.set("notified_clients", [])
    message_templates = MessageTemplates()
    usage_display = ft.Text(
        f"Consumo: {local_messages_sent}/{message_limit} mensagens | {local_pdfs_processed}/{pdf_limit} PDFs",
        size=14, color=current_color_scheme.primary
    )
    message_input = ft.TextField(
        label="Mensagem", multiline=True, value=message_templates.get_template("Padrão"), expand=True,
        hint_text="Digite ou edite a mensagem (use {name}, {debt_amount}, {due_date}, {reason})",
        color=current_color_scheme.on_surface
    )
    bulk_message_input = ft.TextField(
        label="Mensagem para Todos", multiline=True, width=400, value=message_templates.get_template("Padrão"),
        hint_text="Use {name}, {debt_amount}, {due_date}, {reason}", color=current_color_scheme.on_surface
    )
    history = []

    def sync_usage():
        nonlocal local_messages_sent, local_pdfs_processed
        page.client_storage.set(f"{prefix}messages_sent", local_messages_sent)
        page.client_storage.set(f"{prefix}pdfs_processed", local_pdfs_processed)

    page.on_close = lambda e: sync_usage()

    def show_client_details(client):
        current_color_scheme_ = get_current_color_scheme(page)
        dialog = ft.AlertDialog(
            title=ft.Text(f"Detalhes do Cliente: {client.name}", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                controls=[
                    ft.Text(f"Nome: {client.name}", size=16, color=current_color_scheme_.on_surface),
                    ft.Text(f"Contato: {client.contact}", size=16, color=current_color_scheme_.on_surface),
                    ft.Text(f"Valor da Dívida: {client.debt_amount}", size=16, color=current_color_scheme_.on_surface),
                    ft.Text(f"Data de Vencimento: {client.due_date}", size=16, color=current_color_scheme_.on_surface),
                    ft.Text(f"Status: {client.status}", size=16, color=current_color_scheme_.on_surface),
                    ft.Text(f"Motivo: {client.reason if hasattr(client, 'reason') else 'Não especificado'}",
                            size=16, color=current_color_scheme_.on_surface),
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO, height=300
            ),
            actions=[ft.TextButton("Fechar", on_click=lambda e: page.close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.open(dialog)
        page.update()

    def update_client_list():
        current_color_scheme_ = get_current_color_scheme(page)
        client_list_view.controls.clear()
        start_idx = current_page * clients_per_page
        end_idx = min(start_idx + clients_per_page, len(filtered_clients))
        for client in filtered_clients[start_idx:end_idx]:
            client_list_view.controls.append(ClientListTile(
                client=client, on_click=show_message, on_info_click=lambda e, c=client: show_client_details(c), page=page))
        total_pages = (len(filtered_clients) + clients_per_page - 1) // clients_per_page
        navigation_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
        if current_page > 0:
            navigation_row.controls.append(ft.ElevatedButton(
                "Anterior", on_click=lambda e: change_page(-1), bgcolor=current_color_scheme_.primary, color=current_color_scheme_.on_primary))
        navigation_row.controls.append(
            ft.Text(f"Página {current_page + 1} de {total_pages}", color=current_color_scheme_.primary))
        if current_page < total_pages - 1:
            navigation_row.controls.append(ft.ElevatedButton("Próximo", on_click=lambda e: change_page(
                1), bgcolor=current_color_scheme_.primary, color=current_color_scheme_.on_primary))
        client_list_view.controls.append(navigation_row)
        logger.info(f"Lista de clientes atualizada: página {current_page + 1} de {total_pages}")
        page.update()

    def change_page(delta):
        nonlocal current_page
        total_pages = (len(filtered_clients) + clients_per_page - 1) // clients_per_page
        current_page = max(0, min(current_page + delta, total_pages - 1))
        update_client_list()

    def show_message(client):
        nonlocal selected_client
        selected_client = client
        current_color_scheme_ = get_current_color_scheme(page)
        default_message = message_templates.get_template(message_templates.selected_template).format(
            name=client.name, debt_amount=client.debt_amount, due_date=client.due_date, reason=client.reason if hasattr(client, 'reason') else "pendência")
        message_input.value = default_message
        client_details = ft.ExpansionTile(
            title=ft.Text(f"{client.name}", size=18, weight=ft.FontWeight.BOLD, color=current_color_scheme_.primary),
            subtitle=ft.Text(f"Status: {client.status}", size=14, color=current_color_scheme_.on_surface),
            initially_expanded=False,
            bgcolor=current_color_scheme_.surface_variant,
            collapsed_bgcolor=current_color_scheme_.surface,
            shape=ft.RoundedRectangleBorder(radius=10),
            controls=[ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.PHONE, color=current_color_scheme_.primary), ft.Text(
                    f"Contato: {client.contact}", size=14, color=current_color_scheme_.on_surface)], alignment=ft.MainAxisAlignment.START),
                ft.Row([ft.Icon(ft.Icons.MONETIZATION_ON, color=current_color_scheme_.error), ft.Text(
                    f"Valor: {client.debt_amount}", size=14, color=current_color_scheme_.error)], alignment=ft.MainAxisAlignment.START),
                ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, color=current_color_scheme_.primary), ft.Text(
                    f"Vencimento: {client.due_date}", size=14, color=current_color_scheme_.on_surface)], alignment=ft.MainAxisAlignment.START),
                ft.Row([ft.Icon(ft.Icons.INFO, color=current_color_scheme_.primary), ft.Text(
                    f"Motivo: {client.reason}", size=14, color=current_color_scheme_.on_surface)], alignment=ft.MainAxisAlignment.START),
            ], spacing=10), padding=ft.padding.all(10))],
            controls_padding=ft.padding.symmetric(vertical=5),
            text_color=current_color_scheme_.on_surface,
            collapsed_text_color=current_color_scheme_.primary,
            tile_padding=ft.padding.symmetric(horizontal=15, vertical=5),
        )
        messages_view.controls = [
            ft.Row([ft.Text(f"{client.debt_amount}", size=16, weight=ft.FontWeight.BOLD,
                   color=current_color_scheme_.error)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            client_details,
            dialogs["template_dropdown"],
            message_input,
            ft.Row([
                ft.ElevatedButton("Enviar para Cliente", bgcolor=current_color_scheme_.primary, color=ft.Colors.WHITE,
                                  expand=True, on_click=lambda e: page.run_task(send_single_alert, client)),
                ft.ElevatedButton("Enviar para Todos", bgcolor=current_color_scheme_.primary_container,
                                  color=current_color_scheme_.on_surface, expand=True, on_click=lambda e: dialogs["bulk_send_dialog"].open_dialog())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=20),
        ]
        logger.info(f"Exibindo mensagem para {client.name} com template {message_templates.selected_template}")
        page.update()

    async def notify_limit_reached(limit_type):
        message = f"Oi, eu sou o cliente {username}, atingi meu limite de {limit_type} em {datetime.datetime.now().strftime('%d/%m/%Y')}. Quero fazer upgrade ou conversar sobre a aplicação!"
        twilio_client.messages.create(body=message, from_=os.getenv("TWILIO_WHATSAPP_NUMBER"), to=support_number)
        logger.info(f"Notificação de limite enviada: {limit_type} para {support_number}")

    def check_usage_limits(key):
        limits = {"messages_sent": message_limit, "pdfs_processed": pdf_limit}
        current_value = local_messages_sent if key == "messages_sent" else local_pdfs_processed
        return current_value < limits[key]

    def increment_usage(key, amount=1):
        nonlocal local_messages_sent, local_pdfs_processed
        if key == "messages_sent":
            local_messages_sent += amount
        elif key == "pdfs_processed":
            local_pdfs_processed += amount

    async def send_single_alert(client):
        nonlocal last_sent, local_messages_sent
        if not client:
            CustomSnackBar("Nenhum cliente selecionado.", bgcolor=ft.Colors.ERROR).show(page)
            return
        if not check_usage_limits("messages_sent"):
            update_usage_dialog()
            dialogs["usage_dialog"].open_dialog()
            await notify_limit_reached("messages")
            return
        tile = next((t for t in client_list_view.controls if isinstance(
            t, ClientListTile) and t.client == client), None)
        message_body = message_input.value if message_input.value else message_templates.get_template(message_templates.selected_template).format(
            name=client.name, debt_amount=client.debt_amount, due_date=client.due_date, reason=client.reason if hasattr(client, 'reason') else "pendência")
        await asyncio.sleep(1)
        success = message_manager.send_single_notification(client, message_body)
        if tile:
            tile.trailing = ft.Icon(ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR,
                                    color=ft.Colors.GREEN if success else ft.Colors.ERROR)
            page.update()
        if success:
            increment_usage("messages_sent")
            last_sent = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            history.append(type('HistoryEntry', (), {'sent_at': last_sent,
                           'status': 'enviado', 'message': message_body, 'client': client.name})())
            notified_clients = page.session.get("notified_clients")
            if client.name not in notified_clients:
                notified_clients.append(client.name)
                page.session.set("notified_clients", notified_clients)
                logger.info(f"Cliente {client.name} notificado e adicionado à lista")
            CustomSnackBar(f"Alerta enviado para {client.name} às {last_sent}!").show(page)
            update_usage_dialog()
            usage_display.value = f"Consumo: {local_messages_sent}/{message_limit} mensagens | {local_pdfs_processed}/{pdf_limit} PDFs"
            usage_display.color = get_current_color_scheme(page).on_surface
            show_message(client)
            update_usage_data(user_id, local_messages_sent, local_pdfs_processed, page)
        else:
            CustomSnackBar("Erro ao enviar mensagem.", bgcolor=ft.Colors.ERROR).show(page)
            dialogs["error_dialog"].open_dialog()
        logger.info(f"Envio para {client.name}: {'sucesso' if success else 'falha'}")

    async def send_bulk_message():
        dialogs["bulk_send_dialog"].close_dialog()
        if not filtered_clients:
            logger.warning("Tentativa de envio em massa sem clientes")
            CustomSnackBar("Nenhum cliente carregado.", bgcolor=ft.Colors.ERROR).show(page)
            return
        remaining_messages = message_limit - local_messages_sent
        notified_clients = page.session.get("notified_clients")
        eligible_clients = [c for c in filtered_clients if c.name not in notified_clients]
        clients_to_send = min(len(eligible_clients), remaining_messages)
        if clients_to_send <= 0:
            logger.info(
                f"Sem mensagens disponíveis ou todos notificados: {local_messages_sent}/{message_limit}")
            update_usage_dialog()
            dialogs["usage_dialog"].open_dialog()
            await notify_limit_reached("messages")
            return
        logger.info(
            f"Enviando para {clients_to_send}/{len(eligible_clients)} clientes (restante: {remaining_messages})")
        dialogs["bulk_send_feedback_dialog"].dialog.modal = True
        dialogs["bulk_send_feedback_dialog"].open_dialog()
        total_clients = clients_to_send
        dialogs["bulk_send_feedback"].controls.clear()
        dialogs["progress_bar"].value = 0
        feedback_list = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        dialogs["bulk_send_feedback"].controls.append(feedback_list)
        success_count = 0
        try:
            for idx, client in enumerate(eligible_clients[:clients_to_send]):
                logger.info(f"Enviando para {client.name} ({client.contact})")
                feedback_list.controls.append(
                    ft.Text(f"Enviando para {client.name} ({client.contact})...", italic=True, color=current_color_scheme.on_surface))
                page.update()
                try:
                    message_body = bulk_message_input.value.format(
                        name=client.name, debt_amount=client.debt_amount, due_date=client.due_date, reason=client.reason if hasattr(client, 'reason') else "pendência")
                except KeyError as e:
                    logger.error(f"Erro na formatação para {client.name}: {e}")
                    message_body = f"Olá {client.name}, regularize sua pendência de {client.debt_amount} vencida em {client.due_date}."
                tile = next((t for t in client_list_view.controls if isinstance(
                    t, ClientListTile) and t.client == client), None)
                success = message_manager.send_single_notification(client, message_body)
                feedback_list.controls[-1] = ft.Row([ft.Text(f"{client.name} ({client.contact})", color=current_color_scheme.on_surface), ft.Icon(
                    ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR)])
                if tile:
                    tile.trailing = ft.Icon(ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR)
                    page.update()
                if success:
                    success_count += 1
                    notified_clients.append(client.name)
                    page.session.set("notified_clients", notified_clients)
                    history.append(type('HistoryEntry', (), {'sent_at': datetime.datetime.now().strftime(
                        "%d/%m/%Y %H:%M"), 'status': 'enviado', 'message': message_body, 'client': client.name})())
                    logger.info(f"Sucesso para {client.name}, notificado")
                else:
                    logger.error(f"Falha para {client.name}")
                dialogs["progress_bar"].value = (idx + 1) / total_clients
                await asyncio.sleep(0.05)
                page.update()
            last_sent_ = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            increment_usage("messages_sent", success_count)
            feedback_list.controls.append(ft.Text(
                f"Envio concluído às {last_sent_}! ({success_count}/{total_clients} enviados)", weight=ft.FontWeight.BOLD, color=current_color_scheme.on_surface))
            dialogs["bulk_send_feedback_dialog"].dialog.actions[0].disabled = False
            CustomSnackBar(f"Alertas enviados para {success_count} clientes às {last_sent_}!").show(page)
            update_usage_dialog()
            usage_display.value = f"Consumo: {local_messages_sent}/{message_limit} mensagens | {local_pdfs_processed}/{pdf_limit} PDFs"
            usage_display.color = get_current_color_scheme(page).on_surface
            messages_view.controls = [ft.Text("Mensagens enviadas com sucesso!",
                                              size=12, color=current_color_scheme.on_surface)]
            if len(eligible_clients) > clients_to_send:
                logger.info(f"{len(eligible_clients) - clients_to_send} clientes não enviados por limite")
                feedback_list.controls.append(ft.Text(
                    f"Nota: {len(eligible_clients) - clients_to_send} clientes excederam o limite.", color=current_color_scheme.on_surface))
            update_usage_data(user_id, local_messages_sent, local_pdfs_processed, page)
        except Exception as e:
            logger.error(f"Erro no envio em massa: {e}")
            feedback_list.controls.append(ft.Text(f"Erro: {str(e)}", color=ft.Colors.ERROR))
            dialogs["bulk_send_feedback_dialog"].dialog.actions[0].disabled = False
            CustomSnackBar("Erro ao enviar para todos.", bgcolor=ft.Colors.ERROR).show(page)
            dialogs["error_dialog"].open_dialog()
        logger.info(f"Envio em massa concluído: {success_count}/{total_clients} sucessos")

    def update_usage_dialog():
        current_color_scheme_ = get_current_color_scheme(page)
        usage_info = f"Mensagens Enviadas: {local_messages_sent}/{message_limit}\nPDFs Processados: {local_pdfs_processed}/{pdf_limit}"
        dialogs["usage_dialog"].dialog.content = ft.Text(usage_info, size=16, color=current_color_scheme_.on_surface)
        dialogs["usage_dialog"].dialog.title = ft.Text("Limite atingido!", size=20, weight=ft.FontWeight.BOLD)
        dialogs["usage_dialog"].dialog.actions = [ft.TextButton(
            "Fechar", on_click=lambda e: dialogs["usage_dialog"].close_dialog())]
        page.update()

    dialogs = create_dialogs(page, message_input, bulk_message_input, message_templates, None,
                             clients_list, filtered_clients, send_bulk_message, selected_client, update_client_list)

    def show_loading():
        loading_dialog = ft.AlertDialog(content=ft.Container(content=ft.ProgressRing(
        ), alignment=ft.alignment.center), bgcolor=ft.Colors.TRANSPARENT, modal=True, disabled=True)
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def show_success(message="Sucesso!"):
        success_dialog = ft.AlertDialog(content=ft.Container(content=ft.Column([ft.ProgressRing(), ft.Text(message, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)],
                                        alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center), bgcolor=ft.Colors.TRANSPARENT, modal=True, disabled=True)
        page.open(success_dialog)
        page.update()
        return success_dialog

    def hide_dialog(dialog):
        page.close(dialog)
        page.update()

    def process_pdf(e: ft.FilePickerResultEvent):
        nonlocal clients_list, filtered_clients, selected_client, current_page, local_pdfs_processed
        logger.info(f"Processando PDF: {e.files[0].path if e.files else 'Nenhum'}")

        if not e.files:
            logger.warning("Nenhum arquivo selecionado.")
            CustomSnackBar("Escolhe um PDF aí, mano!", bgcolor=ft.Colors.ERROR).show(page)
            return

        pdf_path = e.files[0].path
        if not check_usage_limits("pdfs_processed"):
            logger.info(f"Limite de PDFs excedido: {local_pdfs_processed}/{pdf_limit}")
            update_usage_dialog()
            dialogs["usage_dialog"].open_dialog()
            page.run_task(notify_limit_reached, "pdfs")
            CustomSnackBar("Limite de PDFs atingido! Já avisei o suporte!", bgcolor=ft.Colors.YELLOW).show(page)
            return

        extractor = PDFExtractor(pdf_path, page)
        clients_list.clear()
        filtered_clients.clear()
        loading_dialog = show_loading()

        try:
            extracted_data = extractor.extract_pending_data()
            if not extracted_data:
                logger.warning("Nenhum cliente extraído.")
                CustomSnackBar("Nenhum cliente válido no PDF. Tá faltando algo ou tá zoado!",
                            bgcolor=ft.Colors.YELLOW).show(page)
            else:
                logger.info(f"Extraídos {len(extracted_data)} clientes!")
                clients_list.extend(extracted_data)
                filtered_clients.extend(clients_list)
                CustomSnackBar(f"Beleza! {len(extracted_data)} clientes carregados!",
                            bgcolor=ft.Colors.GREEN).show(page)

            selected_client = None
            current_page = 0
            client_list_view.controls.clear()
            messages_view.controls.clear()
            increment_usage("pdfs_processed")
            update_usage_data(user_id, local_messages_sent, local_pdfs_processed, page)
            update_client_list()
            message_manager.generate_notifications(clients_list)

            current_color_scheme_ = get_current_color_scheme(page)
            messages_view.controls = [ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                    controls=[ft.Text(
                        "Clique em um cliente pra ver detalhes e mandar mensagens",
                        size=16, italic=True, color=current_color_scheme_.on_surface,
                        text_align=ft.TextAlign.CENTER
                    )]
                )]
            )]

            hide_dialog(loading_dialog)
            success_dialog = show_success("PDF processado com sucesso!")

            async def delay_and_hide():
                await asyncio.sleep(2)
                hide_dialog(success_dialog)
            page.run_task(delay_and_hide)

            usage_display.value = f"Consumo: {local_messages_sent}/{message_limit} mensagens | {local_pdfs_processed}/{pdf_limit} PDFs"
            usage_display.color = current_color_scheme_.on_surface

        except Exception as e:
            logger.error(f"Erro ao processar PDF: {e}")
            CustomSnackBar(f"Ocorreu um erro: {str(e)}. Por favor, tente carregar outro PDF.", bgcolor=ft.Colors.ERROR).show(page)
            hide_dialog(loading_dialog)
            dialogs["error_dialog"].open_dialog()

        page.update()

    file_picker = ft.FilePicker(on_result=process_pdf)
    page.overlay.append(file_picker)

    def toggle_theme():
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        c = get_current_color_scheme(page)
        message_input.color = c.on_surface
        bulk_message_input.color = c.on_surface
        usage_display.color = c.on_surface
        update_client_list()
        if selected_client:
            show_message(selected_client)
        logger.info(f"Tema alterado para {page.theme_mode}")
        page.update()

    c = get_current_color_scheme(page)
    messages_view.controls = [ft.Row(alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True, controls=[ft.Text(
        "Carregue um relatório de PDF para começar", size=20, weight=ft.FontWeight.BOLD, color=c.primary, text_align=ft.TextAlign.CENTER), ft.Text("Clique no botão acima para carregar um relatório", size=16, italic=True, color=c.primary_container, text_align=ft.TextAlign.CENTER)])])]
    layout = ft.Column([
        ft.Row([
            ft.ElevatedButton("Carregar Relatório",
                              icon=ft.Icons.UPLOAD_FILE,
                              style=ft.ButtonStyle(
                                  elevation=2,
                                  shape=ft.RoundedRectangleBorder(radius=5),
                              ),
                              on_click=lambda _: file_picker.pick_files(allowed_extensions=["pdf"])
                              ),
            usage_display
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10),
        create_clients_page(clients_list, filtered_clients, current_page, client_list_view,
                            messages_view, last_sent, dialogs, page, update_client_list)
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    return layout, {"toggle_theme": toggle_theme, "dialogs": dialogs, "clients_list": clients_list, "filtered_clients": filtered_clients, "update_client_list": update_client_list, "history": history}
