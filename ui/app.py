# ui/app.py
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import BooleanVar
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from PIL import Image, ImageTk

# Añadimos el directorio raíz al path para que encuentre los módulos del proyecto
# Esto es clave para que la app funcione al ejecutarla directamente
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.mailing import MailingService
from config.logging_config import setup_logging

class PyMailApp(ttk.Window):
    def __init__(self):
        # Configuración inicial de la ventana con el tema 'litera'
        super().__init__(title="Py Mail", themename="darkly")
        setup_logging()
        self.geometry("800x720")
        self.minsize(800, 680)
        self.resizable(False, True)

        # --- Animación del GIF ---
        self.gif_frames = []
        self.gif_delay = 100  # Delay por defecto
        self.load_gif()

        try:
            # Inicializamos el servicio de mailing, el corazón de la aplicación
            self.mailing_service = MailingService()
        except Exception as e:
            # Si hay un error crítico al inicio (ej: no hay .env), lo mostramos
            self.show_critical_error(f"No se pudo iniciar el servicio: {e}")
            return

        self.create_widgets()

    def show_critical_error(self, message):
        """Muestra un error fatal que impide que la app funcione."""
        error_label = ttk.Label(self, text=message, bootstyle="danger", wraplength=750)
        error_label.pack(pady=20, padx=20)

    def load_gif(self):
        """Carga los frames de la animación GIF."""
        try:
            gif_path = Path(__file__).resolve().parent.parent / "assets/megaman.gif"
            with Image.open(gif_path) as img:
                self.gif_delay = img.info.get('duration', 100)
                for i in range(img.n_frames):
                    img.seek(i)
                    # Creamos una copia para cada frame
                    frame_image = img.copy()
                    # Guardamos el PhotoImage para que no lo borre el recolector de basura
                    self.gif_frames.append(ImageTk.PhotoImage(frame_image))
        except FileNotFoundError:
            self.gif_frames = []
        except Exception:
            self.gif_frames = [] # Si hay cualquier error, no mostramos animación

    def update_gif_frame(self, frame_num):
        """Actualiza el frame del GIF que se muestra en el Label."""
        if not self.gif_frames:
            return

        frame = self.gif_frames[frame_num]
        self.gif_label.configure(image=frame)

        next_frame_num = (frame_num + 1) % len(self.gif_frames)
        self.after(self.gif_delay, self.update_gif_frame, next_frame_num)

    def create_widgets(self):
        """Crea y organiza los widgets de la interfaz."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # --- Cabecera con Título y GIF ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        header = ttk.Label(header_frame, text="Py Mail", font=("Helvetica", 18, "bold"), bootstyle=SUCCESS)
        header.pack(side=LEFT, anchor=W)

        if self.gif_frames:
            self.gif_label = ttk.Label(header_frame)
            self.gif_label.pack(side=RIGHT, anchor=E, padx=(0, 10))
            self.after(0, self.update_gif_frame, 0) # Inicia la animación

        # --- Flujos ---
        self.create_flow1_widgets(main_frame)
        self.create_flow2_widgets(main_frame)
        self.create_flow3_widgets(main_frame)

        # Separador visual
        ttk.Separator(main_frame, bootstyle=SECONDARY, orient=HORIZONTAL).pack(pady=20, fill=X)
        
        # --- Área de Logs ---
        log_header = ttk.Label(main_frame, text="Registro de Actividad", font=("Helvetica", 12, "bold"))
        log_header.pack(pady=(0, 10))
        
        self.log_area = ScrolledText(main_frame, height=10, state="disabled", autohide=True)
        self.log_area.pack(fill=BOTH, expand=YES)
        self._setup_log_tags()

    def create_flow_frame(self, parent, title):
        """Crea un marco estandarizado para cada flujo."""
        frame = ttk.Labelframe(parent, text=title, padding=15)
        frame.pack(fill=X, pady=10)
        return frame

    def create_flow1_widgets(self, parent):
        """Widgets para el Flujo 1: Bienvenida a Alumnos."""
        frame = self.create_flow_frame(parent, "F1: Bienvenida a Alumnos")

        # Grid para alinear widgets
        frame.grid_columnconfigure(1, weight=1)

        label = ttk.Label(frame, text="ID del Curso:")
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.f1_id_curso = ttk.Entry(frame, bootstyle=SUCCESS)
        self.f1_id_curso.grid(row=0, column=1, padx=5, sticky="ew")

        button = ttk.Button(frame, text="Generar Borrador", bootstyle="success-outline", command=lambda: self.run_flow(self.f1_bienvenida))
        button.grid(row=0, column=2, padx=(10, 0))

    def create_flow2_widgets(self, parent):
        """Widgets para el Flujo 2: Inicio para Docentes."""
        frame = self.create_flow_frame(parent, "F2: Inicio para Docentes")
        frame.grid_columnconfigure(1, weight=1)

        label = ttk.Label(frame, text="ID del Curso:")
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.f2_id_curso = ttk.Entry(frame, bootstyle=INFO)
        self.f2_id_curso.grid(row=0, column=1, padx=5, sticky="ew")

        button = ttk.Button(frame, text="Generar Borradores", bootstyle="info-outline", command=lambda: self.run_flow(self.f2_inicio_docentes))
        button.grid(row=0, column=2, padx=(10, 0))

    def create_flow3_widgets(self, parent):
        """Widgets para el Flujo 3: Informe Semanal."""
        frame = self.create_flow_frame(parent, "F3: Informe Semanal")
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        # Fila 0: toggle + botón
        self.f3_semana_actual = BooleanVar(value=True)
        ttk.Checkbutton(
            frame, text="Usar semana actual",
            variable=self.f3_semana_actual,
            bootstyle="warning-round-toggle",
            command=self._toggle_f3_dates,
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        ttk.Button(
            frame, text="Generar Informe", bootstyle="warning-outline",
            command=lambda: self.run_flow(self.f3_informe_semanal),
        ).grid(row=0, column=4, sticky="e", padx=(10, 0))

        # Fila 1: campos de fecha
        ttk.Label(frame, text="Inicio:").grid(row=1, column=0, padx=(0, 8), sticky="w")
        self.f3_start = ttk.Entry(frame, bootstyle="warning")
        self.f3_start.grid(row=1, column=1, padx=(0, 15), sticky="ew")

        ttk.Label(frame, text="Fin:").grid(row=1, column=2, padx=(0, 8), sticky="w")
        self.f3_end = ttk.Entry(frame, bootstyle="warning")
        self.f3_end.grid(row=1, column=3, columnspan=2, sticky="ew")

        # Fila 2: pista de formato (solo visible al editar manualmente)
        self.f3_hint = ttk.Label(
            frame,
            text="Formato: YYYY-MM-DD  (ej. 2026-04-07 al 2026-04-13)",
            bootstyle="secondary",
            font=("Helvetica", 9),
        )
        self.f3_hint.grid(row=2, column=0, columnspan=5, sticky="w", pady=(5, 0))

        self._toggle_f3_dates()

    def _toggle_f3_dates(self):
        """Habilita/deshabilita los campos de fecha según el checkbox 'Semana actual'."""
        if self.f3_semana_actual.get():
            hoy = datetime.now()
            lunes = hoy - timedelta(days=hoy.weekday())
            domingo = lunes + timedelta(days=6)
            for entry, date in [(self.f3_start, lunes), (self.f3_end, domingo)]:
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, date.strftime("%Y-%m-%d"))
                entry.configure(state="readonly")
            self.f3_hint.grid_remove()
        else:
            self.f3_start.configure(state="normal")
            self.f3_end.configure(state="normal")
            self.f3_start.delete(0, "end")
            self.f3_end.delete(0, "end")
            self.f3_hint.grid()

    def _setup_log_tags(self):
        """Configura los colores de cada nivel de log en el área de texto."""
        t = self.log_area.text
        t.tag_configure("success",   foreground="#4caf50", font=("Helvetica", 10))
        t.tag_configure("warning",   foreground="#ffc107", font=("Helvetica", 10))
        t.tag_configure("danger",    foreground="#f44336", font=("Helvetica", 10))
        t.tag_configure("info",      foreground="#29b6f6", font=("Helvetica", 10))
        t.tag_configure("secondary", foreground="#adb5bd", font=("Helvetica", 10))

    def log(self, message, style="secondary"):
        """Añade un mensaje al área de logs de forma segura para hilos."""
        self.log_area.text.configure(state="normal")
        self.log_area.text.insert(END, f"{message}\n", style)
        self.log_area.text.configure(state="disabled")
        self.log_area.text.yview(END) # Auto-scroll

    def run_flow(self, target_func):
        """Ejecuta una función de flujo en un hilo separado para no bloquear la UI."""
        thread = threading.Thread(target=target_func, daemon=True)
        thread.start()

    def f1_bienvenida(self):
        id_curso = self.f1_id_curso.get().strip()
        if not id_curso:
            self.log("❌ [F1] El ID del curso no puede estar vacío.", "danger")
            return
        
        try:
            self.log(f"🚀 [F1] Iniciando flujo de bienvenida para el curso: {id_curso}", "success")
            self.mailing_service.enviar_bienvenida_curso(id_curso)
            self.log(f"✅ [F1] Borrador generado para el curso {id_curso}. Revisa Outlook.", "success")
        except Exception:
            logger.exception(f"Error en el flujo de bienvenida para el curso {id_curso}")
            self.log(f"🔥 [F1] Error crítico. Revisa app.log para detalles.", "danger")

    def f2_inicio_docentes(self):
        id_curso = self.f2_id_curso.get().strip()
        if not id_curso:
            self.log("❌ [F2] El ID del curso no puede estar vacío.", "danger")
            return

        try:
            self.log(f"🚀 [F2] Iniciando flujo de inicio para docentes del curso: {id_curso}", "info")
            self.mailing_service.enviar_inicio_docentes(id_curso)
            self.log(f"✅ [F2] Borradores generados para el curso {id_curso}. Revisa Outlook.", "info")
        except Exception:
            logger.exception(f"Error en el flujo de inicio para docentes del curso {id_curso}")
            self.log(f"🔥 [F2] Error crítico. Revisa app.log para detalles.", "danger")

    def f3_informe_semanal(self):
        start_date, end_date = None, None
        if not self.f3_semana_actual.get():
            start_date = self.f3_start.get().strip()
            end_date = self.f3_end.get().strip()
            if not start_date or not end_date:
                self.log("❌ [F3] Ingresa la fecha de inicio y fin (YYYY-MM-DD).", "danger")
                return
            try:
                s = datetime.strptime(start_date, "%Y-%m-%d")
                e = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                self.log("❌ [F3] Formato de fecha inválido. Usa YYYY-MM-DD.", "danger")
                return
            if s > e:
                self.log("❌ [F3] La fecha de inicio debe ser anterior o igual a la fecha de fin.", "danger")
                return
        try:
            self.log("🚀 [F3] Iniciando flujo de informe semanal.", "warning")
            self.mailing_service.enviar_informe_semanal(start_date, end_date)
            self.log("✅ [F3] Borrador de informe semanal generado. Revisa Outlook.", "warning")
        except Exception:
            self.log("🔥 [F3] Error crítico. Revisa app.log para detalles.", "danger")

def main():
    """Punto de entrada para la aplicación gráfica."""
    app = PyMailApp()
    app.mainloop()

if __name__ == "__main__":
    main()
