import flet as ft
from models import PendingClient
from utils import calculate_total_debt
from flet import Container, Column, Row, Text


def create_client_row(client: PendingClient, on_select):
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border_radius=5,
        padding=5,
        content=ft.Row([
            ft.Text(client.name, width=150, size=12,
                    weight='bold', color=ft.Colors.ON_SURFACE),
            ft.Text(client.debt_amount, width=80,
                    color=ft.Colors.ERROR, size=12),
            ft.Text(client.due_date, width=80, size=12,
                    color=ft.Colors.ON_SURFACE),
            ft.Text(client.status, width=80, color=ft.Colors.SECONDARY if client.status ==
                    "Renegociado" else ft.Colors.TERTIARY, size=12),
            ft.IconButton(icon=ft.Icons.MESSAGE, icon_size=20,
                          icon_color=ft.Colors.PRIMARY, on_click=lambda e: on_select(client))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        on_click=lambda e: on_select(client)
    )


def create_status_card(last_sent=None, page=None):
    content = "Nenhum envio recente." if not last_sent else f"Último envio: {last_sent}"
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border_radius=5,
        padding=10,
        content=ft.Text(content, size=12, color=ft.Colors.ON_SURFACE)
    )


def create_dashboard_header(clients, page=None):
    total_debt = calculate_total_debt(clients)
    num_clients = len(clients)
    atraso_count = len([c for c in clients if "atraso" in c.status.lower()])
    return ft.ResponsiveRow([
        Container(
            col={"xs": 12, "sm": 4, "md": 3},
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            padding=10,
            content=Column([
                Row([ft.Icon(ft.Icons.MONEY_OFF, color=ft.Colors.ERROR),
                     ft.Text("Total Pendente", size=14, color=ft.Colors.ON_SURFACE)]),
                Text(f"R$ {total_debt:.2f}", size=20,
                     weight='bold', color=ft.Colors.ERROR)
            ])
        ),
        Container(
            col={"xs": 12, "sm": 4, "md": 3},
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            padding=10,
            content=Column([
                Row([ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.PRIMARY),
                     ft.Text("Clientes", size=14, color=ft.Colors.ON_SURFACE)]),
                Text(str(num_clients), size=20,
                     weight='bold', color=ft.Colors.PRIMARY)
            ])
        ),
        Container(
            col={"xs": 12, "sm": 4, "md": 3},
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            padding=10,
            content=Column([
                Row([ft.Icon(ft.Icons.WARNING, color=ft.Colors.TERTIARY),
                     ft.Text("Em Atraso", size=14, color=ft.Colors.ON_SURFACE)]),
                Text(f"{atraso_count}", size=20,
                     weight='bold', color=ft.Colors.TERTIARY)
            ])
        )
    ], spacing=10)
