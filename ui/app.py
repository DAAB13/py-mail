# ui/app.py
import sys
import threading
from pathlib import Path
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
        self.geometry("800x600")
        self.resizable(False, False)

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

        label = ttk.Label(frame, text="Genera el informe con la data actual.")
        label.pack(side=LEFT, fill=X, expand=YES, padx=(0,15))

        button = ttk.Button(frame, text="Generar Informe", bootstyle="warning-outline", command=lambda: self.run_flow(self.f3_informe_semanal))
        button.pack(side=RIGHT)

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
        try:
            self.log("🚀 [F3] Iniciando flujo de informe semanal.", "warning")
            self.mailing_service.enviar_informe_semanal()
            self.log("✅ [F3] Borrador de informe semanal generado. Revisa Outlook.", "warning")
        except Exception:
            logger.exception("Error en el flujo de informe semanal")
            self.log(f"🔥 [F3] Error crítico. Revisa app.log para detalles.", "danger")

def main():
    """Punto de entrada para la aplicación gráfica."""
    app = PyMailApp()
    app.mainloop()

if __name__ == "__main__":
    main()
