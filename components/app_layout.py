import asyncio
import datetime
import logging
import flet as ft
from components.clients import create_clients_page
from components.dialogs import create_dialogs
from services.message_manager import MessageManager
from services.pdf_extractor import PDFExtractor
from utils.message_templates import MessageTemplates
from utils.theme_utils import get_current_color_scheme
from utils.usage_tracker import UsageTracker
from utils.supabase_utils import fetch_user_id

logger = logging.getLogger(__name__)


class ClientListTile(ft.ListTile):
    def __init__(self, client, on_click, on_info_click, page: ft.Page):
        current_color_scheme = get_current_color_scheme(page)
        super().__init__(
            leading=ft.CircleAvatar(content=ft.Text(client.name[0]), bgcolor=current_color_scheme.primary),
            title=ft.Text(client.name, color=current_color_scheme.primary),
            subtitle=ft.Text(f"Valor: {client.debt_amount} | Vencimento: {client.due_date}",
                             color=current_color_scheme.on_surface),
            trailing=ft.IconButton(icon=ft.Icons.INFO, icon_color=current_color_scheme.primary,
                                   on_click=lambda e: on_info_click(client)),
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
            bgcolor=bgcolor
        )

    def show(self, page: ft.Page):
        page.overlay.append(self)
        self.open = True
        page.update()


