import flet as ft
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ChartWithDateFilter(ft.Column):
    def __init__(self, clients_list, history, page: ft.Page):
        super().__init__(expand=True, alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO)
        self.clients_list = clients_list
        self.history = history
        self.page = page
        self.start_date_picker = ft.DatePicker(
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2025, 12, 31),
            on_change=self.update_charts,
        )
        self.end_date_picker = ft.DatePicker(
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2025, 12, 31),
            on_change=self.update_charts,
        )
        self.page.overlay.extend([self.start_date_picker, self.end_date_picker])

        self.controls = self.build_controls()

    async def redirect_after_snackbar(self):
        await asyncio.sleep(3)  
        self.page.go("/clients")
        self.page.update()

    def build_controls(self):
        if not self.clients_list and not self.history:
            logger.info("Nenhum dado disponível para gráficos")
            snack = ft.SnackBar(
                content=ft.Text("Carregue um relatório em /clients para ver os gráficos"),
                bgcolor=ft.Colors.BLUE_GREY,
                duration=3000, 
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            # Inicia a tarefa assíncrona pra redirecionar
            self.page.run_task(self.redirect_after_snackbar)
            return [
                ft.Text(
                    "Nenhum relatório carregado",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=self.page.theme.color_scheme.primary,
                    text_align=ft.TextAlign.CENTER
                )
            ]

        return [
            ft.Row([
                ft.ElevatedButton("Data Inicial", icon=ft.Icons.CALENDAR_TODAY,
                                  on_click=lambda e: self.page.open(self.start_date_picker)),
                ft.ElevatedButton("Data Final", icon=ft.Icons.CALENDAR_TODAY,
                                  on_click=lambda e: self.page.open(self.end_date_picker)),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.ResponsiveRow([
                ft.Column(
                    col={"md": 6},
                    controls=[
                        ft.Text("Status de Envios", size=18, weight=ft.FontWeight.BOLD,
                                color=self.page.theme.color_scheme.primary),
                        ft.Container(self.create_pie_chart(), padding=20, width=500, height=400)
                    ]
                ),
                ft.Column(
                    col={"md": 6},
                    controls=[
                        ft.Text("Dívidas por Mês", size=18, weight=ft.FontWeight.BOLD,
                                color=self.page.theme.color_scheme.primary),
                        ft.Container(self.create_bar_chart(), padding=20, width=500, height=400)
                    ]
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
            ft.ResponsiveRow([
                ft.Column(
                    col=12,
                    controls=[
                        ft.Text("Taxa de Sucesso ao Longo do Tempo", size=18, weight=ft.FontWeight.BOLD,
                                color=self.page.theme.color_scheme.primary),
                        ft.Container(self.create_line_chart(), padding=20, width=1000, height=400)
                    ]
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ]

    def filter_data(self):
        start_date = self.start_date_picker.value or datetime(2023, 1, 1)
        end_date = self.end_date_picker.value or datetime(2025, 12, 31)
        filtered_clients = [
            c for c in self.clients_list
            if start_date <= datetime.strptime(c.due_date, "%d/%m/%Y") <= end_date
        ]
        filtered_history = [
            h for h in self.history
            if start_date <= datetime.strptime(h.sent_at.split()[0], "%d/%m/%Y") <= end_date
        ]
        logger.info(
            f"Dados filtrados: {len(filtered_clients)} clientes, {len(filtered_history)} históricos entre {start_date} e {end_date}")
        return filtered_clients, filtered_history

    def update_charts(self, e):
        filtered_clients, filtered_history = self.filter_data()
        if not filtered_clients and not filtered_history:
            self.controls = [
                ft.Text(
                    "Nenhum dado no período selecionado",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=self.page.theme.color_scheme.primary,
                    text_align=ft.TextAlign.CENTER
                )
            ]
        else:
            self.controls = [
                ft.Row([
                    ft.ElevatedButton("Data Inicial", icon=ft.Icons.CALENDAR_TODAY,
                                      on_click=lambda e: self.page.open(self.start_date_picker)),
                    ft.ElevatedButton("Data Final", icon=ft.Icons.CALENDAR_TODAY,
                                      on_click=lambda e: self.page.open(self.end_date_picker)),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.ResponsiveRow([
                    ft.Column(
                        col={"md": 6},
                        controls=[
                            ft.Text("Status de Envios", size=18, weight=ft.FontWeight.BOLD,
                                    color=self.page.theme.color_scheme.primary),
                            ft.Container(self.create_pie_chart(filtered_history), padding=20, width=500, height=400)
                        ]
                    ),
                    ft.Column(
                        col={"md": 6},
                        controls=[
                            ft.Text("Dívidas por Mês", size=18, weight=ft.FontWeight.BOLD,
                                    color=self.page.theme.color_scheme.primary),
                            ft.Container(self.create_bar_chart(filtered_clients), padding=20, width=500, height=400)
                        ]
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                ft.ResponsiveRow([
                    ft.Column(
                        col=12,
                        controls=[
                            ft.Text("Taxa de Sucesso ao Longo do Tempo", size=18, weight=ft.FontWeight.BOLD,
                                    color=self.page.theme.color_scheme.primary),
                            ft.Container(self.create_line_chart(filtered_history), padding=20, width=1000, height=400)
                        ]
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ]
        self.page.update()

    def create_pie_chart(self, history=None):
        history = history or self.history
        current_color_scheme = self.page.theme.color_scheme
        success_count = sum(1 for h in history if h.status == "enviado")
        failure_count = len(history) - success_count

        logger.info(f"Gerando gráfico de pizza: {success_count} sucessos, {failure_count} falhas")

        return ft.PieChart(
            sections=[
                ft.PieChartSection(
                    value=success_count if success_count > 0 else 1,
                    title=f"Sucesso ({success_count})",
                    color=current_color_scheme.primary,
                    radius=150
                ),
                ft.PieChartSection(
                    value=failure_count if failure_count > 0 else 1,
                    title=f"Falha ({failure_count})",
                    color=current_color_scheme.error,
                    radius=150
                )
            ],
            center_space_radius=50,
            sections_space=5,
            expand=True
        )

    def create_bar_chart(self, clients_list=None):
        clients_list = clients_list or self.clients_list
        current_color_scheme = self.page.theme.color_scheme
        debt_by_month = {}

        for client in clients_list:
            due_date = datetime.strptime(client.due_date, "%d/%m/%Y")
            month_key = due_date.strftime("%Y-%m")
            debt_value = float(client.debt_amount.replace("R$ ", "").replace(",", "."))
            debt_by_month[month_key] = debt_by_month.get(month_key, 0) + debt_value

        logger.info(f"Gerando gráfico de barras: {debt_by_month}")

        if not debt_by_month:
            debt_by_month["Sem Dados"] = 0

        return ft.BarChart(
            bar_groups=[
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=value,
                            width=40,
                            color=current_color_scheme.primary,
                            tooltip=f"{month}: R$ {value:,.2f}".replace(".", ","),
                            border_radius=5
                        )
                    ]
                )
                for i, (month, value) in enumerate(debt_by_month.items())
            ],
            bottom_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(month, size=14))
                        for i, month in enumerate(debt_by_month.keys())],
                labels_size=50
            ),
            left_axis=ft.ChartAxis(
                labels_size=50,
                title=ft.Text("Valor (R$)", size=16)
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, current_color_scheme.surface_variant),
            max_y=max(debt_by_month.values(), default=100) * 1.2,
            expand=True
        )

    def create_line_chart(self, history=None):
        history = history or self.history
        current_color_scheme = self.page.theme.color_scheme
        success_data = []
        dates = sorted(set(h.sent_at.split()[0] for h in history))

        if not dates:
            dates = [datetime.now().strftime("%d/%m/%Y")]
            success_data = [(dates[0], 0)]
        else:
            for date in dates:
                daily_success = sum(1 for h in history if h.sent_at.startswith(date) and h.status == "enviado")
                daily_total = sum(1 for h in history if h.sent_at.startswith(date))
                success_rate = (daily_success / daily_total * 100) if daily_total > 0 else 0
                success_data.append((date, success_rate))

        logger.info(f"Gerando gráfico de linha: {success_data}")

        return ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(i, value)
                        for i, (date, value) in enumerate(success_data)
                    ],
                    color=current_color_scheme.primary,
                    stroke_width=3,
                    curved=True
                )
            ],
            bottom_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(date, size=14))
                        for i, (date, _) in enumerate(success_data)],
                labels_size=50
            ),
            left_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(f"{i}%", size=14)) for i in range(0, 101, 25)],
                labels_size=50,
                title=ft.Text("Taxa (%)", size=16)
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, current_color_scheme.surface_variant),
            expand=True
        )


def create_charts_container(clients_list, history, page: ft.Page):
    return ChartWithDateFilter(clients_list, history, page)
