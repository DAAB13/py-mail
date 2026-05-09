# ui/app.py
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

import flet as ft
from loguru import logger

# Añadimos el directorio raíz al path para que encuentre los módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.mailing import MailingService
from config.logging_config import setup_logging


# ---------------------------------------------------------------------------
# Paleta de colores por flujo (Material) y niveles de log
# ---------------------------------------------------------------------------
COLOR_F1 = ft.Colors.GREEN_400
COLOR_F2 = ft.Colors.BLUE_400
COLOR_F3 = ft.Colors.AMBER_400

LOG_COLORS = {
    "success": "#4caf50",
    "warning": "#ffc107",
    "danger": "#f44336",
    "info": "#29b6f6",
    "secondary": "#adb5bd",
}


class PyMailApp:
    """Interfaz moderna basada en Flet. Solo capa de presentación."""

    def __init__(self, page: ft.Page):
        self.page = page
        setup_logging()

        self._configure_window()

        try:
            self.mailing_service = MailingService()
        except Exception as e:
            self._show_critical_error(f"No se pudo iniciar el servicio: {e}")
            return

        self._build_ui()

    # ---------------------------- Setup ----------------------------------
    def _configure_window(self):
        page = self.page
        page.title = "Py Mail"
        page.theme_mode = ft.ThemeMode.DARK
        page.window.width = 920
        page.window.height = 820
        page.window.min_width = 820
        page.window.min_height = 700
        page.padding = 24
        page.spacing = 0
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
        page.bgcolor = "#0f1115"

    def _show_critical_error(self, message: str):
        self.page.add(
            ft.Container(
                content=ft.Text(message, color=ft.Colors.RED_400, size=16),
                padding=20,
            )
        )

    # ---------------------------- UI -------------------------------------
    def _build_ui(self):
        self.page.add(
            ft.Column(
                controls=[
                    self._build_header(),
                    ft.Container(height=12),
                    self._build_flow1_card(),
                    self._build_flow2_card(),
                    self._build_flow3_card(),
                    ft.Container(height=8),
                    self._build_log_panel(),
                ],
                spacing=12,
                expand=True,
            )
        )

    def _build_header(self) -> ft.Control:
        title = ft.Column(
            controls=[
                ft.Text(
                    "Py Mail",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_300,
                ),
                ft.Text(
                    "Automatización de correos académicos UPN",
                    size=12,
                    color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                ),
            ],
            spacing=2,
        )

        # GIF de Megaman (si está disponible en assets/)
        gif = ft.Image(
            src="megaman.gif",
            width=72,
            height=72,
            fit=ft.BoxFit.CONTAIN,
            error_content=ft.Container(width=0, height=0),
        )

        return ft.Row(
            controls=[title, ft.Container(expand=True), gif],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _make_card(self, title: str, color: str, icon, body: ft.Control) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=20),
                            ft.Text(
                                title,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                        ],
                        spacing=8,
                    ),
                    body,
                ],
                spacing=14,
            ),
            padding=ft.padding.symmetric(vertical=18, horizontal=20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, color)),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.04, color),
        )

    def _action_button(self, text: str, icon, color: str, on_click) -> ft.Control:
        return ft.FilledTonalButton(
            content=ft.Text(text, weight=ft.FontWeight.W_500),
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=color,
                bgcolor=ft.Colors.with_opacity(0.12, color),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
            ),
        )

    # ----- Flujo 1 -------------------------------------------------------
    def _build_flow1_card(self) -> ft.Control:
        self.f1_id_curso = ft.TextField(
            label="ID del Curso",
            hint_text="ej. 226201.1001",
            border_color=ft.Colors.with_opacity(0.4, COLOR_F1),
            focused_border_color=COLOR_F1,
            cursor_color=COLOR_F1,
            expand=True,
            dense=True,
        )
        body = ft.Row(
            controls=[
                self.f1_id_curso,
                self._action_button(
                    "Generar Borrador",
                    ft.Icons.SCHOOL_OUTLINED,
                    COLOR_F1,
                    lambda e: self._run_flow(self._f1_bienvenida),
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return self._make_card(
            "F1: Bienvenida a Alumnos", COLOR_F1, ft.Icons.MAIL_OUTLINE, body
        )

    # ----- Flujo 2 -------------------------------------------------------
    def _build_flow2_card(self) -> ft.Control:
        self.f2_id_curso = ft.TextField(
            label="ID del Curso",
            hint_text="ej. 226201.1001",
            border_color=ft.Colors.with_opacity(0.4, COLOR_F2),
            focused_border_color=COLOR_F2,
            cursor_color=COLOR_F2,
            expand=True,
            dense=True,
        )
        body = ft.Row(
            controls=[
                self.f2_id_curso,
                self._action_button(
                    "Generar Borradores",
                    ft.Icons.GROUPS_OUTLINED,
                    COLOR_F2,
                    lambda e: self._run_flow(self._f2_inicio_docentes),
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return self._make_card(
            "F2: Inicio para Docentes", COLOR_F2, ft.Icons.PERSON_OUTLINE, body
        )

    # ----- Flujo 3 -------------------------------------------------------
    def _build_flow3_card(self) -> ft.Control:
        hoy = datetime.now()
        lunes = hoy - timedelta(days=hoy.weekday())
        domingo = lunes + timedelta(days=6)

        self.f3_semana_actual = ft.Switch(
            label="Usar semana actual",
            value=True,
            active_color=COLOR_F3,
            on_change=self._toggle_f3_dates,
        )
        self.f3_start = ft.TextField(
            label="Inicio",
            hint_text="YYYY-MM-DD",
            value=lunes.strftime("%Y-%m-%d"),
            read_only=True,
            border_color=ft.Colors.with_opacity(0.4, COLOR_F3),
            focused_border_color=COLOR_F3,
            cursor_color=COLOR_F3,
            expand=True,
            dense=True,
        )
        self.f3_end = ft.TextField(
            label="Fin",
            hint_text="YYYY-MM-DD",
            value=domingo.strftime("%Y-%m-%d"),
            read_only=True,
            border_color=ft.Colors.with_opacity(0.4, COLOR_F3),
            focused_border_color=COLOR_F3,
            cursor_color=COLOR_F3,
            expand=True,
            dense=True,
        )
        self.f3_hint = ft.Text(
            "Formato: YYYY-MM-DD  (ej. 2026-04-07 al 2026-04-13)",
            size=11,
            color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
            visible=False,
        )

        body = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.f3_semana_actual,
                        ft.Container(expand=True),
                        self._action_button(
                            "Generar Informe",
                            ft.Icons.SUMMARIZE_OUTLINED,
                            COLOR_F3,
                            lambda e: self._run_flow(self._f3_informe_semanal),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(controls=[self.f3_start, self.f3_end], spacing=12),
                self.f3_hint,
            ],
            spacing=10,
        )
        return self._make_card(
            "F3: Informe Semanal", COLOR_F3, ft.Icons.ASSESSMENT_OUTLINED, body
        )

    def _toggle_f3_dates(self, e=None):
        if self.f3_semana_actual.value:
            hoy = datetime.now()
            lunes = hoy - timedelta(days=hoy.weekday())
            domingo = lunes + timedelta(days=6)
            self.f3_start.value = lunes.strftime("%Y-%m-%d")
            self.f3_end.value = domingo.strftime("%Y-%m-%d")
            self.f3_start.read_only = True
            self.f3_end.read_only = True
            self.f3_hint.visible = False
        else:
            self.f3_start.value = ""
            self.f3_end.value = ""
            self.f3_start.read_only = False
            self.f3_end.read_only = False
            self.f3_hint.visible = True
        self.page.update()

    # ----- Panel de logs -------------------------------------------------
    def _build_log_panel(self) -> ft.Control:
        self.log_view = ft.ListView(
            spacing=2,
            padding=ft.padding.symmetric(vertical=8, horizontal=12),
            auto_scroll=True,
            expand=True,
        )

        clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip="Limpiar registro",
            icon_color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
            on_click=self._clear_logs,
        )

        header = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.HISTORY,
                            size=16,
                            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                        ),
                        ft.Text(
                            "Registro de actividad",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(expand=True),
                clear_btn,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(
                        content=self.log_view,
                        bgcolor="#161922",
                        border=ft.border.all(
                            1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
                        ),
                        border_radius=10,
                        height=240,
                    ),
                ],
                spacing=8,
            ),
        )

    def _clear_logs(self, e=None):
        self.log_view.controls.clear()
        self.page.update()

    # ---------------------------- Logging --------------------------------
    def log(self, message: str, style: str = "secondary"):
        """Añade un mensaje al panel de logs (seguro para hilos)."""
        color = LOG_COLORS.get(style, LOG_COLORS["secondary"])
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.controls.append(
            ft.Text(
                f"[{timestamp}] {message}",
                color=color,
                size=12,
                font_family="Consolas",
                selectable=True,
            )
        )
        try:
            self.page.update()
        except Exception:
            pass

    # ---------------------------- Flows ----------------------------------
    def _run_flow(self, target):
        """Ejecuta un flujo en un hilo separado para no bloquear la UI."""
        threading.Thread(target=target, daemon=True).start()

    def _f1_bienvenida(self):
        id_curso = (self.f1_id_curso.value or "").strip()
        if not id_curso:
            self.log("[F1] El ID del curso no puede estar vacío.", "danger")
            return

        try:
            self.log(
                f"[F1] Iniciando flujo de bienvenida para el curso: {id_curso}",
                "success",
            )
            self.mailing_service.enviar_bienvenida_curso(id_curso)
            self.log(
                f"[F1] Borrador generado para el curso {id_curso}. Revisa Outlook.",
                "success",
            )
        except Exception:
            logger.exception(
                f"Error en el flujo de bienvenida para el curso {id_curso}"
            )
            self.log("[F1] Error crítico. Revisa app.log para detalles.", "danger")

    def _f2_inicio_docentes(self):
        id_curso = (self.f2_id_curso.value or "").strip()
        if not id_curso:
            self.log("[F2] El ID del curso no puede estar vacío.", "danger")
            return

        try:
            self.log(
                f"[F2] Iniciando flujo de inicio para docentes del curso: {id_curso}",
                "info",
            )
            self.mailing_service.enviar_inicio_docentes(id_curso)
            self.log(
                f"[F2] Borradores generados para el curso {id_curso}. Revisa Outlook.",
                "info",
            )
        except Exception:
            logger.exception(
                f"Error en el flujo de inicio para docentes del curso {id_curso}"
            )
            self.log("[F2] Error crítico. Revisa app.log para detalles.", "danger")

    def _f3_informe_semanal(self):
        start_date, end_date = None, None
        if not self.f3_semana_actual.value:
            start_date = (self.f3_start.value or "").strip()
            end_date = (self.f3_end.value or "").strip()
            if not start_date or not end_date:
                self.log(
                    "[F3] Ingresa la fecha de inicio y fin (YYYY-MM-DD).", "danger"
                )
                return
            try:
                s = datetime.strptime(start_date, "%Y-%m-%d")
                e = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                self.log("[F3] Formato de fecha inválido. Usa YYYY-MM-DD.", "danger")
                return
            if s > e:
                self.log(
                    "[F3] La fecha de inicio debe ser anterior o igual a la fecha de fin.",
                    "danger",
                )
                return

        try:
            self.log("[F3] Iniciando flujo de informe semanal.", "warning")
            self.mailing_service.enviar_informe_semanal(start_date, end_date)
            self.log(
                "[F3] Borrador de informe semanal generado. Revisa Outlook.",
                "warning",
            )
        except Exception:
            logger.exception("Error en el flujo de informe semanal")
            self.log("[F3] Error crítico. Revisa app.log para detalles.", "danger")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Punto de entrada para la aplicación gráfica (Flet)."""
    project_root = Path(__file__).resolve().parent.parent
    assets_dir = project_root / "assets"
    ft.app(target=PyMailApp, assets_dir=str(assets_dir))


if __name__ == "__main__":
    main()
