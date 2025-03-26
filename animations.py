import flet as ft

LOTTIE_LOADING = "https://lottie.host/e651e108-963f-4983-a782-8ea9db7cca87/Q0wQ48OKBQ.json"
LOTTIE_SUCCESS = "https://lottie.host/95a8b77b-108b-4893-b3bb-2ea16b1a8a0e/dUl0wlFl1q.json"


def loading_animation(message: str = "Processando...") -> ft.Column:
    """Retorna uma coluna com a animação de carregamento e um texto dinâmico."""
    return ft.Column(
        controls=[
            ft.Lottie(
                src=LOTTIE_LOADING,
                repeat=True,
                animate=True,
                background_loading=True,
                expand=True
            ),
            ft.Text(message, size=18, weight=ft.FontWeight.BOLD)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )


def success_animation(message: str = "Sucesso!") -> ft.Column:
    """Retorna uma coluna com a animação de sucesso e um texto dinâmico."""
    return ft.Column(
        controls=[
            ft.Lottie(
                src=LOTTIE_SUCCESS,
                width=200,
                height=200,
                repeat=False,
                animate=True
            ),
            ft.Text(message, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
