# services/mailing.py

from services.core_mailer import CoreMailer
from services.flujos_academicos import FlujosAcademicos
from services.flujos_reportes import FlujosReportes

class MailingService:
    """
    Fachada (Facade) del sistema de mensajería.
    Mantiene la compatibilidad con main.py delegando las tareas a los sub-módulos.
    """

    def __init__(self, templates_dir: str = "templates"):
        # Inicializamos el motor base que comparte la configuración y Outlook (COM Object)
        self.core = CoreMailer(templates_dir)
        
        # Inicializamos los flujos pasándoles el motor base
        self.flujos_academicos = FlujosAcademicos(self.core)
        self.flujos_reportes = FlujosReportes(self.core)

    def enviar_bienvenida_curso(self, id_objetivo: str):
        self.flujos_academicos.enviar_bienvenida_curso(id_objetivo)

    def enviar_inicio_docentes(self, id_objetivo: str):
        self.flujos_academicos.enviar_inicio_docentes(id_objetivo)

    def enviar_informe_semanal(self, start_date: str = None, end_date: str = None):
        self.flujos_reportes.enviar_informe_semanal(start_date, end_date)

if __name__ == "__main__":
    service = MailingService()
    # service.enviar_bienvenida_curso("226201.1001")
