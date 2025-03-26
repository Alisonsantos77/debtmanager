import flet as ft
import os
from dotenv import load_dotenv

load_dotenv()
LOTTIE_LOADING = os.getenv(
    "LOTTIE_LOADING_URL")
LOTTIE_SUCCESS = os.getenv(
    "LOTTIE_SUCCESS_URL")


def loading_animation(message: str = "Processando...") -> ft.Column:
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
