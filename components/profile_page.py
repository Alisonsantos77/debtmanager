import asyncio
import logging
import flet as ft
from flet import FilePicker, FilePickerResultEvent
from utils.supabase_utils import read_supabase

logger = logging.getLogger(__name__)


def ProfilePage(page: ft.Page, company_data: dict, app_state: dict):
    name_field = ft.Ref[ft.TextField]()
    email_field = ft.Ref[ft.TextField]()
    phone_field = ft.Ref[ft.TextField]()
    logo_display = ft.Ref[ft.CircleAvatar]()
    current_logo = company_data.get("logo", "https://picsum.photos/150")
    current_name = company_data.get("name", "Empresa Sem Nome")
    current_email = company_data.get("contact_email", "sem@email.com")
    current_phone = company_data.get("phone", "(00) 00000-0000")
    usage_tracker = app_state.get("usage_tracker")
    user_id = page.client_storage.get("user_id")
    user_data = read_supabase("users_debt", f"?id=eq.{user_id}")
    plan_id = user_data.get("plan_id", 1)
    plan_data = read_supabase("plans", f"?id=eq.{plan_id}")
    user_plan = plan_data.get("name", "basic")
    app_state["user_plan"] = user_plan
    user_plan_limits = {user_plan: {"messages": plan_data["message_limit"], "pdfs": plan_data["pdf_limit"]}}

    def pick_logo_result(e: FilePickerResultEvent):
        nonlocal current_logo
        if e.files and e.files[0].path:
            current_logo = e.files[0].path
            logo_display.current.content = None  # Limpa antes
            logo_display.current.content = ft.Image(src=current_logo, fit=ft.ImageFit.COVER)
            company_data["logo"] = current_logo
            page.update()
            logger.info(f"Nova foto de perfil selecionada: {current_logo}")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Seleção de foto cancelada!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()

    pick_logo_dialog = FilePicker(on_result=pick_logo_result)
    page.overlay.append(pick_logo_dialog)

    def show_loading():
        loading_dialog = ft.AlertDialog(content=ft.Container(content=ft.ProgressRing(
        ), alignment=ft.alignment.center), bgcolor=ft.Colors.TRANSPARENT, modal=True, disabled=True)
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def show_success(message="Dados atualizados!"):
        success_dialog = ft.AlertDialog(content=ft.Container(content=ft.Column([ft.Icon(ft.icons.CHECK_CIRCLE, size=50, color=ft.colors.GREEN), ft.Text(
            message, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center), bgcolor=ft.colors.TRANSPARENT, modal=True, disabled=True)
        page.open(success_dialog)
        page.update()
        return success_dialog

    def hide_dialog(dialog):
        page.close(dialog)
        page.update()

    def update_company_data(e):
        nonlocal current_name, current_email, current_phone
        new_name = name_field.current.value.strip()
        new_email = email_field.current.value.strip()
        new_phone = phone_field.current.value.strip()
        if not new_name or not new_email or not new_phone:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos obrigatórios!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        loading_dialog = show_loading()
        current_name, current_email, current_phone = new_name, new_email, new_phone
        company_data["name"] = current_name
        company_data["contact_email"] = current_email
        company_data["phone"] = current_phone
        company_data["logo"] = current_logo
        if not current_logo.startswith("http"):
            logo_display.current.content = ft.Image(src=current_logo, fit=ft.ImageFit.COVER)
        else:
            logo_display.current.content = ft.Text(current_name[0].upper(), size=40, weight=ft.FontWeight.BOLD)
        hide_dialog(loading_dialog)
        success_dialog = show_success()
        page.run_task(lambda: asyncio.sleep(2)).then(lambda _: hide_dialog(success_dialog))
        logger.info(f"Dados da empresa atualizados: {company_data}")
        page.snack_bar = ft.SnackBar(ft.Text("Dados atualizados com sucesso!"), bgcolor=ft.colors.GREEN)
        page.snack_bar.open = True
        page.update()

    profile_content = ft.Column([
        ft.ResponsiveRow([
            ft.Container(
                col={"xs": 12, "sm": 6, "md": 4},
                content=ft.Stack([
                    ft.CircleAvatar(
                        ref=logo_display,
                        foreground_image_src=current_logo if current_logo.startswith("http") else None,
                        content=ft.Image(src=current_logo, fit=ft.ImageFit.COVER) if not current_logo.startswith(
                            "http") else ft.Text(current_name[0].upper(), size=40, weight=ft.FontWeight.BOLD),
                        radius=60,
                        bgcolor=ft.colors.BLUE_200,
                        on_image_error=lambda e: logger.error(f"Erro ao carregar imagem: {e.data}")
                    ),
                    ft.Container(
                        alignment=ft.alignment.bottom_right,
                        content=ft.IconButton(icon=ft.Icons.EDIT, bgcolor=ft.colors.WHITE, icon_color=ft.colors.BLUE,
                                              on_click=lambda _: pick_logo_dialog.pick_files(allowed_extensions=["png", "jpg", "jpeg"]))
                    )
                ]),
                alignment=ft.alignment.center
            ),
            ft.Column(
                col={"xs": 12, "sm": 6, "md": 8},
                controls=[
                    ft.TextField(ref=name_field, label="Nome da Empresa", value=current_name,
                                 prefix_icon=ft.Icons.BUSINESS, border_radius=10),
                    ft.TextField(ref=email_field, label="Email de Contato", value=current_email,
                                 prefix_icon=ft.Icons.EMAIL, border_radius=10),
                    ft.TextField(ref=phone_field, label="Telefone de Contato", value=current_phone,
                                 prefix_icon=ft.Icons.PHONE, border_radius=10),
                    ft.Row([
                        ft.ElevatedButton("Atualizar Dados", icon=ft.Icons.SAVE, bgcolor=ft.colors.BLUE,
                                          color=ft.colors.WHITE, on_click=update_company_data),
                        ft.ElevatedButton("Fazer Upgrade", icon=ft.Icons.UPGRADE, bgcolor=ft.colors.GREEN,
                                          color=ft.colors.WHITE, on_click=lambda e: page.launch_url("https://example.com/upgrade"))
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                ],
                spacing=15
            )
        ]),
        ft.Divider(height=2, color=ft.colors.GREY_400),
        ft.Text("Informações do Plano", size=20, weight=ft.FontWeight.BOLD),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.AIRPLANE_TICKET, color=ft.colors.BLUE), ft.Text(
                        f"Plano Atual: {user_plan.capitalize()}", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Row([ft.Icon(ft.Icons.BUSINESS, color=ft.colors.BLUE), ft.Text(
                        f"Limites: {user_plan_limits[user_plan]['messages']} mensagens, {user_plan_limits[user_plan]['pdfs']} PDFs", size=14)]),
                    ft.Row([ft.Icon(ft.Icons.MESSAGE, color=ft.colors.BLUE), ft.Text(
                        f"Mensagens Enviadas: {usage_tracker.get_usage('messages_sent') if usage_tracker else 0}", size=14)]),
                    ft.Row([ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ft.colors.BLUE), ft.Text(
                        f"PDFs Processados: {usage_tracker.get_usage('pdfs_processed') if usage_tracker else 0}", size=14)])
                ], spacing=10),
                padding=15
            ),
            elevation=3
        )
    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER, expand=True)

    return profile_content
