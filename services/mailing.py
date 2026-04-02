# services/mailing.py

from jinja2 import Environment, FileSystemLoader
from loguru import logger
from typing import List, Set

from data import data_loader
from mail.outlook import OutlookMail

class MailingService:
    """Cerebro del sistema: coordina datos, plantillas y envío."""

    def __init__(self, templates_dir: str = "templates"):
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self.outlook = OutlookMail()

    def enviar_bienvenida_curso(self, id_objetivo: str):
        """[Flujo 1] Envía un solo correo a todos los alumnos usando CCO."""
        id_objetivo = id_objetivo.strip()
        logger.info(f"Procesando Bienvenida para el ID: {id_objetivo}")

        # Carga de datos
        todas_las_sesiones = data_loader.load_programacion()
        todos_los_estudiantes = data_loader.load_estudiantes()

        # Filtrado de sesiones de este ID (ordenadas por número de sesión)
        sesiones_id = sorted(
            [s for s in todas_las_sesiones if str(s.id).strip() == id_objetivo],
            key=lambda x: x.sesion
        )
        if not sesiones_id:
            logger.error(f"No se encontraron sesiones para el ID {id_objetivo}.")
            return

        sesion_principal = sesiones_id[0] # Para sacar el nombre del curso, nrc, etc.

        # Filtrado de todos los estudiantes
        estudiantes_curso = [e for e in todos_los_estudiantes if str(e.id).strip() == id_objetivo]
        if not estudiantes_curso:
            logger.warning(f"No se encontraron estudiantes para el ID {id_objetivo}.")
            return

        # Recolectar todos los correos disponibles (UPN + Personal) sin duplicados
        destinatarios_set: Set[str] = set()
        for est in estudiantes_curso:
            if est.email_upn: destinatarios_set.add(est.email_upn.strip())
            if est.correo_est_personal: destinatarios_set.add(est.correo_est_personal.strip())
        
        # Filtramos posibles vacíos
        destinatarios_lista = [d for d in destinatarios_set if d]
        
        if not destinatarios_lista:
            logger.error("No se encontraron correos para este curso.")
            return

        # Renderizado
        try:
            template = self.jinja_env.get_template("bienvenida_alumnos.html")
            html_contenido = template.render(
                curso=sesion_principal.curso,
                nrc=sesion_principal.nrc,
                docente=sesion_principal.docente,
                sesiones=sesiones_id # Pasamos TODA la lista de sesiones
            )
        except Exception as e:
            logger.error(f"Error renderizando plantilla: {e}")
            return

        # Envío único con BCC
        bcc_string = "; ".join(destinatarios_lista)
        asunto = f"Bienvenido al curso {sesion_principal.curso} (NRC: {sesion_principal.nrc})"
        
        # Mandamos a un destinatario vacío o a ti mismo y a todos en BCC
        self.outlook.enviar(
            destinatario="alumnos@upn.pe",  # Etiqueta visual
            asunto=asunto,
            cuerpo_html=html_contenido,
            bcc=bcc_string
        )
        logger.success(f"Correo de bienvenida preparado para {len(estudiantes_curso)} alumnos.")

    def enviar_inicio_docentes(self, id_objetivo: str):
        """[Flujo 2] Envía un correo por docente con sus sesiones específicas."""
        id_objetivo = id_objetivo.strip()
        logger.info(f"Procesando Inicio de Curso para Docentes del ID: {id_objetivo}")

        # 1. Cargar datos
        todas_las_sesiones = data_loader.load_programacion()
        todos_los_docentes = data_loader.load_docentes()

        # 2. Filtrar todas las sesiones de este curso ID
        sesiones_id = [s for s in todas_las_sesiones if str(s.id).strip() == id_objetivo]
        if not sesiones_id:
            logger.error(f"No hay sesiones para el ID {id_objetivo}.")
            return

        # 3. Identificar docentes únicos en este ID
        # Nota: El campo codigo_banner en SesionProgramada es el ID del docente
        ids_docentes_presentes = set(s.codigo_banner for s in sesiones_id)
        
        try:
            template = self.jinja_env.get_template("inicio_docentes.html")
        except Exception as e:
            logger.error(f"Plantilla no encontrada: {e}")
            return

        for cod_docente in ids_docentes_presentes:
            # Buscar info del docente
            info_docente = next((d for d in todos_los_docentes if d.codigo_banner == cod_docente), None)
            
            # Sesiones de ESTE docente en ESTE curso
            sesiones_docente = [s for s in sesiones_id if s.codigo_banner == cod_docente]
            
            # Determinar destinatario (priorizando personal + upn si quieres, o solo upn)
            # Como tu .env sugiere, buscaremos el que tenga
            email_dest = None
            if info_docente:
                email_dest = info_docente.email_upn or info_docente.email_personal
                nombre = info_docente.nombre_docente
            else:
                # Si no está en el maestro de docentes, intentamos sacar algo de la programación
                nombre = sesiones_docente[0].docente
                logger.warning(f"Docente {nombre} no encontrado en maestro de docentes.")
                continue

            if not email_dest:
                logger.warning(f"Docente {nombre} no tiene correo registrado.")
                continue

            # Renderizado individual
            html = template.render(
                nombre_docente=nombre,
                curso=sesiones_docente[0].curso,
                nrc=sesiones_docente[0].nrc,
                sesiones=sesiones_docente
            )
            
            asunto = f"Inicio de Curso: {sesiones_docente[0].curso} (NRC: {sesiones_docente[0].nrc})"
            
            self.outlook.enviar(
                destinatario=email_dest,
                asunto=asunto,
                cuerpo_html=html
            )
            logger.success(f"Correo preparado para el docente: {nombre}")

if __name__ == "__main__":
    service = MailingService()
    # service.enviar_bienvenida_curso("226201.1001")
