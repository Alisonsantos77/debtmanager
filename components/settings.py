"""Settings page components."""
import flet as ft


def create_settings_page() -> ft.Control:
    """Create the settings page."""
    return ft.Column(
        controls=[
            ft.Text("Configurações", size=20,
                    weight='bold', color=ft.Colors.BLACK),
            ft.Text("Aqui você pode ajustar as configurações da aplicação.",
                    color=ft.Colors.BLACK),
            ft.Text("Política de Privacidade", size=16,
                    weight='bold', color=ft.Colors.BLACK),
            ft.Text(
                "Nós respeitamos sua privacidade e estamos em conformidade com a LGPD. "
                "Seus dados são armazenados de forma segura e usados apenas para os fins descritos. "
                "Para mais detalhes, entre em contato com nosso suporte.",
                size=14,
                color=ft.Colors.BLACK
            )
        ],
        expand=True,
        spacing=15,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
