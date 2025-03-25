import flet as ft


def get_current_color_scheme(page: ft.Page):
    return (
        page.dark_theme.color_scheme if page.theme_mode == ft.ThemeMode.DARK
        else page.theme.color_scheme
    )
