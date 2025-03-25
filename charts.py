import flet as ft
from datetime import datetime
from typing import List
from models.pending_client import PendingClient
from utils.theme_utils import get_current_color_scheme


def create_pie_chart(history, page: ft.Page):
    
    current_color_scheme = get_current_color_scheme(page)
    
    success_count = sum(1 for h in history if h.status.lower() == "enviado")
    failure_count = len(history) - success_count
    normal_radius = 120
    hover_radius = 130
    normal_title_style = ft.TextStyle(
        size=14, color=current_color_scheme.on_surface, weight=ft.FontWeight.BOLD
    )
    hover_title_style = ft.TextStyle(
        size=16,
        color=current_color_scheme.on_surface,
        weight=ft.FontWeight.BOLD,
        shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK54),
    )
    normal_badge_size = 40
    hover_badge_size = 50

    def badge(icon, size):
        return ft.Container(
            ft.Icon(icon, color=current_color_scheme.on_surface),
            width=size,
            height=size,
            border=ft.border.all(1, current_color_scheme.outline),
            border_radius=size / 2,
            bgcolor=current_color_scheme.primary_container,
        )

    def on_chart_event(e: ft.PieChartEvent):
        for idx, section in enumerate(chart.sections):
            if idx == e.section_index:
                section.radius = hover_radius
                section.title_style = hover_title_style
            else:
                section.radius = normal_radius
                section.title_style = normal_title_style
        chart.update()

    chart = ft.PieChart(
        sections=[
            ft.PieChartSection(
                value=success_count,
                color=current_color_scheme.primary,
                radius=normal_radius,
                title=f"Sucesso: {success_count}",
                title_style=normal_title_style,
                badge=badge(ft.Icons.CHECK_CIRCLE, normal_badge_size),
                badge_position=0.95,
            ),
            ft.PieChartSection(
                value=failure_count,
                color=ft.Colors.RED,
                radius=normal_radius,
                title=f"Falha: {failure_count}",
                title_style=normal_title_style,
                badge=badge(ft.Icons.ERROR, normal_badge_size),
                badge_position=0.95,
            )
        ],
        sections_space=4,
        center_space_radius=50,
        width=350,
        height=350,
        animate=500,
        on_chart_event=on_chart_event,
    )

    return ft.Container(
        content=chart,
        bgcolor=current_color_scheme.surface,
        border=ft.border.all(1, current_color_scheme.outline),
        padding=10,
        border_radius=10,
    )


def create_line_chart(debt_amount: str, page: ft.Page):
    current_color_scheme = get_current_color_scheme(page)
    debt_value = float(debt_amount.replace("R$", "").replace(".", "").replace(",", ".").strip())
    simulated_values = [debt_value * (1 - i * 0.1) for i in range(6)]

    text_color = current_color_scheme.on_surface
    tooltip_bgcolor = ft.Colors.with_opacity(0.9, current_color_scheme.primary_container)

    return ft.LineChart(
        data_series=[
            ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(x=i, y=simulated_values[i], tooltip=f"Mês {i+1}: R${simulated_values[i]:.2f}")
                    for i in range(len(simulated_values))
                ],
                stroke_width=4,
                color=current_color_scheme.primary,
                curved=True,
                stroke_cap_round=True
            )
        ],
        border=ft.border.all(2, current_color_scheme.outline),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_300, width=1, dash_pattern=[3, 3]),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Meses", color=text_color, size=14),
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(f"Mês {i+1}", size=12, color=text_color))
                for i in range(len(simulated_values))
            ],
            labels_size=40
        ),
        left_axis=ft.ChartAxis(
            title=ft.Text("Valor (R$)", color=text_color, size=14),
            labels=[
                ft.ChartAxisLabel(value=simulated_values[i], label=ft.Text(
                    f"R${simulated_values[i]:.0f}", size=12, color=text_color))
                for i in range(len(simulated_values))
            ],
            labels_size=40
        ),
        tooltip_bgcolor=tooltip_bgcolor,
        min_y=min(simulated_values) * 0.9,
        max_y=max(simulated_values) * 1.1,
        width=450,
        height=350,
        interactive=True,
        animate=1000,
        bgcolor=current_color_scheme.surface
    )


