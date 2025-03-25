import flet as ft
import logging
from utils.theme_utils import get_current_color_scheme

logger = logging.getLogger(__name__)


def create_drawer(page: ft.Page, company_data: dict):
    """Cria e retorna um NavigationDrawer funcional."""
    current_color_scheme = get_current_color_scheme(page)
    def handle_drawer_change(e, page):
        """Gerencia a mudança de seleção no drawer."""
        selected_index = e.control.selected_index
        # Substituído print por logging
        logger.info(f"Drawer selecionado: {selected_index}")

        if selected_index == 0:
            page.go("/clients")
        elif selected_index == 1:
            page.go("/dashboard")
        elif selected_index == 2:
            page.go("/settings")
        elif selected_index == 3:
            page.go("/profile")

    # Cabeçalho do Drawer
    drawer_header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    company_data["name"],
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=current_color_scheme.primary,
                ),
                ft.CircleAvatar(
                    content=ft.Image(
                        src=company_data["logo"],
                        fit=ft.ImageFit.COVER,
                        border_radius=50,
                    ),
                    radius=30,
                    bgcolor=current_color_scheme.primary_container
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.all(15),
    )

    # Criando o Drawer
    drawer = ft.NavigationDrawer(
        on_change=lambda e: handle_drawer_change(e, page),
        controls=[
            drawer_header,
            ft.Divider(),  # Linha divisória
            ft.NavigationDrawerDestination(
                label="Clientes",
                icon=ft.Icons.PEOPLE_OUTLINED),
            ft.NavigationDrawerDestination(
                label="Dashboard",
                icon=ft.Icons.DASHBOARD_OUTLINED
            ),
            ft.NavigationDrawerDestination(
                label="Configurações",
                icon=ft.Icons.SETTINGS_OUTLINED
            ),
            ft.NavigationDrawerDestination(
                label="Perfil",
                icon=ft.Icons.PERSON_OUTLINED
            ),
        ]
    )

    return drawer  # Retorna o drawer corretamente
