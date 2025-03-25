import logging
import flet as ft
from utils.theme_utils import get_current_color_scheme

logger = logging.getLogger(__name__)


def create_dialogs(page, message_input, bulk_message_input, message_templates, usage_tracker, clients_list, filtered_clients, send_bulk_message, selected_client, update_client_list):
    current_color_scheme = get_current_color_scheme(page)

    class CustomDialog:
        def __init__(self, title, content, actions):
            self.dialog = ft.AlertDialog(
                title=title, content=content, actions=actions, actions_alignment=ft.MainAxisAlignment.END)

        def open_dialog(self):
            page.overlay.append(self.dialog)
            self.dialog.open = True
            page.update()

        def close_dialog(self):
            self.dialog.open = False
            page.update()

    usage_dialog = CustomDialog(
        ft.Text("Informações do Plano", size=20, weight=ft.FontWeight.BOLD),
        ft.Text("Carregando...", size=16, color=current_color_scheme.on_surface),
        [ft.TextButton("Fechar", on_click=lambda e: usage_dialog.close_dialog())]
    )

    bulk_send_dialog = CustomDialog(
        ft.Text("Enviar para Todos", size=20, weight=ft.FontWeight.BOLD),
        ft.Column([
            ft.Dropdown(
                label="Modelo de Mensagem",
                options=[ft.dropdown.Option(key) for key in message_templates.templates.keys()],
                value=message_templates.selected_template,
                on_change=lambda e: [message_templates.set_template(e.control.value),
                                     setattr(bulk_message_input, 'value',
                                             message_templates.get_template(e.control.value)),
                                     page.update()],
                width=300,
                # color=current_color_scheme.on_surface,
                # label_style=ft.TextStyle(color=current_color_scheme.primary),
                border_color=current_color_scheme.outline
            ),
            bulk_message_input
        ], spacing=10),
        [
            ft.Row([
                ft.TextButton("Cancelar", on_click=lambda e: bulk_send_dialog.close_dialog()),
                ft.ElevatedButton("Enviar", bgcolor=current_color_scheme.primary,
                                  color='white',
                                  on_click=lambda e: page.run_task(send_bulk_message))
            ], alignment=ft.MainAxisAlignment.END)
        ]
    )

    progress_bar = ft.ProgressBar(width=300, value=0, bgcolor=ft.Colors.GREY_300, color=current_color_scheme.primary)
    bulk_send_feedback = ft.Column(spacing=10)
    bulk_send_feedback_dialog = CustomDialog(
        ft.Text("Progresso do Envio", size=20, weight=ft.FontWeight.BOLD),
        ft.Column(scroll=ft.ScrollMode.HIDDEN, controls=[progress_bar, bulk_send_feedback], spacing=10),
        [ft.TextButton("Fechar", on_click=lambda e: bulk_send_feedback_dialog.close_dialog(), disabled=True)]
    )

    template_dropdown = ft.Dropdown(
        label="Modelo de Mensagem",
        options=[ft.dropdown.Option(key) for key in message_templates.templates.keys()],
        value=message_templates.selected_template,
        on_change=lambda e: [message_templates.set_template(e.control.value),
                             setattr(message_input, 'value', message_templates.get_template(e.control.value) if not selected_client else message_templates.get_template(e.control.value).format(
                                 name=selected_client.name, debt_amount=selected_client.debt_amount,
                                 due_date=selected_client.due_date, reason=getattr(selected_client, 'reason', 'pendência'))),
                             page.update()],
        width=300,
        # color=current_color_scheme.on_surface,
        # label_style=ft.TextStyle(color=current_color_scheme.on_surface),
        border_color=current_color_scheme.outline
    )

    error_dialog = CustomDialog(
        ft.Text("Erro", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
        ft.Text("Ocorreu um erro ao processar sua solicitação. Tente novamente.",
                size=16, color=current_color_scheme.on_surface),
        [ft.TextButton("Fechar", on_click=lambda e: error_dialog.close_dialog())]
    )

    about_dialog = CustomDialog(
        ft.Text("Sobre o AutomaFlet", size=20, weight=ft.FontWeight.BOLD),
        ft.Column([
            ft.Text("Versão: 1.0.0", size=16),
            ft.Text("Desenvolvido por: Alison Santos", size=16),
            ft.Text("GitHub: github.com/Alisonsantos77/AutomaFlet", size=16),
            ft.Text("Descrição: Ferramenta para automação de envio de notificações de dívidas.", size=16, italic=True)
        ], spacing=10),
        [ft.TextButton("Fechar", on_click=lambda e: about_dialog.close_dialog())]
    )

    return {
        "usage_dialog": usage_dialog,
        "bulk_send_dialog": bulk_send_dialog,
        "bulk_send_feedback_dialog": bulk_send_feedback_dialog,
        "template_dropdown": template_dropdown,
        "error_dialog": error_dialog,
        "about_dialog": about_dialog,
        "progress_bar": progress_bar,
        "bulk_send_feedback": bulk_send_feedback
    }
