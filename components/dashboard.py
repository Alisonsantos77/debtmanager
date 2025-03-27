import flet as ft
from charts import create_charts_container
import logging

logger = logging.getLogger(__name__)


def create_dashboard_page(clients_list, history, page: ft.Page):
    """Create the dashboard page with charts."""
    logger.info("Criando página de dashboard")

    charts_container = create_charts_container(clients_list, history, page)

    return ft.Column(
        controls=[
            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD,
                    color=page.theme.color_scheme.primary, text_align=ft.TextAlign.CENTER),
            charts_container
        ],
        alignment=ft.MainAxisAlignment.START,
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )
