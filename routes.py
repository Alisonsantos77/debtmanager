import logging

import flet as ft

from components.client_details import create_client_details_page
from components.dashboard import create_dashboard_page
from components.navigation_drawer import create_drawer
from components.profile_page import ProfilePage
from components.settings import create_settings_page
from utils.theme_utils import get_current_color_scheme

logger = logging.getLogger(__name__)


def setup_routes(page: ft.Page, layout, layout_data, app_state, company_data: dict):
    current_color_scheme = get_current_color_scheme(page)

    def route_change(route):
        company_data.update({
            "name": company_data.get("name", "DebtManager"),
            "logo": company_data.get("logo", "https://picsum.photos/150"),
            "contact_email": company_data.get("contact_email", "example@email.com"),
            "phone": company_data.get("phone", "(11) 99999-9999"),
            "plan": company_data.get("plan", "basic")
        })

        class create_appbar(ft.AppBar):
            def __init__(self, title):
                super().__init__(
                    title=ft.Text(
                        f"{company_data['name']} - {title}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=current_color_scheme.primary
                    ),
                    bgcolor=current_color_scheme.background,
                    center_title=True,
                    actions=[
                     
                        # ft.Container(
                        #     content=ft.Stack(
                        #         [
                        #             ft.CircleAvatar(
                        #                 foreground_image_src="https://robohash.org/{username}.png",
                        #                 content=ft.Text(user_initials),
                        #             ),
                        #             ft.Container(
                        #                 content=ft.CircleAvatar(
                        #                     bgcolor=ft.colors.GREEN, radius=5),
                        #                 alignment=ft.alignment.bottom_left,
                        #             ),
                        #         ],
                        #         width=40,
                        #         height=40,
                        #     ),
                        #     tooltip=f"Logado como {username}",
                        # ),
                        ft.PopupMenuButton(
                            icon=ft.Icons.PERSON,
                            tooltip="Perfil",
                            icon_color=current_color_scheme.primary,
                            content=ft.CircleAvatar(
                                content=ft.Image(
                                    src=company_data["logo"],
                                    fit=ft.ImageFit.COVER,
                                    border_radius=50,
                                ),
                                radius=30,
                                bgcolor=current_color_scheme.primary_container
                                ),
                            items=[
                                ft.PopupMenuItem(
                                    text="Meu Perfil",
                                    icon=ft.Icons.PERSON_OUTLINE,
                                    on_click=lambda e: page.go("/profile")
                                ),
                                ft.PopupMenuItem(
                                    text="Alterar Tema",
                                    icon=ft.Icons.WB_SUNNY_OUTLINED,
                                    on_click=lambda e: layout_data["toggle_theme"](),
                                ),
                                ft.PopupMenuItem(
                                    text="Configurações",
                                    icon=ft.Icons.SETTINGS,
                                    on_click=lambda e: page.go("/settings")
                                ),
                            ]
                        ),
                    ]
                )

        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                drawer=create_drawer(page, company_data),
                appbar=create_appbar("DebtManager"),
                controls=[layout]
            )
        )

        if page.route == "/clients":
            page.title = "Clientes"
            page.views.append(
                ft.View(
                    route="/clients",
                    drawer=create_drawer(page, company_data),
                    appbar=create_appbar("Clientes"),
                    controls=[layout],
                    scroll=ft.ScrollMode.HIDDEN
                )
            )
        elif page.route == "/dashboard":
            page.title = "Dashboard"
            page.views.append(
                ft.View(
                    route="/dashboard",
                    drawer=create_drawer(page, company_data),
                    appbar=create_appbar("Dashboard"),
                    controls=[create_dashboard_page(layout_data["clients_list"], page)],
                    scroll=ft.ScrollMode.HIDDEN
                )
            )
        elif page.route == "/settings":
            page.title = "Configurações"
            page.views.append(
                ft.View(
                    route="/settings",
                    drawer=create_drawer(page, company_data),
                    appbar=create_appbar("Configurações"),
                    controls=[create_settings_page()],
                    scroll=ft.ScrollMode.HIDDEN
                )
            )
        elif page.route == "/profile":
            page.title = "Perfil"
            page.views.append(
                ft.View(
                    route="/profile",
                    drawer=create_drawer(page, company_data),
                    appbar=create_appbar("Perfil"),
                    controls=[ProfilePage(page, company_data, app_state)],
                    scroll=ft.ScrollMode.HIDDEN
                )
            )

        logger.info(f"Rota alterada para: {page.route}")
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        logger.info(f"View atual: {top_view.route}")
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
