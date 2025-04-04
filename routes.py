import logging
import flet as ft
from components.activation import ActivationPage
from components.client_details import create_client_details_page
from components.dashboard import create_dashboard_page
from components.login import LoginPage
from components.navigation_drawer import create_drawer
from components.profile_page import ProfilePage
from components.register import RegisterPage
from components.app_layout import create_app_layout
from utils.database import get_client_history
from utils.theme_utils import get_current_color_scheme

logger = logging.getLogger(__name__)


def setup_routes(page: ft.Page, layout, layout_data, app_state, company_data: dict):
    current_color_scheme = get_current_color_scheme(page)
    prefix = "debtmanager."
    saved_avatar = page.client_storage.get(f"{prefix}user_avatar")
    username = page.client_storage.get(f"{prefix}username")

    def logout(e):
        page.client_storage.clear()  
        logger.info("Usuário deslogado e Client Storage limpo")
        page.go("/login")
        page.update()

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
                        f"{username} - {title}" if username else title,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=current_color_scheme.primary
                    ),
                    bgcolor=current_color_scheme.background,
                    center_title=True,
                    actions=[
                        ft.PopupMenuButton(
                            icon=ft.Icons.PERSON,
                            tooltip="Perfil",
                            icon_color=current_color_scheme.primary,
                            content=ft.Stack(
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
                            items=[
                                ft.PopupMenuItem(
                                    text="Meu Perfil",
                                    icon=ft.Icons.PERSON_OUTLINE,
                                    on_click=lambda e: page.go("/profile")
                                ),
                                ft.PopupMenuItem(
                                    text="Alterar Tema",
                                    icon=ft.Icons.WB_SUNNY_OUTLINED,
                                    on_click=lambda e: app_state.get("toggle_theme", lambda: None)()
                                ),
                                ft.PopupMenuItem(
                                    text="Sair",
                                    icon=ft.Icons.EXIT_TO_APP,
                                    on_click=logout
                                )
                            ]
                        ),
                    ]
                )

        page.views.clear()
        page.views.append(
            ft.View(
                route="/login",
                controls=[LoginPage(page)],
                scroll=ft.ScrollMode.HIDDEN,
            ))

        if page.route == "/clients":
            # Cria o layout dinamicamente quando a rota é /clients
            layout, app_state_new = create_app_layout(page)
            app_state.update(app_state_new)  # Atualiza o app_state com os novos dados
            if layout is None:
                page.go("/login") 
            else:
                page.title = "Clientes"
                page.views.append(
                    ft.View(
                        route="/clients",
                        drawer=create_drawer(page, company_data),
                        appbar=create_appbar("Clientes"),
                        controls=[layout],
                        scroll=ft.ScrollMode.HIDDEN,
                    )
                )
        elif page.route == "/register":
            page.title = "Registro"
            page.views.append(
                ft.View(
                    route="/register",
                    controls=[RegisterPage(page)],
                    scroll=ft.ScrollMode.HIDDEN,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/activation":
            page.title = "Ativação"
            page.views.append(
                ft.View(
                    route="/activation",
                    controls=[ActivationPage(page)],
                    scroll=ft.ScrollMode.HIDDEN,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/dashboard":
            page.title = "Dashboard"
            history = get_client_history(None)
            page.views.append(
                ft.View(
                    route="/dashboard",
                    drawer=create_drawer(page, company_data),
                    appbar=create_appbar("Dashboard"),
                    controls=[create_dashboard_page(app_state.get("clients_list", []),
                                                    app_state.get("history", []), page)],
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
                    scroll=ft.ScrollMode.HIDDEN,
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
