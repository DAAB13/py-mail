# services/mailing.py

import os
import toml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from typing import List, Set, Optional, Dict

from data import data_loader
from mail.outlook import OutlookMail

class MailingService:
    """Cerebro del sistema: coordina datos, plantillas y envío."""

    def __init__(self, templates_dir: str = "templates"):
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self.outlook = OutlookMail()
        
        # Cargar configuración desde TOML
        config_path = Path("config/config.toml")
        if config_path.exists():
            self.config = toml.load(config_path)
            logger.info("Configuración cargada correctamente desde config.toml")
        else:
            self.config = {}
            logger.warning("No se encontró config/config.toml. Se usará configuración por defecto.")
            
        # Directorio base de adjuntos desde .env
        self.path_adjuntos = os.getenv("PATH_ADJUNTOS", "")
        if not self.path_adjuntos:
            logger.warning("La variable PATH_ADJUNTOS no está definida en el .env.")

    def _get_template_config(self, template_name: str) -> Dict:
        """Obtiene la configuración específica para una plantilla."""
        return self.config.get("templates", {}).get(template_name, {})

    def _resolve_attachments(self, filenames: List[str], env_var_name: str) -> List[str]:
        """Convierte nombres de archivos en rutas absolutas usando la variable de entorno indicada."""
        rutas = []
        base_path = os.getenv(env_var_name, "")
        
        if not base_path:
            if filenames:
                logger.warning(f"La variable de entorno {env_var_name} no está definida o está vacía.")
            return rutas
            
        for name in filenames:
            ruta_completa = Path(base_path) / name
            if ruta_completa.exists():
                rutas.append(str(ruta_completa.absolute()))
            else:
                logger.error(f"Adjunto no encontrado en {env_var_name}: {ruta_completa}")
        return rutas

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

        # Configuración de la plantilla
        conf = self._get_template_config("bienvenida_alumnos")
        
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

        # Preparar Asunto dinámico
        subject_template = conf.get("subject", "Bienvenida al curso: {curso}")
        try:
            asunto = subject_template.format(
                curso=sesion_principal.curso,
                id=id_objetivo,
                nrc=sesion_principal.nrc
            )
        except Exception as e:
            logger.warning(f"Error al formatear asunto: {e}. Usando fallback.")
            asunto = f"Bienvenido al curso {sesion_principal.curso}"

        # Preparar Adjuntos
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_ALUMNOS")
        adjuntos = self._resolve_attachments(conf.get("attachments", []), env_var_adjuntos)

        # Envío único con BCC
        bcc_string = "; ".join(destinatarios_lista)
        
        self.outlook.enviar(
            destinatario="alumnos@upn.pe",  # Etiqueta visual
            asunto=asunto,
            cuerpo_html=html_contenido,
            bcc=bcc_string,
            adjuntos=adjuntos
        )
        logger.success(f"Correo de bienvenida preparado para {len(estudiantes_curso)} alumnos con {len(adjuntos)} adjuntos.")

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
        ids_docentes_presentes = set(s.codigo_banner for s in sesiones_id)
        
        # Configuración de la plantilla
        conf = self._get_template_config("inicio_docentes")
        
        try:
            template = self.jinja_env.get_template("inicio_docentes.html")
        except Exception as e:
            logger.error(f"Plantilla no encontrada: {e}")
            return

        # Preparar Adjuntos (comunes para todos los docentes en este flujo)
        env_var_adjuntos = conf.get("attachments_path", "PATH_ADJUNTOS_DOCENTES")
        adjuntos = self._resolve_attachments(conf.get("attachments", []), env_var_adjuntos)

        for cod_docente in ids_docentes_presentes:
            # Buscar info del docente
            info_docente = next((d for d in todos_los_docentes if d.codigo_banner == cod_docente), None)
            
            # Sesiones de ESTE docente en ESTE curso
            sesiones_docente = [s for s in sesiones_id if s.codigo_banner == cod_docente]
            
            # Determinar destinatario
            email_dest = None
            if info_docente:
                email_dest = info_docente.email_upn or info_docente.email_personal
                nombre = info_docente.nombre_docente
            else:
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
            
            # Preparar Asunto dinámico
            subject_template = conf.get("subject", "Inicio de Clases: {curso}")
            try:
                asunto = subject_template.format(
                    curso=sesiones_docente[0].curso,
                    codigo_banner=cod_docente,
                    nrc=sesiones_docente[0].nrc
                )
            except Exception as e:
                logger.warning(f"Error al formatear asunto: {e}. Usando fallback.")
                asunto = f"Inicio de Curso: {sesiones_docente[0].curso}"
            
            self.outlook.enviar(
                destinatario=email_dest,
                asunto=asunto,
                cuerpo_html=html,
                adjuntos=adjuntos
            )
            logger.success(f"Correo preparado para el docente: {nombre} con {len(adjuntos)} adjuntos.")

if __name__ == "__main__":
    service = MailingService()
    # service.enviar_bienvenida_curso("226201.1001")
