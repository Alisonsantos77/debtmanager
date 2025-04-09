import logging
import os
import flet as ft
from datetime import datetime, timedelta
import asyncio

from components.activation import ActivationPage
from components.app_layout import create_app_layout
from components.client_details import create_client_details_page
from components.dashboard import create_dashboard_page
from components.login import LoginPage
from components.navigation_drawer import create_drawer
from components.profile_page import ProfilePage
from components.register import RegisterPage
from components.terms_page import TermsPage
from utils.database import get_client_history
from utils.theme_utils import get_current_color_scheme
from utils.supabase_utils import fetch_user_data

logger = logging.getLogger(__name__)


def setup_routes(page: ft.Page, layout, layout_data, app_state, company_data: dict):
    current_color_scheme = get_current_color_scheme(page)
    prefix = os.getenv("PREFIX")
    saved_avatar = page.client_storage.get(f"{prefix}avatar")
    username = page.client_storage.get(f"{prefix}username")
    user_id = page.client_storage.get(f"{prefix}user_id")
    URL_DICEBEAR = os.getenv("URL_DICEBEAR")


    def logout(e):
        page.client_storage.clear()
        logger.info("Usuário deslogado e Client Storage limpo")
        page.go("/login")
        page.update()
        
    def handle_close(e):
        page.close(dlg_modal)
        page.add(ft.Text(f"Modal dialog closed with action: {e.control.text}"))
        
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmação"),
        content=ft.Text("Você realmente deseja sair?"),
        actions=[
            ft.TextButton("Não", on_click=handle_close),
            ft.TextButton("Sim", on_click=logout),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: page.add(
            ft.Text("Modal dialog dismissed"),
        ),
    )
    async def get_client_storage_async(page, key, timeout=2):
        """Busca assíncrona do client_storage com timeout."""
        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: page.client_storage.get(key)),
                timeout=timeout
            )
            logger.debug(f"client_storage.get({key}) retornou: {result}")
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout ao buscar {key} do client_storage")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar {key} do client_storage: {e}")
            return None

    class CountDown(ft.Text):
        def __init__(self, page: ft.Page):
            super().__init__()
            self.page = page
            self.executando = False
            self.value = "Carregando..."
            self.expiration_date = None

        def did_mount(self):
            self.executando = True
            self.page.run_task(self.iniciar_contador)

        def will_unmount(self):
            self.executando = False

        async def iniciar_contador(self):
            """Inicializa o contador com busca segura."""
            prefix = os.getenv("PREFIX")
            expiration_key = f"{prefix}data_expiracao"

            # Tenta pegar do client_storage com timeout
            expiration_str = await get_client_storage_async(self.page, expiration_key)

            if not expiration_str and user_id:
                logger.info("Data_expiracao não encontrada no client_storage, buscando no Supabase")
                try:
                    user_data = fetch_user_data(user_id, self.page)
                    if user_data and "data_expiracao" in user_data:
                        expiration_str = user_data.get("data_expiracao")
                        self.page.client_storage.set(expiration_key, expiration_str)
                        logger.info(f"Data_expiracao salva no client_storage: {expiration_str}")
                    else:
                        logger.warning("Nenhuma data_expiracao encontrada no Supabase")
                except Exception as e:
                    logger.error(f"Erro ao buscar dados do Supabase: {e}")

            if not expiration_str:
                self.value = "Sem expiração!"
                self.update()
                return

            try:
                self.expiration_date = datetime.fromisoformat(expiration_str.replace("Z", "+00:00"))
                logger.info(f"Contador iniciado com expiration_date: {self.expiration_date}")
                await self.atualizar_timer()
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao parsear data_expiracao: {e}")
                self.value = "Data inválida!"
                self.update()

        async def atualizar_timer(self):
            """Atualiza o contador em tempo real."""
            while self.executando and self.expiration_date:
                now = datetime.now(self.expiration_date.tzinfo)
                segundos_restantes = int((self.expiration_date - now).total_seconds())

                if segundos_restantes <= 0:
                    self.value = "Expirado!"
                    self.update()
                    break

                dias, resto_segundos = divmod(segundos_restantes, 86400)
                horas, resto_segundos = divmod(resto_segundos, 3600)
                minutos, segundos = divmod(resto_segundos, 60)
                self.value = f"{dias}d {horas}h {minutos}m {segundos}s"
                self.update()
                await asyncio.sleep(1)

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
                countdown = CountDown(page) if user_id else ft.Text("Não logado", size=14)

                super().__init__(
                    title=ft.Text(
                        f"{title}",
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
                                        foreground_image_src=saved_avatar if saved_avatar else f"{URL_DICEBEAR}seed={username}",
                                        width=45,
                                        height=45,
                                    ),
                                    ft.Container(
                                        content=ft.CircleAvatar(bgcolor=ft.Colors.GREEN, radius=5),
                                        alignment=ft.alignment.bottom_left,
                                    ),
                                ],
                                width=35,
                                height=35,
                            ),
                            items=[
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.PERSON_4_SHARP,
                                                size=20,
                                                color=current_color_scheme.primary,
                                            ),
                                            ft.Text(
                                                value=username or "Usuário",
                                                size=14,
                                                color=current_color_scheme.primary,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ]
                                    ),
                                    on_click=lambda e: page.go("/profile")
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.CALENDAR_MONTH_ROUNDED,
                                                size=20,
                                                color=current_color_scheme.primary,
                                            ),
                                            ft.Text(
                                                value=page.client_storage.get(f"{prefix}user_plan") or "Plano Básico",
                                                size=14,
                                                color=current_color_scheme.primary,
                                            ),
                                        ]
                                    ),
                                    disabled=True
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.TIMER,
                                                size=20,
                                                color=current_color_scheme.primary,
                                            ),
                                            countdown
                                        ]
                                    ),
                                    disabled=True
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.WB_SUNNY_OUTLINED,
                                                size=20,
                                                color=current_color_scheme.primary,
                                            ),
                                            ft.Text(
                                                value="Alterar Tema",
                                                size=14,
                                                color=current_color_scheme.primary,
                                            ),
                                        ]
                                    ),
                                    on_click=lambda e: app_state.get("toggle_theme", lambda: None)()
                                ),
                                ft.PopupMenuItem(),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.SETTINGS,
                                                size=20,
                                                color=current_color_scheme.primary,
                                            ),
                                            ft.Text(
                                                value="Perfil",
                                                size=14,
                                                color=current_color_scheme.primary,
                                            ),
                                        ]
                                    ),
                                    on_click=lambda e: page.go("/profile")
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(
                                                name=ft.Icons.LOGOUT_SHARP,
                                                size=20,
                                                color=ft.Colors.RED,
                                            ),
                                            ft.Text(
                                                value="Sair",
                                                size=14,
                                                color=ft.Colors.RED,
                                            ),
                                        ]
                                    ),
                                    on_click=lambda e: page.open(dlg_modal),
                                ),
                            ]
                        ),
                    ]
        )
        page.views.clear()
        page.title = "Login"
        page.views.append(
            ft.View(
                route="/login",
                controls=[LoginPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ))

        if page.route == "/clients":
            layout, app_state_new = create_app_layout(page)
            app_state.update(app_state_new)
            page.title = "Clientes"
            page.window.height = 720.0
            page.window.width = 1280.0
            page.window.min_height = 720.0
            page.window.min_width = 1280.0
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
            page.window.height = 960.0
            page.window.width = 1000.0
            page.views.append(
                ft.View(
                    route="/register",
                    appbar=ft.AppBar(
                        bgcolor=ft.Colors.TRANSPARENT,
                        center_title=True,
                    ),
                    controls=[RegisterPage(page)],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/activation":
            page.title = "Ativação"
            page.views.append(
                ft.View(
                    route="/activation",
                    appbar=ft.AppBar(
                        title=ft.Text("Ativação", size=20, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.TRANSPARENT,
                        center_title=True,
                    ),
                    controls=[ActivationPage(page)],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/terms":
            page.title = "Termos de Uso"
            page.views.append(
                ft.View(
                    route="/terms",
                    scroll=ft.ScrollMode.HIDDEN,
                    appbar=ft.AppBar(
                        title=ft.Text("Termos de Uso", size=20, weight=ft.FontWeight.BOLD),
                        bgcolor=current_color_scheme.background,
                        center_title=True,
                    ),
                    controls=[TermsPage(page)]
                ))
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
