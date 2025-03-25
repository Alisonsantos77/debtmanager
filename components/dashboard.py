import flet as ft
from charts import create_pie_chart, create_bar_chart, create_conversion_chart
from utils.theme_utils import get_current_color_scheme


def create_dashboard_page(clients_list, page: ft.Page):
    history = [
        type('History', (), {'status': 'enviado', 'sent_at': '10/03/2023 10:00'}),
        type('History', (), {'status': 'falha', 'sent_at': '15/04/2023 12:00'}),
        type('History', (), {'status': 'enviado', 'sent_at': '20/05/2023 14:00'}),
    ] * 10

    for h in history:
        h.converted = True if h.status == 'enviado' else False

    current_color_scheme = get_current_color_scheme(page)

    return ft.Column([
        ft.ResponsiveRow([
            ft.Container(
                col={"xs": 12, "md": 5},
                content=ft.Column([
                    ft.Text(
                        "Status dos Clientes",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=current_color_scheme.on_surface
                    ),
                    create_pie_chart(history, page)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ),
        ]),
        ft.ResponsiveRow([
            ft.Container(
                col={"xs": 12, "md": 5},
                content=ft.Column([
                    ft.Text(
                        "Taxa de Conversão",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=current_color_scheme.on_surface
                    ),
                    create_conversion_chart(history, page)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ),
        ]),
                    ft.Container(
                col={"xs": 12, "md": 12},
                content=ft.Column([
                    ft.Text(
                        "Dívidas por Vencimento",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=current_color_scheme.on_surface
                    ),
                    create_bar_chart(history, page)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ),

    ], expand=True)