def create_app_layout(page: ft.Page):
    user_plan_limits = {"basic": {"pdfs": 3, "messages": 5}, "pro": {
        "pdfs": 10, "messages": 20}, "enterprise": {"pdfs": 50, "messages": 100}}
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
    user_plan = "basic"
    usage_tracker = UsageTracker(user_plan)

    message_templates = MessageTemplates()

    username = page.client_storage.get("username") or "default_user"
    user_id = fetch_user_id(username)
    logger.info(f"Usuário inicializado: {username} (ID: {user_id})")

    usage_display = ft.Text(
        f"Consumo: {usage_tracker.get_usage('messages_sent')}/{user_plan_limits[user_plan]['messages']} mensagens | {usage_tracker.get_usage('pdfs_processed')}/{user_plan_limits[user_plan]['pdfs']} PDFs",
        size=14,
        color=current_color_scheme.primary
    )
    message_input = ft.TextField(
        label="Mensagem",
        multiline=True,
        value=message_templates.get_template("Padrão"),
        expand=True,
        hint_text="Digite ou edite a mensagem (use {name}, {debt_amount}, {due_date}, {reason})",
        color=current_color_scheme.on_surface
    )
    bulk_message_input = ft.TextField(
        label="Mensagem para Todos",
        multiline=True,
        width=400,
        value=message_templates.get_template("Padrão"),
        hint_text="Use {name}, {debt_amount}, {due_date}, {reason}",
        color=current_color_scheme.on_surface
    )

    def update_client_list():
        current_color_scheme_ = get_current_color_scheme(page)
        client_list_view.controls.clear()
        start_idx = current_page * clients_per_page
        end_idx = min(start_idx + clients_per_page, len(filtered_clients))
        for client in filtered_clients[start_idx:end_idx]:
            client_list_view.controls.append(
                ClientListTile(
                    client=client,
                    on_click=show_message,
                    on_info_click=lambda c: page.go(f"/client/{c.name}"),
                    page=page
                )
            )
        total_pages = (len(filtered_clients) + clients_per_page - 1) // clients_per_page
        navigation_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
        if current_page > 0:
            navigation_row.controls.append(
                ft.ElevatedButton(
                    "Anterior",
                    on_click=lambda e: change_page(-1),
                    bgcolor=current_color_scheme_.primary,
                    color=current_color_scheme_.on_primary
                )
            )
        navigation_row.controls.append(
            ft.Text(f"Página {current_page + 1} de {total_pages}", color=current_color_scheme_.on_surface)
        )
        if current_page < total_pages - 1:
            navigation_row.controls.append(
                ft.ElevatedButton(
                    "Próximo",
                    on_click=lambda e: change_page(1),
                    bgcolor=current_color_scheme_.primary,
                    color=current_color_scheme_.on_primary
                )
            )
        client_list_view.controls.append(navigation_row)
        logger.info(f"Lista de clientes atualizada: página {current_page + 1}/{total_pages}")
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
            name=client.name,
            debt_amount=client.debt_amount,
            due_date=client.due_date,
            reason=client.reason if hasattr(client, 'reason') else "pendência"
        )
        message_input.value = default_message
        client_details = ft.ExpansionTile(
            title=ft.Text(f"{client.name}", size=18, weight=ft.FontWeight.BOLD, color=current_color_scheme_.primary),
            subtitle=ft.Text(f"Status: {client.status}", size=14, color=current_color_scheme_.on_surface),
            initially_expanded=False,
            bgcolor=current_color_scheme_.surface_variant,
            collapsed_bgcolor=current_color_scheme_.surface,
            shape=ft.RoundedRectangleBorder(radius=10),
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Icon(ft.Icons.PHONE, color=current_color_scheme_.primary),
                                ft.Text(f"Contato: {client.contact}", size=14, color=current_color_scheme_.on_surface)],
                               alignment=ft.MainAxisAlignment.START),
                        ft.Row([ft.Icon(ft.Icons.MONETIZATION_ON, color=current_color_scheme_.error),
                                ft.Text(f"Valor: {client.debt_amount}", size=14, color=current_color_scheme_.error)],
                               alignment=ft.MainAxisAlignment.START),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, color=current_color_scheme_.primary),
                                ft.Text(f"Vencimento: {client.due_date}", size=14, color=current_color_scheme_.on_surface)],
                               alignment=ft.MainAxisAlignment.START),
                        ft.Row([ft.Icon(ft.Icons.INFO, color=current_color_scheme_.primary),
                                ft.Text(f"Motivo: {client.reason}", size=14, color=current_color_scheme_.on_surface)],
                               alignment=ft.MainAxisAlignment.START),
                    ], spacing=10),
                    padding=ft.padding.all(10)
                )
            ],
            controls_padding=ft.padding.symmetric(vertical=5),
            text_color=current_color_scheme_.on_surface,
            collapsed_text_color=current_color_scheme_.primary,
            tile_padding=ft.padding.symmetric(horizontal=15, vertical=5),
        )
        messages_view.controls = [
            ft.Row([ft.Text(f"{client.debt_amount}", size=16, weight=ft.FontWeight.BOLD, color=current_color_scheme_.error)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            client_details,
            dialogs["template_dropdown"],
            message_input,
            ft.Row([
                ft.ElevatedButton("Enviar para Cliente", bgcolor=current_color_scheme_.primary, color=ft.Colors.WHITE,
                                  expand=True, on_click=lambda e: page.run_task(send_single_alert, client)),
                ft.ElevatedButton("Enviar para Todos", bgcolor=current_color_scheme_.primary_container,
                                  color=current_color_scheme_.on_surface, expand=True,
                                  on_click=lambda e: dialogs["bulk_send_dialog"].open_dialog())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=20),
        ]
        logger.info(f"Mensagem exibida para {client.name} com modelo {message_templates.selected_template}")
        page.update()

    async def send_single_alert(client):
        nonlocal last_sent
        if not client:
            snack = CustomSnackBar("Nenhum cliente selecionado.", bgcolor=ft.Colors.RED)
            snack.show(page)
            return
        if not usage_tracker.check_usage_limits("message"):
            dialogs["usage_dialog"].open_dialog()
            return
        tile = next((t for t in client_list_view.controls if isinstance(
            t, ClientListTile) and t.client == client), None)
        if tile:
            tile.bgcolor = ft.Colors.YELLOW_100
            page.update()
        message_body = message_input.value if message_input.value else message_templates.get_template(
            message_templates.selected_template).format(
            name=client.name, debt_amount=client.debt_amount, due_date=client.due_date,
            reason=client.reason if hasattr(client, 'reason') else "pendência")
        await asyncio.sleep(1)
        success = message_manager.send_single_notification(client, message_body)
        if tile:
            tile.bgcolor = ft.Colors.GREEN_100 if success else ft.Colors.RED_100
            tile.trailing = ft.Icon(ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR,
                                    color=ft.Colors.GREEN if success else ft.Colors.RED)
            page.update()
        if success:
            usage_tracker.increment_usage("messages_sent")
            usage_tracker.sync_with_supabase(user_id)
            last_sent = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            page.snack_bar = CustomSnackBar(
                f"Alerta enviado para {client.name} às {last_sent}!", bgcolor=ft.Colors.GREEN)
            page.snack_bar.show(page)
            update_usage_dialog()
            usage_display.value = f"Consumo: {usage_tracker.get_usage('messages_sent')}/{user_plan_limits[user_plan]['messages']} mensagens | {usage_tracker.get_usage('pdfs_processed')}/{user_plan_limits[user_plan]['pdfs']} PDFs"
            usage_display.color = get_current_color_scheme(page).on_surface
            show_message(client)
        else:
            page.snack_bar = CustomSnackBar("Erro ao enviar mensagem.", bgcolor=ft.Colors.RED)
            page.snack_bar.show(page)
            dialogs["error_dialog"].open_dialog()
        logger.info(f"Envio de alerta para {client.name}: {'Sucesso' if success else 'Falha'}")
        page.update()

    async def send_bulk_message():
        dialogs["bulk_send_dialog"].close_dialog()
        if not filtered_clients:
            logger.warning("Tentativa de envio em massa sem clientes carregados")
            page.snack_bar = CustomSnackBar("Nenhum cliente carregado.", bgcolor=ft.Colors.RED)
            page.snack_bar.show(page)
            return

        messages_sent = usage_tracker.get_usage("messages_sent")
        messages_limit = user_plan_limits[user_plan]["messages"]
        remaining_messages = messages_limit - messages_sent
        clients_to_send = min(len(filtered_clients), remaining_messages)

        if clients_to_send <= 0:
            logger.info(f"Nenhuma mensagem disponível: {messages_sent}/{messages_limit}")
            dialogs["usage_dialog"].open_dialog()
            return

        logger.info(
            f"Iniciando envio em massa para {clients_to_send} de {len(filtered_clients)} clientes (limite restante: {remaining_messages})")
        dialogs["bulk_send_feedback_dialog"].open_dialog()
        total_clients = clients_to_send
        dialogs["bulk_send_feedback"].controls.clear()
        dialogs["progress_bar"].value = 0
        feedback_list = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        dialogs["bulk_send_feedback"].controls.append(feedback_list)
        success_count = 0

        try:
            # Limita aos primeiros clientes até o limite
            for idx, client in enumerate(filtered_clients[:clients_to_send]):
                logger.info(f"Tentando enviar para {client.name} ({client.contact})")
                feedback_list.controls.append(
                    ft.Text(f"Enviando para {client.name} ({client.contact})...", italic=True,
                            color=current_color_scheme.on_surface)
                )
                page.update()

                try:
                    message_body = bulk_message_input.value.format(
                        name=client.name, debt_amount=client.debt_amount, due_date=client.due_date,
                        reason=client.reason if hasattr(client, 'reason') else "pendência"
                    )
                except KeyError as e:
                    logger.error(f"Erro na formatação da mensagem para {client.name}: {e}")
                    message_body = f"Olá {client.name}, regularize sua pendência de {client.debt_amount} vencida em {client.due_date}."

                success = message_manager.send_single_notification(client, message_body)
                feedback_list.controls[-1] = ft.Row([
                    ft.Text(f"{client.name} ({client.contact})", color=current_color_scheme.on_surface),
                    ft.Icon(ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR,
                            color=ft.Colors.GREEN if success else ft.Colors.RED)
                ])
                if success:
                    success_count += 1
                    logger.info(f"Sucesso no envio para {client.name}")
                else:
                    logger.error(f"Falha no envio para {client.name}")

                dialogs["progress_bar"].value = (idx + 1) / total_clients
                await asyncio.sleep(0.05)
                page.update()

            last_sent_ = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            usage_tracker.increment_usage("messages_sent", success_count)
            usage_tracker.sync_with_supabase(user_id)
            feedback_list.controls.append(
                ft.Text(f"Envio concluído às {last_sent_}! ({success_count}/{total_clients} enviados)",
                        weight=ft.FontWeight.BOLD, color=current_color_scheme.on_surface)
            )
            dialogs["bulk_send_feedback_dialog"].dialog.actions[0].disabled = False
            page.snack_bar = CustomSnackBar(
                f"Alertas enviados para {success_count} clientes às {last_sent_}!", bgcolor=ft.Colors.GREEN)
            page.snack_bar.show(page)
            update_usage_dialog()
            usage_display.value = f"Consumo: {usage_tracker.get_usage('messages_sent')}/{user_plan_limits[user_plan]['messages']} mensagens | {usage_tracker.get_usage('pdfs_processed')}/{user_plan_limits[user_plan]['pdfs']} PDFs"
            usage_display.color = get_current_color_scheme(page).on_surface
            messages_view.controls = [ft.Text("Mensagens enviadas com sucesso!", size=12,
                                              color=current_color_scheme.on_surface)]
            if len(filtered_clients) > clients_to_send:
                logger.info(f"{len(filtered_clients) - clients_to_send} clientes não enviados devido ao limite")
                feedback_list.controls.append(
                    ft.Text(f"Nota: {len(filtered_clients) - clients_to_send} clientes excederam o limite e não foram enviados.",
                            color=current_color_scheme.on_surface)
                )
        except Exception as e:
            logger.error(f"Erro no envio em massa: {e}")
            feedback_list.controls.append(ft.Text(f"Erro: {str(e)}", color=ft.Colors.RED))
            dialogs["bulk_send_feedback_dialog"].dialog.actions[0].disabled = False
            page.snack_bar = CustomSnackBar("Erro ao enviar para todos.", bgcolor=ft.Colors.RED)
            page.snack_bar.show(page)
            dialogs["error_dialog"].open_dialog()

        logger.info(f"Envio em massa concluído com {success_count}/{total_clients} sucessos")
        page.update()

    def update_usage_dialog():
        current_color_scheme_ = get_current_color_scheme(page)
        usage_info = f"Mensagens Enviadas: {usage_tracker.get_usage('messages_sent')}\nPDFs Processados: {usage_tracker.get_usage('pdfs_processed')}\nLimite: {user_plan_limits[user_plan]['messages']} mensagens, {user_plan_limits[user_plan]['pdfs']} PDFs"
        dialogs["usage_dialog"].content = ft.Text(usage_info, size=16, color=current_color_scheme_.on_surface)
        dialogs["usage_dialog"].title = ft.Text("Informações do Plano", size=20, weight=ft.FontWeight.BOLD)
        dialogs["usage_dialog"].actions = [ft.TextButton(
            "Fechar", on_click=lambda e: dialogs["usage_dialog"].close_dialog())]
        page.update()

    dialogs = create_dialogs(page, message_input, bulk_message_input, message_templates, usage_tracker,
                             clients_list, filtered_clients, send_bulk_message, selected_client, update_client_list)

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()

    def process_pdf(e: ft.FilePickerResultEvent):
        nonlocal clients_list, filtered_clients, selected_client, current_page
        if not e.files:
            logger.warning("Nenhum arquivo selecionado no FilePicker")
            return
        if not usage_tracker.check_usage_limits("pdf"):
            logger.info(
                f"Limite de PDFs excedido: {usage_tracker.get_usage('pdfs_processed')}/{user_plan_limits[user_plan]['pdfs']}")
            dialogs["usage_dialog"].open_dialog()
            return
        pdf_path = e.files[0].path
        logger.info(f"Processando PDF: {pdf_path}")
        extractor = PDFExtractor(pdf_path, page)
        clients_list.clear()
        filtered_clients.clear()

        loading_dialog = show_loading()
        extracted_data = extractor.extract_pending_data()
        logger.info(
            f"Dados extraídos: {[(c.name, c.debt_amount, c.due_date, c.status, c.contact) for c in extracted_data]}")
        clients_list.extend(extracted_data)
        filtered_clients.extend(clients_list)
        selected_client = None
        current_page = 0
        client_list_view.controls.clear()
        messages_view.controls.clear()
        usage_tracker.increment_usage("pdfs_processed")
        usage_tracker.sync_with_supabase(user_id)
        update_client_list()
        message_manager.generate_notifications(clients_list)
        current_color_scheme_ = get_current_color_scheme(page)
        messages_view.controls = [
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        ft.Text("Clique em um cliente para visualizar detalhes e enviar mensagens", size=16,
                                italic=True, color=current_color_scheme_.on_surface, text_align=ft.TextAlign.CENTER)
                    ]
                )
            ])
        ]
        hide_loading(loading_dialog)
        snack = CustomSnackBar("Dados carregados com sucesso!", bgcolor=ft.Colors.GREEN)
        snack.show(page)
        usage_display.value = f"Consumo: {usage_tracker.get_usage('messages_sent')}/{user_plan_limits[user_plan]['messages']} mensagens | {usage_tracker.get_usage('pdfs_processed')}/{user_plan_limits[user_plan]['pdfs']} PDFs"
        usage_display.color = current_color_scheme_.on_surface
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
    messages_view.controls = [
        ft.Row(alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Text("Carregue um relatório de PDF para começar", size=20, weight=ft.FontWeight.BOLD,
                            color=c.primary, text_align=ft.TextAlign.CENTER),
                    ft.Text("Clique no botão acima para carregar um relatório", size=16, italic=True,
                            color=c.on_surface, text_align=ft.TextAlign.CENTER)
                ]
            )
        ])
    ]
    layout = ft.Column([
        ft.Row([
            ft.ElevatedButton("Carregar Relatório", icon=ft.Icons.UPLOAD_FILE,
                              on_click=lambda _: file_picker.pick_files(allowed_extensions=["pdf"])),
            usage_display
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=10),
        create_clients_page(clients_list, filtered_clients, current_page, client_list_view,
                            messages_view, last_sent, dialogs, page, update_client_list)
    ], expand=True, alignment=ft.MainAxisAlignment.CENTER)
    return layout, {"toggle_theme": toggle_theme, "dialogs": dialogs, "user_plan": user_plan, "clients_list": clients_list, "filtered_clients": filtered_clients, "update_client_list": update_client_list, "usage_tracker": usage_tracker}
