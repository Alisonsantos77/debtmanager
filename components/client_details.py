import flet as ft
from typing import List
from models.pending_client import PendingClient
from charts import create_charts_container
from utils.database import get_client_history


def create_client_details_page(
    client_name: str,
    clients_list: List[PendingClient],
    user_plan: str,
    page: ft.Page
) -> ft.Control:
    """Create the client details page."""
    client = next((c for c in clients_list if c.name == client_name), None)
    if not client:
        return ft.Text("Cliente não encontrado.", size=16)

    history = get_client_history(client.name)
    charts_container = create_charts_container(clients_list, history, page)
    details_controls = [
        ft.Text(f"Nome: {client.name}", size=16,
                color=page.theme.color_scheme.on_surface),
        ft.Text(f"Valor Pendente: {client.debt_amount}",
                size=16, color=page.theme.color_scheme.error),
        ft.Text(f"Vencimento: {client.due_date}", size=16,
                color=page.theme.color_scheme.on_surface),
        ft.Text(f"Status: {client.status}", size=16,
                color=page.theme.color_scheme.on_surface),
    ]
    if user_plan == "premium":
        details_controls.append(ft.Text(
            f"Contato: {client.contact}", size=16, color=page.theme.color_scheme.on_surface))
        details_controls.append(ft.Text(
            "Histórico de Avisos", size=18, weight='bold', color=page.theme.color_scheme.on_surface))
        details_controls.extend([ft.Text(f"{h.sent_at}: {h.status} - {h.message}",
                                size=14, color=page.theme.color_scheme.on_surface) for h in history])
    else:
        details_controls.append(ft.Text(
            "Atualize para o plano Premium para ver mais detalhes!", size=14, color=page.theme.color_scheme.error))

    details_controls.append(ft.Text("Gráficos de Análise", size=18, weight='bold',
                                    color=page.theme.color_scheme.on_surface))
    details_controls.append(charts_container)

    return ft.Column(
        controls=details_controls,
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
