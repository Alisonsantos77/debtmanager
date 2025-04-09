import os
import flet as ft
import logging
from utils.theme_utils import get_current_color_scheme

logger = logging.getLogger(__name__)


def create_drawer(page: ft.Page, company_data: dict):
    """Cria e retorna um NavigationDrawer estilizado."""
    current_color_scheme = get_current_color_scheme(page)

    def handle_drawer_change(e, page):
        """Gerencia a mudança de seleção no drawer."""
        selected_index = e.control.selected_index
        logger.info(f"Drawer selecionado: {selected_index}")

        if selected_index == 0:
            page.go("/profile")
        elif selected_index == 1:
            page.go("/clients")
        elif selected_index == 2:
            page.go("/dashboard")

    prefix = os.getenv("PREFIX")
    URL_DICEBEAR = os.getenv("URL_DICEBEAR")
    username = page.client_storage.get("username")
    saved_avatar = page.client_storage.get(f"{prefix}avatar")

    drawer_header = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Stack(
                            [
                                ft.CircleAvatar(
                                    foreground_image_src=saved_avatar if saved_avatar else f"{URL_DICEBEAR}seed={username}",
                                    width=60,
                                    height=60,
                                ),
                                ft.Container(
                                    content=ft.CircleAvatar(bgcolor=ft.Colors.GREEN, radius=5),
                                    alignment=ft.alignment.bottom_left,
                                ),
                            ],
                            width=50,
                            height=50,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    value=f"{username}" if username else "DebtManager",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=current_color_scheme.primary,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    "Gerencie suas dívidas",
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                    italic=True,
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=15,
                ),
            ],
            spacing=10,
        ),
        padding=ft.padding.symmetric(vertical=20, horizontal=15),
        border_radius=ft.border_radius.only(top_left=15, top_right=15),
    )

    drawer = ft.NavigationDrawer(
        elevation=5,
        indicator_shape=ft.RoundedRectangleBorder(radius=10),
        tile_padding=ft.padding.symmetric(vertical=5, horizontal=10),
        on_change=lambda e: handle_drawer_change(e, page),
        selected_index=1,
        controls=[
            drawer_header,
            ft.Divider(thickness=1, color=ft.Colors.GREY_300),
            ft.NavigationDrawerDestination(
                label="Perfil",
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                icon_content=ft.Icon(ft.Icons.PERSON_OUTLINE, color=ft.Colors.GREY_700),
                selected_icon_content=ft.Icon(ft.Icons.PERSON, color=current_color_scheme.primary),
            ),
            ft.NavigationDrawerDestination(
                label="Clientes",
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                icon_content=ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=ft.Colors.GREY_700),
                selected_icon_content=ft.Icon(ft.Icons.PEOPLE, color=current_color_scheme.primary),
            ),
            ft.NavigationDrawerDestination(
                label="Dashboard",
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                icon_content=ft.Icon(ft.Icons.DASHBOARD_OUTLINED, color=ft.Colors.GREY_700),
                selected_icon_content=ft.Icon(ft.Icons.DASHBOARD, color=current_color_scheme.primary),
            ),
            ft.Container(height=20),
        ],
    )

    return drawer
