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
            page.go("/profile")
        elif selected_index == 1:
            page.go("/clients")
        elif selected_index == 2:
            page.go("/dashboard")
    username = page.client_storage.get("username")
    saved_avatar = page.client_storage.get("user_avatar")


    # Cabeçalho do Drawer
    drawer_header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    username,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=current_color_scheme.primary,
                ),
                ft.Stack(
                    [
                        ft.CircleAvatar(
                            foreground_image_src=saved_avatar if saved_avatar else "https://picsum.photos/150",
                        ),
                        ft.Container(
                            content=ft.CircleAvatar(bgcolor=ft.Colors.GREEN, radius=5),
                            alignment=ft.alignment.bottom_left,
                        ),
                    ],
                    width=40,
                    height=40,
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
            ft.Divider(), 
            ft.NavigationDrawerDestination(
                label="Perfil",
                icon=ft.Icons.PERSON_OUTLINED
            ),
            ft.NavigationDrawerDestination(
                label="Clientes",
                icon=ft.Icons.PEOPLE_OUTLINED),
            ft.NavigationDrawerDestination(
                label="Dashboard",
                icon=ft.Icons.DASHBOARD_OUTLINED
            ),
        ]
    )

    return drawer