def create_bar_chart(history, page: ft.Page):
    current_color_scheme = get_current_color_scheme(page)

    monthly_counts = {}
    for h in history:
        sent_at = datetime.strptime(h.sent_at, "%d/%m/%Y %H:%M")
        month = sent_at.strftime("%b %Y")
        monthly_counts[month] = monthly_counts.get(month, 0) + 1

    labels = list(monthly_counts.keys())
    values = list(monthly_counts.values())

    display_labels = []
    for i in range(len(labels)):
        if i % 5 == 0:
            display_labels.append(
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(labels[i], size=12, color=current_color_scheme.on_surface, rotate=45)
                )
            )
        else:
            display_labels.append(
                ft.ChartAxisLabel(value=i, label=ft.Text(""))
            )

    text_color = current_color_scheme.on_surface
    tooltip_bgcolor = ft.Colors.with_opacity(0.9, current_color_scheme.primary_container)

    return ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=values[i],
                        width=25,
                        color=current_color_scheme.primary,
                        border_radius=5,
                        tooltip=f"{labels[i]}: {values[i]} avisos"
                    )
                ]
            )
            for i in range(len(values))
        ],
        border=ft.border.all(2, current_color_scheme.outline),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_300, width=1, dash_pattern=[3, 3]),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Meses", color=text_color, size=14),
            labels=display_labels,
            labels_size=50
        ),
        left_axis=ft.ChartAxis(
            title=ft.Text("Nº de Avisos", color=text_color, size=14),
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=12, color=text_color))
                for i in range(int(max(values) + 1))
            ],
            labels_size=40
        ),
        tooltip_bgcolor=tooltip_bgcolor,
        min_y=0,
        max_y=max(values) + 1 if values else 1,
        width=600,
        height=350,
        interactive=True,
        animate=1000,
        bgcolor=current_color_scheme.surface
    )


def create_conversion_chart(history, page: ft.Page):
    current_color_scheme = get_current_color_scheme(page)

    converted_count = sum(1 for h in history if hasattr(h, 'converted') and h.converted)
    not_converted_count = len(history) - converted_count

    text_color = current_color_scheme.on_surface

    chart = ft.PieChart(
        sections=[
            ft.PieChartSection(
                value=converted_count,
                color=current_color_scheme.primary,
                radius=120,
                title=f"Convertidos: {converted_count}",
                title_style=ft.TextStyle(color=text_color, size=14, weight=ft.FontWeight.BOLD)
            ),
            ft.PieChartSection(
                value=not_converted_count,
                color=ft.Colors.RED,
                radius=120,
                title=f"Não Convertidos: {not_converted_count}",
                title_style=ft.TextStyle(color=text_color, size=14, weight=ft.FontWeight.BOLD)
            )
        ],
        sections_space=4,
        center_space_radius=50,
        width=350,
        height=350,
        animate=500,
    )

    return ft.Container(
        content=chart,
        bgcolor=current_color_scheme.surface,
        border=ft.border.all(1, current_color_scheme.outline),
        padding=10,
        border_radius=10,
    )


def create_segment_analysis_chart(clients: List[PendingClient], page: ft.Page):
    current_color_scheme = get_current_color_scheme(page)

    segments = {"< R$1.000": 0, "R$1.000 - R$5.000": 0, "> R$5.000": 0}
    for client in clients:
        debt = float(client.debt_amount.replace("R$", "").replace(".", "").replace(",", ".").strip())
        if debt < 1000:
            segments["< R$1.000"] += 1
        elif 1000 <= debt <= 5000:
            segments["R$1.000 - R$5.000"] += 1
        else:
            segments["> R$5.000"] += 1

    labels = list(segments.keys())
    values = list(segments.values())

    text_color = current_color_scheme.on_surface
    tooltip_bgcolor = ft.Colors.with_opacity(0.9, current_color_scheme.primary_container)

    return ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=values[i],
                        width=25,
                        color=current_color_scheme.primary,
                        border_radius=5,
                        tooltip=f"{labels[i]}: {values[i]} clientes"
                    )
                ]
            )
            for i in range(len(values))
        ],
        border=ft.border.all(2, current_color_scheme.outline),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_300, width=1, dash_pattern=[3, 3]),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Segmentos", color=text_color, size=14),
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(labels[i], size=12, color=text_color))
                for i in range(len(labels))
            ],
            labels_size=40
        ),
        left_axis=ft.ChartAxis(
            title=ft.Text("Nº de Clientes", color=text_color, size=14),
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=12, color=text_color))
                for i in range(int(max(values) + 1))
            ],
            labels_size=40
        ),
        tooltip_bgcolor=tooltip_bgcolor,
        min_y=0,
        max_y=max(values) + 1 if values else 1,
        width=450,
        height=350,
        interactive=True,
        animate=1000,
        bgcolor=current_color_scheme.surface
    )
