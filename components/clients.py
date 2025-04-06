import datetime
from typing import Callable, List

import flet as ft

from utils.theme_utils import get_current_color_scheme


def create_clients_page(
    clients_list: List,
    filtered_clients: List,
    current_page: int,
    client_list_view: ft.ListView,
    messages_view: ft.Column,
    last_sent,
    dialogs: dict,
    page: ft.Page,
    update_client_list: Callable[[], None],
) -> ft.Control:
    """Cria a página de clientes com lista e área de mensagens."""
    current_color_scheme = get_current_color_scheme(page)

    # Botão para abrir o DatePicker
    filter_date_button = ft.ElevatedButton(
        "Filtrar por Data",
        on_click=lambda e: page.open(date_picker),
        icon=ft.Icons.CALENDAR_TODAY,
        style=ft.ButtonStyle(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )

    selected_date_text = ft.Text(
        f"Data Selecionada: Nenhuma",
        size=12,
        color=current_color_scheme.primary,
        weight=ft.FontWeight.NORMAL,
    )

    def on_date_change(e):
        # Atualiza o texto com a data selecionada
        selected_date_text.value = f"Data Selecionada: {e.control.value.strftime('%d/%m/%Y') if e.control.value else 'Nenhuma'}"
        search_and_filter_clients(None)
        if date_picker in page.overlay:
            page.overlay.remove(date_picker)
        page.update()

    def on_date_dismiss(e):
        if date_picker in page.overlay:
            page.overlay.remove(date_picker)
        page.update()

    date_picker = ft.DatePicker(
        first_date=datetime.datetime(2023, 1, 1),
        last_date=datetime.datetime(2026, 12, 31),
        on_change=on_date_change,
        on_dismiss=on_date_dismiss
    )

    page.overlay.append(date_picker)

    # Função para filtrar clientes
    def search_and_filter_clients(e):
        nonlocal filtered_clients, current_page
        query = search_field.value.lower()
        filtered_clients.clear()
        for client in clients_list:
            search_match = query in client.name.lower()
            date_match = (
                selected_date_text.value == f"Data Selecionada: {client.due_date}"
                if selected_date_text.value != "Data Selecionada: Nenhuma"
                else True
            )
            if search_match and date_match:
                filtered_clients.append(client)
        current_page = 0
        update_client_list()

    search_field = ft.TextField(
        label="Buscar Cliente",
        on_change=search_and_filter_clients,
        border_color=current_color_scheme.primary,
        height=50,
        border_radius=10,
        suffix=ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color=current_color_scheme.primary,
            on_click=lambda e: [
                setattr(search_field, 'value', ''),
                setattr(selected_date_text, 'value', 'Data Selecionada: Nenhuma'),
                filtered_clients.clear(),
                filtered_clients.extend(clients_list),
                update_client_list(),
                page.update()
            ],
        ),
    )

    return ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Row([
                    search_field,
                    filter_date_button
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
                selected_date_text,
                client_list_view
            ], expand=2),
            ft.VerticalDivider(width=1, color=current_color_scheme.primary_container),
            ft.Column([messages_view], expand=3)
        ], expand=True),
        padding=10,
        expand=True
    )
